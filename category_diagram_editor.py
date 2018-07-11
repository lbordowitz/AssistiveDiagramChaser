from graph_editor import GraphEditor
from category_object import CategoryObject
from category_arrow import CategoryArrow
from qt_tools import simpleMaxContrastingColor, Pen
import re
from graph_arrow import ControlPoint

class CategoryDiagramEditor(GraphEditor):
    GettingCalledCode, Neutral = range(2)
    
    def __init__(self, new=True):
        super().__init__()
        self.NodeType = CategoryObject
        self.ArrowType = CategoryArrow
        if new:
            self._autoCodeColor = True
        self._appState = self.Neutral
        self.addCodeEditor = None
        self._focusedNode = None
        
    def setScene(self, scene):
        super().setScene(scene)
        scene.backgroundColorChanged.connect(lambda color: self._autoSetCodeColor(simpleMaxContrastingColor(color)))
        scene.setGridEnabled(True)
        self.setupDefaultUserExperience()
        
    def placeItem(self, pos):
        item = super().placeItem(pos)
        if isinstance(item, CategoryArrow):
            item.setFlag(item.ItemIsMovable, False)
        return item
        
    def _autoSetCodeColor(self, color):
        if self._autoCodeColor:
            self.setCodeColor(color)
    
    def setCodeColor(self, color):
        for node in self._nodes:
            node.codeItem().setDefaultTextColor(color)
        for arrow in self._arrows:
            arrow.codeItem().setDefaultTextColor(color)
            
    SimpleCallRegex = re.compile(r'')       
    def nodeZoomedIn(self, state):
        self._appState = self.GettingCalledCode
        exec(state.code())
    
    def arrowZoomedIn(self, arrow):
        pass
            
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
                