from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class CodeWidget(QsciScintilla):
    def __init__(self, text=None, new=True):
        super().__init__()
        if text:
            self.setText(text)
        lexer = QsciLexerPython(self)
        lexer.setPaper(QColor(Qt.yellow))
        self.setLexer(lexer)
        self.setUtf8(True)  # Set encoding to UTF-8
        self.setWrapMode(self.WrapNone)
        # Turn off scroll bar:
        self.setScrollWidth(1)
        self.setScrollWidthTracking(False)
        self.setCaretForegroundColor(QColor(Qt.blue))
        self.setStyleSheet("border:none")  # Remove blue border
        self.setMarginType(1, self.NumberMargin) 
        self.setAutoCompletionSource(self.AcsAll)  
        self.setAutoIndent(True)
        self.setMouseTracking(True)
        self.setPaper(QColor(Qt.yellow))
        
    def makeTransparent(self):
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_PaintOnScreen)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
    def mouseDoubleClickEvent(self, event):
        self.setFocus()
        super().mouseDoubleClickEvent(event)
        
    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)
        
        
        
        