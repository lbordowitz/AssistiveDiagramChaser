from graph_editor import GraphEditor
from category_object import CategoryObject
from category_arrow import CategoryArrow
from qt_tools import simpleMaxContrastingColor, Pen, firstParentGfxItemOfType
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QMenu
import re
from PyQt5.QtCore import Qt
from graph_arrow import ControlPoint
from diagram import Diagram
from functor import Functor

class CategoryDiagramEditor(GraphEditor):
    def __init__(self, window, new=True):
        super().__init__(window, new)
        self.NodeType = CategoryObject
        self.ArrowType = CategoryArrow
        if new:
            pass
        self._focusedNode = None
        
    def setScene(self, scene):
        super().setScene(scene)
        scene.backgroundColorChanged.connect(lambda color: self._autoSetCodeColor(simpleMaxContrastingColor(color)))
        scene.setGridEnabled(True)
        self.setupDefaultUserExperience()
        
    def placeItem(self, pos):
        item = self.scene().itemAt(pos, QTransform())
        if item:
            if isinstance(item, Diagram) and item.editing():
                node = self.NodeType()
                node.setEditor(self)
                node.setContextMenu(self.buildNodeContextMenu(node))
                #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
                node.focusedIn.connect(lambda: self.nodeFocusedIn(node))
                node.setZValue(-1.0)
                #self.scene().placeItems(node, pos)
                item.addObject(node, undoable=True)
                node.setPos(item.mapFromScene(pos))
                self.scene().placeItems(node, add=False)
                item = node
            elif isinstance(item, Diagram):
                C = item
                F = Functor()
                F.setFrom(C)
                F.setContextMenu(self.buildArrowContextMenu(F))
                F.setLabelText(0, "F")     
                F.setEditor(self)
                self.addArrow(F)
                self.scene().placeItems(F.toPoint(), pos)
                item = F
            elif isinstance(item, CategoryObject):
                arr = self.ArrowType()
                self.setupArrowConnections(arr)
                arr.setEditor(self)
                arr.setFrom(item)
                parent = item.parentItem()
                if parent:
                    parent.addMorphism(arr, undoable=True)
                    add = False
                    pos = parent.mapFromScene(pos)
                else:
                    add = True
                self.scene().placeItems(arr.toPoint(), pos, add=add)
                item = arr  
        else:
            node = Diagram()
            node.setEditor(self)
            node.setContextMenu(self.buildCategoryContextMenu(node))
            #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
            node.focusedIn.connect(lambda: self.nodeFocusedIn(node))
            node.setZValue(0.0)
            self.addNode(node) 
            self.scene().placeItems(node, pos)   
            item = node        
        if isinstance(item, CategoryArrow):
            item.setFlag(item.ItemIsMovable, False)
        return item

    def nodeFocusedIn(self, node):
        self._focusedNode = node        
        
    def arrowFocusedIn(self, arrow):
        pass
    
    def sceneItemsPlaced(self, items):
        if len(items) == 1:
            item = items[0]
            if isinstance(item, ControlPoint):
                item.parentItem().label(0).setTextInteraction(True)
            elif isinstance(item, self.NodeType):
                item.label(0).setTextInteraction(True)
                
    def buildCategoryContextMenu(self, cat, menu=None):
        if menu is None:
            menu = QMenu()
        menu = self.buildNodeContextMenu(cat, menu)
        menu.addSeparator()
        menu.addAction("Compose Arrows").triggered.connect(lambda b: cat.composeArrows())
        menu.addSeparator()
        action = menu.addAction("Edit Diagram")
        action.setCheckable(True)
        action.setChecked(False)
        action.toggled.connect(lambda b: cat.setEditing(b))
        return menu
    
    def arrowExtremityHasChanged(self, arr, pos, is_start=False):
        items = self.scene().items(pos)
        filtered = []
        for item in items:
            if item is arr.parentItem():
                continue
            if item is arr:
                continue
            if isinstance(item, ControlPoint):
                continue
            filtered.append(item)
        if filtered:
            for item in filtered:
                item = firstParentGfxItemOfType(item, self.NodeType)
                if item:  # There is a node!
                    if arr.canConnectTo(item, is_start):
                        if is_start:
                            arr.setFrom(item, undoable=True)
                        else:
                            arr.setTo(item, undoable=True)
                        break 
        else:
            # There is no sufficient item at pos
            if is_start:
                arr.setFrom(None, undoable=True)
            else:
                arr.setTo(None, undoable=True)            
            
    def buildSceneContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        return super().buildSceneContextMenu(menu)
    
    def deleteItems(self, items=None):
        if items is None:
            items = self.scene().selectedItems()
        children = []
        for item in items:
            children += item.childItems()
        filtered = []
        for item in items:
            if item not in children:
                filtered.append(item)
        for item in filtered:
            item.delete()