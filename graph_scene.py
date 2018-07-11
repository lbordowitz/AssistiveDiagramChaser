from PyQt5.QtWidgets import QGraphicsScene, QGraphicsObject
from PyQt5.QtGui import QColor, QBrush, QTransform, QPainter, QPen
from PyQt5.QtCore import pyqtSignal, QPointF, QLineF
from graph_arrow import GraphArrow
from control_point import ControlPoint
from qt_tools import simpleMaxContrastingColor

class GraphScene(QGraphicsScene):
    backgroundDoubleClicked = pyqtSignal(QPointF)
    mousePressed = pyqtSignal(QPointF)
    dragStarted = pyqtSignal(list, QPointF)
    dragEnded = pyqtSignal(list, QPointF)
    backgroundColorChanged = pyqtSignal(QColor)
    itemsPlaced = pyqtSignal(list)
    
    def __init__(self, new=True):
        super().__init__()
        self._placeItems = None
        self._moveItems = None
        self._contextMenu = None
        if new:
            self.setBackgroundBrush(QBrush(QColor(150,150,150)))
            self._gridSizeX = 20
            self._gridSizeY = 20
            self._gridEnabled = False
            self._gridOrigin = QPointF()
            self._pickGridOrigin = False      
            self._editor = None
        self._placing = False
            
    def setEditor(self, editor):
        self._editor = editor
    
    def editor(self):
        return self._editor

    def setContextMenu(self, menu):
        self._contextMenu = menu
        
    def contextMenu(self):
        return self._contextMenu
        
    def __setstate__(self, data):
        self.__init__(new=False)
        self.setBackgroundBrush(QBrush(data['background color']))
        
    def __getstate__(self):
        return {
            'background color' : self.backgroundBrush().color(),
        }
    
    def mouseDoubleClickEvent(self, event):
        self.backgroundDoubleClicked.emit(event.scenePos())
        super().mouseDoubleClickEvent(event)
        
    def placeItems(self, items, pos=None, add=False):
        if not isinstance(items, list):
            items = [items]
        if pos is not None:
            for item in items:
                item.setPos(pos)
        if add:
            for item in items:
                self.addItem(item)                
        self._placeItems = items
        self._placing = True
        
    def mousePressEvent(self, event):
        if not self._placeItems:
            if not self._moveItems:
                item = self.itemAt(event.scenePos(), QTransform())
                if item:
                    if isinstance(item, ControlPoint):
                    #if item.isSelected():
                        #self._placeItems = self.selectedItems()
                    #else:
                        self._placeItems = [item]
                        pos = event.scenePos()
                        self.dragStarted.emit(self._placeItems, pos)
                        for item in self._placeItems:
                            if hasattr(item, 'mouseDragBegan'):
                                item.mouseDragBegan.emit(pos)
            else:
                pos = event.scenePos()
                self.dragEnded.emit(self._moveItems, pos)
                for item in self._moveItems:
                    if hasattr(item, 'mouseDragEnded'):
                        item.mouseDragEnded.emit(pos)
                self._moveItems = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._moveItems:
            pos = event.scenePos()
            self.dragEnded.emit(self._moveItems, pos)
            for item in self._moveItems:
                if hasattr(item, 'mouseDragEnded'):
                    item.mouseDragEnded.emit(pos)       
            if self._placing:
                self.itemsPlaced.emit(self._moveItems)
                self._placing = False
            self._moveItems = None                  
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        if self._placeItems:
            self._moveItems = self._placeItems
            self._placeItems = None
        if self._moveItems:
            delta = event.scenePos() - event.lastScenePos()
            for item in self._moveItems:
                item.setPos(item.pos() + delta)
        super().mouseMoveEvent(event)
        
    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if self._contextMenu and item is None:
            self._contextMenu.exec_(event.screenPos())
        else:
            super().contextMenuEvent(event)
            
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        if self._gridEnabled:
            painter.setRenderHints(QPainter.Antialiasing)
            painter.setPen(QPen(simpleMaxContrastingColor(self.backgroundBrush().color()), 0.3))
            points = []                 # Adding to a list and then drawing is much faster
            
            o = self._gridOrigin
            ox = o.x() % self._gridSizeX
            oy = o.y() % self._gridSizeY
            left = int(rect.left()) - (int(rect.left()) % self._gridSizeX)
            top = int(rect.top()) - (int(rect.top()) % self._gridSizeY)
            
            for x in range(left, int(rect.right()), self._gridSizeX):
                for y in range(top, int(rect.bottom()), self._gridSizeY):
                    points.append(QPointF(x + ox, y + oy))
        
            painter.drawPoints(*points)
            # Draw grid origin
            painter.drawLine(QLineF(o.x(), o.y() - 20, o.x(), o.y() + 20))
            painter.drawLine(QLineF(o.x() - 20, o.y(), o.x() + 20, o.y()))    
            
    def setXGridSize(self, size):
        self._gridSizeX = size
        self.update()
        
    def setYGridSize(self, size):
        self._gridSizeY = size
        self.update()
        
    def setGridSize(self, size):
        self._gridSizeX = size
        self._gridSizeY = size
        self.update()
        
    def setGridEnabled(self, enable):
        self._gridEnabled = enable
        self.update()
        
    def gridEnabled(self):
        return self._gridEnabled
    
    def pickGridOrigin(self):
        self._pickGridOrigin = True
        
    def gridSizeX(self):
        return self._gridSizeX
    
    def gridSizeY(self):
        return self._gridSizeY
    
    def gridOrigin(self):
        return self._gridOrigin    
    
    def setBackgroundBrush(self, brush):
        super().setBackgroundBrush(brush)
        self.backgroundColorChanged.emit(brush.color())
        