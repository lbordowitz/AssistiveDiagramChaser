from graph_node import GraphNode
from text_item import TextItem
from code_widget import CodeWidget
from PyQt5.QtWidgets import QGraphicsProxyWidget
from PyQt5.QtGui import QMoveEvent, QColor, QPen
from PyQt5.QtCore import QEvent, Qt, QRectF
from qt_tools import SimpleBrush

class CategoryObject(GraphNode):
    def __init__(self):
        super().__init__()
        label = TextItem("A")
        self.addLabel(label)
        self.centerChild(label)
        label.setFlag(GraphNode.ItemIsMovable, False)
        self.setBrush(SimpleBrush(QColor(255,255,255,0)))   # Transparent
    
    def eventFilter(self, watched, event):
        if watched in [self._entryCode, self._exitCode]:
            if event.type() == QEvent.Move:
                if self.scene():
                    self.updateArrows()
                    self.scene().update()
            elif event.type() == QEvent.MouseButtonDblClick:
                print("here")
        return False
    
    
    #def paint(self, painter, option, widget):
        #super().paint(painter, option, widget)
        
        #painter.setPen(QPen(QColor(Qt.red), 20))
        #pos = self.mapFromScene(self.pos())
        #w = 30
        #painter.drawRect(QRectF(pos.x() - w, pos.y() - w, 2*w, 2*w))