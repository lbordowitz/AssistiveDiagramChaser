from ui_code_editor import Ui_CodeEditor
from PyQt5.QtWidgets import QDockWidget
from PyQt5.Qsci import QsciScintilla

class CodeEditor(QDockWidget, Ui_CodeEditor):
    def __init__(self):
        super().__init__()
        super().__init__()
        self.setupUi(self)
        
    def setCurrent(self, editor):
        if isinstance(editor, int):
            self.stackedWidget.setCurrentIndex(editor)
        else:
            self.stackedWidget.setCurrentWidget(editor)
        
    def add(self, editor):
        return self.stackedWidget.addWidget(editor)