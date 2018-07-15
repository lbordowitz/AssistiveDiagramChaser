from gfx_object import GfxObject
from PyQt5.QtCore import QPointF, Qt, QRectF, pyqtSignal
from qt_tools import Pen, SimpleBrush
from geom_tools import mag2D, paintSelectionShape
from copy import deepcopy

class ControlPoint(GfxObject):
    DefaultRadius = 4
    positionHasChanged = pyqtSignal(QPointF)
    positionAboutToChange = pyqtSignal(QPointF)
    mouseDragBegan = pyqtSignal(QPointF)
    mouseDragEnded = pyqtSignal(QPointF)
    
    def __init__(self, new=True):
        super().__init__(new)
        if new:
            r = self.DefaultRadius
            self._rect = QRectF(-r, -r, 2*r, 2*r)            
            self._radius = self.DefaultRadius
            self.setBrush(SimpleBrush(Qt.yellow))
            self.setPen(Pen(Qt.NoPen))
            self._snapToGrid = False
        self.setFlags(self.ItemIsMovable | self.ItemIsFocusable | self.ItemSendsGeometryChanges | \
                      self.ItemSendsScenePositionChanges | self.ItemIsSelectable)
        self._dragging = False
        
    def __setstate__(self, data):
        super().__setstate__(data)
        self._radius = data["radius"]
        self._rect = data["rect"]
        self._snapToGrid = data["snap to grid"]
        self.update()
        
    def __getstate__(self):
        data = super().__getstate__()
        data["radius"] = self._radius
        data["rect"] = self._rect
        data["snap to grid"] = self._snapToGrid
        return data
        
    def __deepcopy__(self, memo):
        memo[id(self)] = self
        copy = deepcopy(super(), memo)
        copy._radius = self._radius
        copy._rect = QRectF(self._rect)
        copy._snapToGrid = self._snapToGrid
        return copy
        
    def boundingRect(self):
        return self._rect
    
    def paint(self, painter, option, widget):
        if self.scene():
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
    
