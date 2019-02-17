from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter


class PgSQLHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        raw_data = open('colors.txt', 'rb').read()
        highlight_data = eval(raw_data)
        rules = PgSQLHighlighter.create_highlight_rules(highlight_data)

        self.rules = [(QRegExp(pattern), color)
                      for (pattern, color) in rules]

    # this method process the data from configuration file
    # and creates array consisting of a tuple:
    # 1. regex used to search for particular highlight pattern
    # 2. text format - (QColor)
    @staticmethod
    def create_highlight_rules(highlight_definitions):
        rules = []
        for group in highlight_definitions:
            # color
            text_color = group.get('color')
            color = QColor.fromRgb(int(text_color, 16))
            text_formatting = QTextCharFormat()
            text_formatting.setForeground(color)
            # group name
            group_name = group.get('name')
            # TODO: these two conditionals should be replaced
            #       by the code that checks if 'words' array is not empty
            if group_name == 'keywords':
                ks = "(\b" + str.join(r"\b)|(\b", group['words']) + "\b)"
                rules += [(r'%s' % ks, text_formatting)]
                continue
            if group_name == 'operators':
                os = str.join(r"|", group['words'])
                rules += [(r'%s' % os, text_formatting)]
                continue
            rules += [(group['regex'], text_formatting)]
        return rules


    def highlightBlock(self, text):
        text = text.lower()
        for regx, style in self.rules:
            match = regx.indexIn(text, 0)
            while match > -1:
                index = regx.pos(0)
                length = len(regx.cap(0))
                self.setFormat(index, length, style)
                # check if there are any other tokens to be highlighted
                match = regx.indexIn(text, length + index)
            continue
        self.setCurrentBlockState(0)
