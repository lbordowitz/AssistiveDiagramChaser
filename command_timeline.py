from ui_command_timeline import Ui_CommandTimeline
from PyQt5.QtWidgets import QDockWidget, QUndoView

class CommandTimeline(QDockWidget, Ui_CommandTimeline):
    def __init__(self):
        super().__init__()
        super().__init__()
        self.setupUi(self)
        
    def addUndoView(self, stack):
        view = QUndoView(stack)
        self.stackedWidget.addWidget(view)
        return view
    
    def setCurrentUndoView(self, view):
        self.stackedWidget.setCurrentWidget(view)
        
    def removeUndoView(self, view):
        self.stackedWidget.removeWidget(view)
        
    