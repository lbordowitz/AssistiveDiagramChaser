from ui_main_window import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QGraphicsTextItem
from PyQt5.QtGui import QColor
from graph_editor import GraphEditor
from graph_node import GraphNode
from graph_scene import GraphScene
from category_diagram_editor import CategoryDiagramEditor
from PyQt5.QtCore import QPointF, Qt
from command_timeline import CommandTimeline

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app, new=True):
        super().__init__()
        super().__init__()
        self.setupUi(self)       
        self.commandTimeline = CommandTimeline()
        self.addDockWidget(Qt.RightDockWidgetArea, self.commandTimeline)
        self.tabWidget.currentChanged.connect(self.currentTabIndexChanged)
        if new: 
            self._editors = {}
            self.addEditor("main")
        self.actionDelete.triggered.connect(lambda b: self.deleteSelectedItems())
        self.actionUndo.triggered.connect(lambda b: self.undoRecentChanges())
        self.actionRedo.triggered.connect(lambda b: self.redoRecentChanges())
        self._app = app
        
    def app(self):
        return self._app
        
    def addEditor(self, name):
        editor = CategoryDiagramEditor(window=self)
        self.tabWidget.addTab(editor, name)
        self._editors[name] = editor
        editor.setScene(GraphScene())
        editor.setUndoView(self.commandTimeline.addUndoView(editor.undoStack()))
        
    def currentEditor(self):
        return self.tabWidget.currentWidget()
    
    def deleteSelectedItems(self):
        editor = self.currentEditor()
        if editor:
            editor.deleteItems()
    
    def undoRecentChanges(self):
        editor = self.currentEditor()
        if editor:
            editor.undo()
        
    def redoRecentChanges(self):
        editor = self.currentEditor()
        if editor:
            editor.redo()
    
    def currentTabIndexChanged(self, index):
        editor = self.tabWidget.widget(index)
        self.commandTimeline.setCurrentUndoView(editor.undoView())