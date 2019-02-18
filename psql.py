#!/usr/bin/env python3
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import sys
import db
import syntax
import sqleditor

from db_settings_logic import DBSettingsDialog
from config import PatriciaConfig

DEFAULT_ROW_HEIGHT = 30
Ui_MainWindow, _ = uic.loadUiType("patriciasql_main.ui")


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.highlight = syntax.PgSQLHighlighter(self.sqlEditorArea.document())
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())
        self.show()
        # wire up signals & slots
        self.actionQuit.triggered.connect(MainWindow.exitApplication)
        self.actionExecute.triggered.connect(self.executeQuery)
        self.actionExecute_selected.triggered.connect(self.executeQuerySelected)
        self.actionSettings.triggered.connect(self.showSettings)
        self.actionExplain.triggered.connect(self.explainQuery)
        self.actionExplain_Selected.triggered.connect(self.explainSelectedQuery)
        # read config
        self.psqlConfig = PatriciaConfig()
        self.psqlConfig.read()
        # try to connect (most recent connection)
        self.pgsql = db.PostgreSQL()
        self.updateDBConnection(self.psqlConfig)
        self.vertical_resize = False
        # setup sql editor
        completer = sqleditor.SQLKeywordsCompleter()
        completer.read_keywords("sqlkeywords.txt")
        self.sqlEditorArea.setCompleter(completer)

    @staticmethod
    def exitApplication(self):
        sys.exit(0)

    def updateDBConnection(self, conp):
        self.pgsql.reconnect(conp)
        self.lbldb.setText("connected to: " + self.pgsql.getCurrentDBName())

    def showSettings(self):
        retval, newConfig = DBSettingsDialog.getConnectionProperties(self.pgsql, self.psqlConfig)
        if retval == 1:
            self.psqlConfig = newConfig
            self.updateDBConnection(newConfig)

    def explainQuery(self):
        query_text = self.sqlEditorArea.toPlainText()
        self.__executeAndExplain__(query_text)

    def explainSelectedQuery(self):
        query_text = self.__extractSelection__()
        self.__executeAndExplain__(query_text)

    def executeQuery(self):
        query_text = self.sqlEditorArea.toPlainText()
        self.__executeQuery__(query_text)

    def executeQuerySelected(self):
        query_text = self.__extractSelection__()
        self.__executeQuery__(query_text)

    def __executeQuery__(self, query_text):
        if self.pgsql is not None and self.pgsql.isConnectionOpen():
            model, execution_time = self.pgsql.getModel(query_text)
            row_count = model.rowCount()
            sql_error = (row_count == 0) and (model.lastError().isValid())
            if sql_error:
                model = self.extract_last_error(model)
            self.tableView.setModel(model)
            # resize could cost a lot of time for big results...
            if sql_error or row_count < 1000:
                self.tableView.resizeColumnsToContents()
            # TODO: this ugly hack probably means I should subclass it...
            self.restore_first_row_height()
            if sql_error:
                self.tableView.resizeRowToContents(0)
                self.vertical_resize = True
            self.lblstatus.setText("rows: %d" % row_count)
            self.lblExecutionTime.setText("execution time: %.8fs" % execution_time)
        else:
            self.__show_error_box__("Error executing query!", "Not connected to PostgreSQL!")

    def extract_last_error(self, model):
        last_error = model.lastError().text()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Error executing query:"])
        item = QStandardItem(last_error)
        model.appendRow(item)
        return model

    def restore_first_row_height(self):
        if self.vertical_resize:
            self.tableView.setRowHeight(0, DEFAULT_ROW_HEIGHT)  # default row height is 30
            self.tableView.resizeColumnToContents(0)
            self.vertical_resize = False

    def __show_error_box__(self, title, message):
        msg = QMessageBox()
        msg.setText(title)
        msg.setWindowTitle(message)
        msg.setIcon(QMessageBox.Critical)
        msg.exec_()
        self.lblstatus.setText("rows: 0")

    def __extractSelection__(self):
        start = self.sqlEditorArea.textCursor().selectionStart()
        end = self.sqlEditorArea.textCursor().selectionEnd()
        whole_text = self.sqlEditorArea.toPlainText()
        query_text = whole_text[start:end]
        return query_text

    def __executeAndExplain__(self, query_text):
        new_query_text = "explain %s" % query_text
        self.__executeQuery__(new_query_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("PatriciaSQL")
    window = MainWindow()
    app.exec_()
