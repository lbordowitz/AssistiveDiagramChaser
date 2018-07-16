from category_object import CategoryObject
from geom_tools import minBoundingRect, paintSelectionShape
from PyQt5.QtCore import QEvent, pyqtSignal, Qt
from PyQt5.QtGui import QColor
from gfx_object import GfxObject
from copy import deepcopy
from qt_tools import SimpleBrush, Pen
from commands import MethodCallCommand

class CategoryDiagram(CategoryObject):
    def __init__(self, new=True):
        self._objects = {}
        self._morphisms = {}
        super().__init__(new)
        self._editing = False
        if new:
            self.setBrush(SimpleBrush(QColor(255,0,127,200)))   # Semi-transparent
            self.setPen(Pen(Qt.NoPen))
            self.setLabelText(0, "C")
            pos = self.label(0).pos()
            self.label(0).setPos(pos.x(), pos.y() - self.label(0).boundingRect().height())
            self._insetPadding = 3 * self._insetPadding
                
    def paint(self, painter, option, widget):
        if self.isSelected() and self.scene():
            paintSelectionShape(painter, self)
        painter.setRenderHints(painter.Antialiasing | painter.HighQualityAntialiasing)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        r = self._cornerRadius
        painter.drawRoundedRect(self.boundingRect(), r, r)
        
    def boundingRect(self):
        rect_list = [child.boundingRect().translated(child.pos()) for child in self.objects().values()]
        if rect_list:
            w = self._insetPadding
            return minBoundingRect(rect_list).adjusted(-w, -w, w, w)
        return self._defaultRect
    
    def objects(self):
        return self._objects
    
    def morphisms(self):
        return self._morphisms
        
    #def sceneEventFilter(self, watched, event):
        #if watched.uid() in self._objects:
            #if event.type() == QEvent.GraphicsSceneMouseMove:
                #self.updateArrowsAndClearResidual()
        #return False
    
    def editing(self):
        return self._editing
    
    def setEditing(self, edit):
        self._editing = edit
        
    def updateArrows(self):
        super().updateArrows()
        for child in self._objects.values():
            child.updateGraph() 
            
    def clearGraphAlgoVisitedFlags(self):
        for obj in self._objects.values():
            obj.clearGraphAlgoVisited()
            
    def composeArrows(self):
        for obj in self._objects:
            X = obj
            for f in obj.outgoingArrows():
                Y = f.toNode()
                if Y:
                    for g in Y.outgoingArrows():
                        gf = self.editor().ArrowType()
                        gf.setLabelText(0, g.labelText(0) + f.labelText(0))
                        gf.setFrom(X)
                        gf.setTo(g.codomain())
                        self.editor().attachArrow(gf)
                        
    def addMorphism(self, arr, undoable=False, loops=None):
        if arr.uid() not in self._morphisms:
            if loops is None:
                loops = 1
            if arr.uid() not in self._morphisms:
                if undoable:
                    self.editor().pushCommand(MethodCallCommand("Adding morphism " + str(arr) + " to category " + str(self),
                                                         self.addMorphism, [arr], self.removeMorphism, [arr], self.editor()))
                else:
                    arr.deleted.connect(lambda a: self.removeMorphism(arr))
                    self.editor().setupArrowConnections(arr)
                    arr.setEditor(self.editor())
                    self.scene().addItem(arr)
                    arr.setParentItem(self)
                    self._morphisms[arr.uid()] = arr
                    self.updateArrows()
                    self.updateFunctorImages()
        
    def removeMorphism(self, arr, undoable=False, loops=None):
        if arr.uid() in self._morphisms:
            if loops is None:
                loops = 1
            if arr.uid() in self._morphisms:
                if undoable:
                    self.editor().pushCommand(MethodCallCommand("Removing morphism " + str(arr) + " from category " + str(self),
                                                         self.removeMorphism, [arr], self.addMorphism, [arr], self.editor()))
                else:
                    if arr.scene():
                        self.scene().removeItem(arr)
                    arr.setEditor(None)
                    arr.setParentItem(None)
                    del self._morphisms[arr.uid()]
                    self.updateArrowsAndClearResidual()
                    self.updateFunctorImages()
                
    def addObject(self, obj, undoable=False):
        if obj.uid() not in self._objects:
            if obj.uid() not in self._objects:
                if undoable:
                    getText = lambda: "Adding object " + str(obj) + " to category " + str(self)
                    command = MethodCallCommand(getText(), self.addObject, [obj], self.removeObject, [obj], self.editor())
                    slot = lambda symbol: command.setText(getText())
                    self.symbolChanged.connect(slot) 
                    obj.symbolChanged.connect(slot)
                    self.editor().pushCommand(command)
                else:
                    obj.deleted.connect(lambda o: self.removeObject(obj))
                    obj.setParentItem(self)
                    self._objects[obj.uid()] = obj
                    obj.installSceneEventFilter(self)
                    self.updateArrows()
                    obj.positionChanged.connect(lambda pos: self.updateArrowsAndClearResidual())
                    self.updateFunctorImages()
                                        
    def removeObject(self, obj, undoable=False, loops=None):
        if obj.uid() in self._objects:
            if loops is None:
                loops = 1
            if obj.uid() in self._objects:
                if undoable:
                    getText = lambda: "Removing object " + str(obj) + " from category " + str(self)
                    self.editor().pushCommand(getText(), self.removeObject, [obj], self.addObject, [obj], self.editor())
                    slot = lambda symbol: command.setText(getText())
                else:
                    obj.setParentItem(None)
                    if self.scene():
                        self.scene().removeItem(obj)
                    if obj.uid() in self._objects:
                        del self._objects[obj.uid()]
                    obj.removeSceneEventFilter(self)
                    self.updateArrowsAndClearResidual()
                    self.updateFunctorImages()
        
    def attachArrow(self, fun):
        super().attachArrow(fun)
        
    def canConnectTo(self, item, at_start):
        if at_start:
            other_end = self.codomain()
        else:
            other_end = self.domain()
        if isinstance(other_end, CategoryDiagram) and other_end.parentItem() is item.parentItem() and \
           isinstance(item, CategoryDiagram):
            return True
        return False    
    
    def updateFunctorImages(self):
        for F in self.outgoingArrows():
            F.updateImage()
            
    def getMorphism(self, uid):
        return self._morphisms.get(uid, None)
    
    def getObject(self, uid):
        return self._objects.get(uid, None)
    
    def nonempty(self):
        res = False
        if self._morphisms:
            res = True
        elif self._objects:
            res = True
        return res