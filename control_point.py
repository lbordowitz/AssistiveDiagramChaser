from gfx_object import GfxObject
from PyQt5.QtCore import QPointF, Qt, QRectF, pyqtSignal
from qt_tools import Pen, SimpleBrush
from geom_tools import mag2D, paintSelectionShape

class ControlPoint(GfxObject):
    DefaultRadius = 7
    positionHasChanged = pyqtSignal(QPointF)
    positionAboutToChange = pyqtSignal(QPointF)
    mouseDragBegan = pyqtSignal(QPointF)
    mouseDragEnded = pyqtSignal(QPointF)
    
    def __init__(self):
        super().__init__()
        self._radius = self.DefaultRadius
        self.setFlags(self.ItemIsMovable | self.ItemIsFocusable | self.ItemSendsGeometryChanges | \
                      self.ItemSendsScenePositionChanges | self.ItemIsSelectable)
        self.setBrush(SimpleBrush(Qt.yellow))
        self.setPen(Pen(Qt.NoPen))
        r = self.DefaultRadius
        self._rect = QRectF(-r, -r, 2*r, 2*r)
        self._dragging = False
        self._snapToGrid = False
        
    def boundingRect(self):
        return self._rect
    
    def paint(self, painter, option, widget):
        if self.isSelected():
            paintSelectionShape(painter, self)
        painter.setRenderHints(painter.Antialiasing | painter.HighQualityAntialiasing)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.boundingRect())
        
    def itemChange(self, change, value):
        if change == self.ItemPositionHasChanged:
            self.positionHasChanged.emit(self.pos())
        elif change == self.ItemPositionChange:
            self.positionAboutToChange.emit(self.pos())
        return super().itemChange(change, value)

    def closestBoundaryPos(self, pos):
        rect = self.boundingRect()
        radius = rect.width() / 2        
        v = pos - rect.center()
        mag = mag2D(v)
        if abs(mag) == 0:
            return rect.topLeft()
        return v / mag * radius    
    
