from PyQt5.QtWidgets import QGraphicsObject, QUndoStack, QApplication
from qt_tools import simpleMaxContrastingColor
from PyQt5.QtGui import QPainterPath, QColor
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from geom_tools import paintSelectionShape, rectToPoly
from qt_tools import Pen, SimpleBrush, unpickleGfxItemFlags
from copy import deepcopy
from uuid import uuid4

class GfxObject(QGraphicsObject):
    focusedIn = pyqtSignal()
    focusedOut = pyqtSignal()
    zoomedIn = pyqtSignal()
    positionChanged = pyqtSignal(QPointF)
    positionChangedDelta = pyqtSignal(QPointF)
    deleted = pyqtSignal(QGraphicsObject)
    undeleted = pyqtSignal(QGraphicsObject)
    DefaultZoomThreshold = 3
    
    def __init__(self, new=True):
        super().__init__()
        self._snapToGrid = True
        if new:
            self._editable = True
            self._editPen = Pen(QColor(Qt.green), 1.0)
            self._penSave = None 
            self._pen = Pen(Qt.NoPen)
            self._brush = SimpleBrush(Qt.NoBrush)
            self._locked = False
            self._constraints = []
        self._zoomThreshold = self.DefaultZoomThreshold
        self._zoom = 0
        self._commands = []
        self._uid = str(uuid4())
                
    def setEditable(self, editable):
        if self._editable != editable:
            self._editable = editable
            self.update()
            
    def setEditPen(self, pen):
        self._editPen = pen
        self.update()
            
    def editable(self):
        return self._editable
        
    def uid(self):
        return self._uid
    
    def setUid(self, uid):
        self._uid = uid
        
    def __setstate__(self, data):
        self.__init__(new=False)
        self.setParentItem(data['parent'])
        self._pen = data['pen']
        self._brush = data['brush']
        self.setFlags(unpickleGfxItemFlags(data['flags']))
        self.setPos(data['pos'])
        self._locked = data['locked']
        
    def __getstate__(self):
        return {
            'parent' : self.parentItem(),
            'pen' : self._pen,
            'brush' : self._brush,
            'flags' : int(self.flags()),
            'pos' : self.pos(),
            'locked' : self._locked
        }
        
    def __deepcopy__(self, memo):
        copy = type(self)(new=False)
        memo[id(self)] = copy
        copy.setParentItem(self.parentItem())
        copy._pen = deepcopy(self._pen, memo)
        copy._brush = deepcopy(self._brush, memo)
        copy._undoStack = None          # Can't copy an undo stack since it holds references to this item and will change /it/
        copy.setPos(QPointF(self.pos()))
        copy.setFlags(self.flags())
        copy._locked = self._locked
        copy._editable = self._editable
        copy._constraints = deepcopy(self._constraints, memo)
        copy._editPen = deepcopy(self._editPen, memo)
        copy._penSave = deepcopy(self._penSave, memo)   
        return copy
    
    def locked(self):
        return self._locked
    
    def setLocked(self, locked):
        self._locked = locked
        
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
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        #if self._totalDelta != QPointF():
            #if self._undoStack:
                #self._undoStack.push(SetterUndoCommand(self, 'setPos', event.pos() - self._totalDelta, event.pos()))
        super().mouseReleaseEvent(event)
        
    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            self._lastPos = self.pos()
            if self.snapToGrid() and self.scene() and self.scene().gridEnabled():
                if QApplication.mouseButtons() == Qt.LeftButton and self.scene():
                    grid_sizex = self.scene().gridSizeX()
                    grid_sizey = self.scene().gridSizeY()
                    o = self.scene().gridOrigin()
                    ox = o.x() % grid_sizex
                    oy = o.y() % grid_sizey
                    
                    x = round(value.x() / grid_sizex) * grid_sizex
                    y = round(value.y() / grid_sizey) * grid_sizey
                    value = QPointF(x + ox, y + oy)
            return value
        elif change == self.ItemPositionHasChanged:
            delta = value - self._lastPos
            self.positionChanged.emit(value)
            self.positionChangedDelta.emit(delta)
            return value
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
        prevstate = self.__getstate__()
        self._snapToGrid = enabled
        self.changed.emit(prevstate)
        
    def buildDefaultContextMenu(self, menu):
        raise NotImplementedError
    
    def clearZoom(self):
        self._zoom = 0
        
    def zoom(self, amount):
        self._zoom += amount
        if self._zoom >= self._zoomThreshold:
            self.zoomedIn.emit()
            
    def isZoomedIn(self):
        if self._zoom >= self._zoomThreshold:
            return True
        return False
            
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
    
    def associateCommand(self, cmd):
        self._commands.append(cmd)
        
    def clearCommands(self):
        self._commands.clear()
        
    def commandsAssociated(self):
        return self._commands
    
    def disassociateCommand(self, cmd):
        self._commands.remove(cmd)
        
    def mostRecentCommandOfType(self, type):
        if self._commands:
            k = len(self._commands) - 1
            while k >= 0:
                cmd = self._commands[k]
                if isinstance(cmd, type):
                    return cmd
                k -= 1
        return None
    
    def delete(self, deleted=None, emit=True):
        if deleted is None:
            deleted = {}
        deleted["parent"] = self.parentItem()
        deleted["children"] = []
        self.setParentItem(None)
        deleted["scene"] = self.scene()
        if self.scene():
            self.scene().removeItem(self)
        for child in self.childItems():
            d = child.delete()
            t = (child, d)
            deleted["children"].append(t)
        if emit:
            self.deleted.emit(self)
        return deleted
        
    def undelete(self, deleted, emit=True):
        scene = deleted["scene"]
        if scene:
            scene.addItem(self)
        self.setParentItem(deleted["parent"])
        for t in deleted["children"]:
            d = t[1];  child = t[0]
            child.undelete(d)
        if emit:
            self.undeleted.emit(self)
            
    def uidPairHash(self, x, y):
        return x.uid() + "," + y.uid()
    
    def constraints(self):
        return self._constraints
    
    def isConstrained(self):
        return self._constraints != []
    
    def painterPen(self):
        if self._editable:
            return self._editPen
        else:
            return self.pen()    