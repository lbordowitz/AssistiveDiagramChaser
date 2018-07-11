from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt, pyqtSignal
from copy import deepcopy


class Editor(QGraphicsView):
    focused = pyqtSignal()
    
    def __init__(self, new=True):
        super().__init__()
        if new:
            self._editable = True
            self._wheelZoom = True
            self._zoomFactor = (1.1, 1.1)
            self._zoomLimit = 20
            self._scale = (1.0, 1.0)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        
    def setEditable(self, enable):
        self._editable = enable
        
    def editable(self):
        return self._editable
    
    def setScene(self, scene):
        scene.selectionChanged.connect(self.itemSelectionChanged)
        scene.setEditor(self)
        super().setScene(scene)
        
    def __setstate__(self, data):
        self.__init__(new=False)
        self.setScene(data["scene"])
        self._zoomFactor = data["zoom factor"]
        self._zoomLimit = data["zoom limit"]
        self.setScale(data["scale"])
    
    def __getstate__(self):
        return {
            "scene" : self.scene(),
            "zoom factor" : self._zoomFactor,
            "zoom limit" : self._zoomLimit,
            "scale" : self._scale
        }
    
    def __deepcopy__(self):
        copy = type(self)(new=False)
        memo[id(self)] = self
        copy.setScene(deepcopy(self.scene()))
        copy._zoomFactor = self._zoomFactor
        copy._zoomLimit = self._zoomLimit
        copy.setScale(self.getScale())
        copy.super().scale(copy._scale)
        
    def getScale(self):
        return self._scale
            
    def setScale(self, scale):
        s = self._scale
        super().scale(scale[0]/s[0], scale[1]/s[1])
        self._scale = scale    
        
    def wheelEvent(self, event):
        if self._wheelZoom:
            s = self.scale()
          
            #Scale the view / do the zoom
            if event.angleDelta().y() > 0:
                #Zoom in
                if s[0] < self._zoomLimit:
                    s = self._zoomFactor
                else:
                    return
            else:
                if s[0] > 1/self._zoomLimit:
                    s = self._zoomFactor
                    s = (1.0/s[0], 1.0/s[1])
                else:
                    return
            
            self.setTransformationAnchor(self.AnchorUnderMouse)
            super().scale(*s)
            self.scene().update()
        
    def focusInEvent(self, event):
        self.focused.emit()
        super().focusInEvent(event)    