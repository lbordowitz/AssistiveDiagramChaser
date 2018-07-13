from ui_main_window import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QGraphicsTextItem
from PyQt5.QtGui import QColor
from graph_editor import GraphEditor
from graph_node import GraphNode
from graph_scene import GraphScene
from category_diagram_editor import CategoryDiagramEditor
from PyQt5.QtCore import QPointF, Qt

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, new=True):
        super().__init__()
        super().__init__()
        self.setupUi(self)        
        
        if new: 
            self._editors = {}
            self.addEditor("main")
        
        self.actionDelete.triggered.connect(lambda b: self.deleteSelectedItems())
        
    def addEditor(self, name):
        editor = CategoryDiagramEditor()
        self.tabWidget.addTab(editor, name)
        self._editors[name] = editor
        editor.setScene(GraphScene())
        
    def currentEditor(self):
        return self.tabWidget.currentWidget()
    
    def deleteSelectedItems(self):
        editor = self.currentEditor()
        if editor:
            editor.deleteItems()
    
