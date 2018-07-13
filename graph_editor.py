from PyQt5.QtWidgets import QMenu, QActionGroup, QAction, QLineEdit
from graph_scene import GraphScene
from editor import Editor
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QObject
from PyQt5.QtGui import QTransform
from qt_tools import unpickleDragMode, unpickleFocusPolicy, firstParentGfxItemOfType
from graph_node import GraphNode
from graph_arrow import ControlPoint, GraphArrow
from text_item import TextItem
from geom_tools import mag2D
from int_spin_dialog import IntSpinDialog

class GraphEditor(Editor):
    ZoomScreenSizeFraction = 0.7
    zoomInRequest = pyqtSignal(str)
    
    def __init__(self, new=True):
        super().__init__(new)
        if new:
            self._nodes = []
            self._arrows = []
        self._groupAction = None
        self.NodeType = GraphNode
        self.ArrowType = GraphArrow
        self._zoomItem = None
        self._gridSpacing = IntSpinDialog("Grid Spacing: ")
        self._gridSpacing.spinBox.setMinimum(1)
                
    def __setstate__(self, data):
        super().__setstate__(data)
        self._nodes = data["nodes"]
        self._arrows = data["arrows"]
                        
    def __getstate__(self):
        data = super().__getstate__()
        data["nodes"] = self._nodes
        data["arrows"] = self._arrows
        return data
        
    def setupDefaultUserExperience(self):
        self._wheelZoom = True
        self.scene().backgroundDoubleClicked.connect(self.sceneBackgroundDoubleClicked)
        self.scene().dragStarted.connect(lambda objs, point: self.setDragMode(self.NoDrag))
        self.scene().dragEnded.connect(lambda objs, point: self.setDragMode(self.RubberBandDrag))
        self.scene().itemsPlaced.connect(self.sceneItemsPlaced)
        self.scene().setContextMenu(self.buildSceneContextMenu())
        self._gridSpacing.spinBox.valueChanged.connect(self.scene().setGridSize)
        self._gridSpacing.spinBox.setValue(self.scene().gridSizeX())
        self._gridSpacing.spinBox.setMaximum(10000)
        
    def nodes(self):
        return self._nodes
    
    def setNodes(self, nodes):
        self._nodes = nodes
        for node in nodes:
            self.scene().addItem(node)
    
    def addNode(self, node):
        self._nodes.append(node)
        self.scene().addItem(node)
    
    def removeNode(self, node):
        if node in self._nodes:
            self._nodes.remove(node)
            for arr in node.arrows():
                if arr.toNode() is node:
                    arr.setTo(None)
                elif arr.fromNode() is node:
                    arr.setFrom(None)
            self.scene().removeItem(node)
        
    def removeArrow(self, arr):
        if arr in self._arrows:
            self._arrows.remove(arr)
            self.scene().removeItem(arr)
            arr.setTo(None)
            arr.setFrom(None)
        
    def scale(self):
        return self._scale
            
    def getScale(self):
            return self._scale
            
    def setScale(self, scale):
        s = self._scale
        super().scale(scale[0]/s[0], scale[1]/s[1])
        self._scale = scale
    
    #def zoom100Percent(self):
        #self.setTransformationAnchor(self.AnchorUnderMouse)
        #transform = self.transform()
        #scaleX = getPositiveXscaleFromTransform(transform)
        #scaleY = getPositiveYscaleFromTransform(transform) 
        #self.setTransform(transform.scale(1.0/scaleX, 1.0/scaleY).scale(self.scaleX, self.scaleY))    #IDK why this works...
        #self.scale(1.0/self.scaleX, 1.0/self.scaleY)
    
    def wheelEvent(self, event):
        if self._wheelZoom:
            s = self.scale()
            #Scale the view / do the zoom
            if event.angleDelta().y() > 0:
                #Zoom in
                if s[0] < self._zoomLimit:
                    s = self._zoomFactor
                    zoom_dir = 1
                else:
                    return
            else:
                if s[0] > 1/self._zoomLimit:
                    s = self._zoomFactor
                    s = (1.0/s[0], 1.0/s[1])
                    zoom_dir = -1
                else:
                    return
            self.setTransformationAnchor(self.AnchorUnderMouse)
            super().scale(*s)
            self.scene().update()
            items = self.scene().items(self.mapToScene(event.pos()))
            if items:
                for item in items:
                    if isinstance(item, (GraphNode, GraphArrow)):
                        if item is not self._zoomItem:
                            if self._zoomItem:
                                self._zoomItem.clearZoom()
                            self._zoomItem = item
                        item.zoom(zoom_dir)
                        break
                    
    def focusInEvent(self, event):
        self.focused.emit()
        super().focusInEvent(event)    
        
    def addArrow(self, arr, scene=True):
        #arr.zoomedIn.connect(lambda: self.arrowZoomedIn(arr))
        arr.focusedIn.connect(lambda: self.arrowFocusedIn(arr))
        ctrl_pts = arr.controlPoints()
        ctrl_pts[0].mouseDragBegan.connect(lambda pos: self.arrowStartAboutToChange(arr, pos))
        ctrl_pts[-1].mouseDragBegan.connect(lambda pos: self.arrowEndAboutToChange(arr, pos))
        ctrl_pts[0].mouseDragEnded.connect(lambda pos: self.arrowStartHasChanged(arr, pos))
        ctrl_pts[-1].mouseDragEnded.connect(lambda pos: self.arrowEndHasChanged(arr, pos))        
        arr.setContextMenu(self.buildArrowContextMenu(arr))
        self._arrows.append(arr)
        if scene:
            self.scene().addItem(arr)
            
    def placeItem(self, pos):
        item = self.scene().itemAt(pos, QTransform())
        if item:
            if isinstance(item, self.NodeType):
                arr = self.ArrowType()
                arr.setFrom(item)
                self.addArrow(arr)
                self.scene().placeItems(arr.toPoint(), pos)
                return arr
        node = self.NodeType()
        node.setContextMenu(self.buildNodeContextMenu(node))
        #node.zoomedIn.connect(lambda: self.nodeZoomedIn(node))
        node.focusedIn.connect(lambda: self.nodeFocusedIn(node))
        node.setZValue(-1.0)
        self.addNode(node) 
        self.scene().placeItems(node, pos)
        return node
    
    def arrowStartAboutToChange(self, arr, pos):
        arr.setFrom(None)
    
    def arrowStartHasChanged(self, arr, pos):
        items = self.scene().items(pos)
        for item in items:
            item = firstParentGfxItemOfType(item, self.NodeType)
            if item:
                arr.setFrom(item)
                break
                
    def arrowEndAboutToChange(self, arr, pos):
        arr.setTo(None)
                    
    def arrowEndHasChanged(self, arr, pos):
        items = self.scene().items(pos)
        for item in items:
            item = firstParentGfxItemOfType(item, self.NodeType)
            if item:
                arr.setTo(item)
                break
    
    def setCodeEditorTo(self, editor):
        raise NotImplementedError
    
    def buildNodeContextMenu(self, node, menu=None):
        if menu is None:
            menu = QMenu()
        return node.buildDefaultContextMenu(menu) 
    
    def buildArrowContextMenu(self, arr):
        menu = QMenu()
        return arr.buildDefaultContextMenu(menu)
    
    def buildSceneContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        menu.addSeparator()
        action = menu.addAction("Snap Grid")
        action.toggled.connect(lambda b: self.scene().setGridEnabled(b))
        action.setCheckable(True)
        action.setChecked(self.scene().gridEnabled())
        action = menu.addAction("Grid Spacing").triggered.connect(self._gridSpacing.exec_)
        action = menu.addAction("Pick Grid Origin").triggered.connect(lambda b: self.scene().setPickGridOrigin(True))
        return menu
    
    def itemSelectionChanged(self):
        pass
            
    def nodeZoomedIn(self, node):
        raise NotImplementedError
    
    def arrowZoomedIn(self, arrow):
        raise NotImplementedError
    
    def nodeFocusedIn(self, node):
        raise NotImplementedError
    
    def arrowFocusedIn(self, arrow):
        raise NotImplementedError
    
    def sceneItemsPlaced(self, items):
        raise NotImplementedError
    
    def sceneBackgroundDoubleClicked(self, pos):
        item = self.scene().itemAt(pos, QTransform())
        if item:
            if isinstance(item, TextItem):
                item.setTextInteraction(True)
            else:
                self.placeItem(pos)
        else:
            self.placeItem(pos)