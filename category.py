from category_object import CategoryObject
from geom_tools import minBoundingRect, paintSelectionShape
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtGui import QColor
from gfx_object import GfxObject
from copy import deepcopy
from qt_tools import SimpleBrush

class Category(CategoryObject):
    subitemAdded = pyqtSignal(GfxObject)
    subitemRemoved = pyqtSignal(GfxObject)
    
    def __init__(self, new=True):
        self._objects = []
        super().__init__()
        self._editing = False
        self._functorImages = {}
        if new:
            self.setBrush(SimpleBrush(QColor(0,255,100,50)))   # Semi-transparent
            self.setLabelText(0, "C")
                
    def paint(self, painter, option, widget):
        if self.isSelected() and self.scene():
            paintSelectionShape(painter, self)
        painter.setRenderHints(painter.Antialiasing | painter.HighQualityAntialiasing)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        r = self._cornerRadius
        painter.drawRoundedRect(self.boundingRect(), r, r)
        
    def boundingRect(self):
        rect_list = [child.boundingRect().translated(child.pos()) for child in self.objects()]
        if rect_list:
            w = self._insetPadding
            return minBoundingRect(rect_list).adjusted(-w, -w, w, w)
        return self._defaultRect
    
    def objects(self):
        return self._objects
    
    def addObject(self, item):
        item.setParentItem(self)
        self._objects.append(item)
        item.installSceneEventFilter(self)
        self.update()
        self.subitemAdded.emit(item)
        
    def removeObject(self, item):
        item.setParentItem(None)
        if self.scene():
            self.scene().removeItem(item)
        self._objects.remove(item)
        item.removeSceneEventFilter(self)
        self.subitemRemoved.emit(item)
        
    def sceneEventFilter(self, watched, event):
        if watched in self._objects:
            if event.type() == QEvent.GraphicsSceneMouseMove:
                self.updateArrowsAndClearResidual()
        return False
    
    def editing(self):
        return self._editing
    
    def setEditing(self, edit):
        self._editing = edit
        
    def updateArrows(self):
        super().updateArrows()
        for child in self._objects:
            child.updateGraph() 
            
    def addArrow(self, arr):
        super().addArrow(arr)
        arr.takeFunctorImage()
        
    def removeArrow(self, arr):
        arr.undoTakeFunctorImage()
        super().removeArrow(arr)
        
    def clearGraphAlgoVisitedFlags(self):
        for obj in self._objects:
            obj.clearGraphAlgoVisited()
            
    # Returns list of objects only, arrows come referenced by objects
    def deepcopyGraph(self):
        memo = {}
        memo[id(self)] = self
        obj_list = []
        for obj in self._objects:
            obj_list.append(deepcopy(obj, memo))
        return obj_list