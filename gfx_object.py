from PyQt5.QtWidgets import QGraphicsObject, QUndoStack, QApplication
from qt_tools import simpleMaxContrastingColor
from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from geom_tools import paintSelectionShape, rectToPoly
from qt_tools import Pen, SimpleBrush, unpickleGfxItemFlags
from copy import deepcopy

class GfxObject(QGraphicsObject):
    focusedIn = pyqtSignal()
    focusedOut = pyqtSignal()
    zoomedIn = pyqtSignal()
    
    DefaultZoomThreshold = 6
    
    def __init__(self):
        super().__init__()
        self._pen = Pen(Qt.NoPen)
        self._brush = SimpleBrush(Qt.NoBrush)
        self._undoStack = None
        self._totalDelta = None
        self._locked = False
        self._snapToGrid = True
        self._zoomThreshold = self.DefaultZoomThreshold
        self._zoom = 0
        
    def __setstate__(self, data):
        self.setParentItem(data['parent'])
        self._pen = data['pen']
        self._brush = data['brush']
        self._undoStack = data['undo stack']
        self.setFlags(unpickleGfxItemFlags(data['flags']))
        self.setPos(data['pos'])
        self._locked = data['locked']
        
    def __getstate__(self):
        return {
            'parent' : self.parentItem(),
            'pen' : self._pen,
            'brush' : self._brush,
            'undo stack' : self._undoStack,
            'flags' : int(self.flags()),
            'pos' : self.pos(),
            'locked' : self._locked
        }
        
    def _deepcopy(self, copy, memo):
        memo[id(self)] = self
        copy.setParentItem(deepcopy(self.parentItem(), memo))
        copy._pen = deepcopy(self._pen, memo)
        copy._brush = deepcopy(self._brush, memo)
        copy._undoStack = None          # Can't copy an undo stack since it holds references to this item and will change /it/
        copy.setPos(QPointF(self.pos()))
        copy.setFlags(self.flags())
        copy._locked = self._locked
    
    def locked(self):
        return self._locked
    
    def setLocked(self, locked):
        self._locked = locked

    def setUndoStack(self, stack):
        self._undoStack = stack
        
    def setPen(self, pen):
        self._pen = pen
        self.update()
    
    def pen(self):
        return self._pen
    
    def setBrush(self, brush):
        self._brush = brush
        self.update()
    
    def brush(self):
        return self._brush
        
    def paint(self, painter, option, widget):
        if self.isSelected():
            paintSelectionShape(painter, item=self)
    
    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    def mouseMoveEvent(self, event):
        if not self._locked:
            super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        self._totalDelta = QPointF()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        #if self._totalDelta != QPointF():
            #if self._undoStack:
                #self._undoStack.push(SetterUndoCommand(self, 'setPos', event.pos() - self._totalDelta, event.pos()))
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if self.snapToGrid() and change == self.ItemPositionChange and self.scene() and self.scene().gridEnabled():
                if QApplication.mouseButtons() == Qt.LeftButton and self.scene():
                    grid_sizex = self.scene().gridSizeX()
                    grid_sizey = self.scene().gridSizeY()
                    o = self.scene().gridOrigin()
                    ox = o.x() % grid_sizex
                    oy = o.y() % grid_sizey
                    
                    x = round(value.x() / grid_sizex) * grid_sizex
                    y = round(value.y() / grid_sizey) * grid_sizey
                    return QPointF(x + ox, y + oy)
                else:
                    return value
        #elif change == self.ItemSelectedChange:
            #if hasattr(self.scene(), 'rightMousePressed') and self.scene().rightMousePressed():
                #return self.isSelected()
            #return value
        else:
            return super().itemChange(change, value)
    
    def focusInEvent(self, event):
        self.focusedIn.emit()
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        self.focusedOut.emit()
        super().focusOutEvent(event)
        
    def snapToGrid(self):
        return self._snapToGrid
    
    def setSnapToGrid(self, enabled):
        self._snapToGrid = enabled
        
    def buildDefaultContextMenu(self, menu):
        raise NotImplementedError
    
    def clearZoom(self):
        self._zoom = 0
        
    def zoom(self, amount):
        self._zoom += amount
        if self._zoom >= self._zoomThreshold:
            self.zoomedIn.emit()
            
    def closestBoundaryPosToItem(self, item):
        if self.collidesWithItem(item):
            return self.boundingRect().center()

        point_sum = QPointF()
        points = list(rectToPoly(item.boundingRect()))

        for point in points:
            point_sum += self.closestBoundaryPos(self.mapFromItem(item, point))

        point_sum /= 4
        self_point = point_sum

        point_sum = QPointF()
        points = list(rectToPoly(self.boundingRect()))
        point_sum = QPointF()

        for point in points:
            point_sum += item.closestBoundaryPos(item.mapFromItem(self, point))

        point_sum /= 4
        obj_point = point_sum

        point = item.closestBoundaryPos(item.mapFromItem(self, self_point))

        obj_point += point
        obj_point /= 2

        return self.closestBoundaryPos(self.mapFromItem(item, obj_point))    
    
    def closestBoundaryPos(self, pos):
        raise NotImplementedError