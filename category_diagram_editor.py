from graph_editor import GraphEditor
from category_object import CategoryObject
from category_arrow import CategoryArrow
from qt_tools import simpleMaxContrastingColor, Pen, firstParentGfxItemOfType
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QMenu
import re
from graph_arrow import ControlPoint
from category import Category

class CategoryDiagramEditor(GraphEditor):
    def __init__(self, new=True):
        super().__init__()
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
            if isinstance(item, Category) and item.editing():
                node = self.NodeType()
                node.setEditor(self)
                node.setContextMenu(self.buildNodeContextMenu(node))
                #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
                node.focusedIn.connect(lambda: self.nodeFocusedIn(node))
                node.setZValue(-1.0)
                #self.scene().placeItems(node, pos)
                item.addObject(node)
                node.setPos(item.mapFromScene(pos))
                self.scene().placeItems(node, add=False)
                item = node
            elif isinstance(item, CategoryObject):
                arr = self.ArrowType()
                arr.setEditor(self)
                arr.setFrom(item)
                self.addArrow(arr)
                self.scene().placeItems(arr.toPoint(), pos)           
                if isinstance(item, Category):
                    arr.setLabelText(0, "F")
                item = arr  
        else:
            node = Category()
            node.setEditor(self)
            node.setContextMenu(self.buildCategoryContextMenu(node))
            #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
            node.focusedIn.connect(lambda: self.nodeFocusedIn(node))
            node.setZValue(-1.0)
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
        action = menu.addAction("Edit Diagram")
        action.setCheckable(True)
        action.setChecked(False)
        action.toggled.connect(lambda b: cat.setEditing(b))
        return menu
    
    def arrowStartHasChanged(self, arr, pos):
        items = self.scene().items(pos)
        for item in items:
            item = firstParentGfxItemOfType(item, self.NodeType)
            if item:
                if arr.toNode() and isinstance(arr.toNode().parentItem(), Category):
                    cat = arr.toNode().parentItem()
                    if item in cat.objects():
                        arr.setFrom(item)
                else:
                    arr.setFrom(item)
                break    
            
    def arrowEndHasChanged(self, arr, pos):
        items = self.scene().items(pos)
        for item in items:
            item = firstParentGfxItemOfType(item, self.NodeType)
            if item:
                if arr.fromNode() and isinstance(arr.fromNode().parentItem(), Category):
                    cat = arr.fromNode().parentItem()
                    if item in cat.objects():
                        arr.setTo(item)
                else:
                    arr.setTo(item)
                break
            
    def buildSceneContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        delete = menu.addAction("Delete").triggered.connect(self.deleteItems)
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
            if isinstance(item, CategoryObject):
                self.removeNode(item)
            elif isinstance(item, CategoryArrow):
                self.removeArrow(item)
            parent = item.parentItem()
            if parent:
                if isinstance(parent, Category):
                    parent.removeObject(item)

    def addObjectToCategory(self, obj, cat):
        obj.setContextMenu(self.buildNodeContextMenu(obj))
        #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
        obj.focusedIn.connect(lambda: self.nodeFocusedIn(obj))
        obj.setZValue(-1.0)
        #self.scene().placeItems(node, pos)
        cat.addObject(obj)
        for arr in obj.arrows():
            self.addArrow(arr)        