from graph_node import GraphNode
from text_item import TextItem
from PyQt5.QtWidgets import QGraphicsProxyWidget
from PyQt5.QtGui import QMoveEvent, QColor
from PyQt5.QtCore import QEvent, Qt, QRectF
from qt_tools import SimpleBrush
from geom_tools import minBoundingRect
from copy import deepcopy

class CategoryObject(GraphNode):
    def __init__(self, new=True):
        super().__init__()
        if new:
            label = TextItem("x")
            self.addLabel(label)
            self.centerChild(label)
            self.setBrush(SimpleBrush(QColor(255,255,255,0)))   # Transparent
            self._insetPadding = self.DefaultInsetPadding / 3
        self._graphAlgoVisited = False
        self._editor = None
    
    def setEditor(self, editor):
        self._editor = editor
    
    def editor(self):
        return self._editor
        
    def graphAlgoVisited(self):
        return self._graphAlgoVisited
    
    def clearGraphAlgoVisitedFlag(self):
        self._graphAlgoVisited = False
        for arr in self._arrows:
            arr.clearGraphAlgoVisitedFlag()
        
    def setGraphAlgoVisitedFlag(self):
        self._graphAlgoVisited = True
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._editor = self.editor()
        self.copyLabelsTo(copy) 
        return copy
        