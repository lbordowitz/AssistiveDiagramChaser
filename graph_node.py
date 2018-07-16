from PyQt5.QtWidgets import QGraphicsTextItem, QMenu, QColorDialog, QGraphicsSceneEvent
from geom_tools import minBoundingRect
from PyQt5.QtCore import QRectF, QPointF, Qt, QEvent, pyqtSignal
from qt_tools import unpickleGfxItemFlags, unpickleRenderHints, SimpleBrush, Pen, setPenColor
from PyQt5.QtGui import QPainter, QTransform, QPen, QBrush, QColor
from geom_tools import paintSelectionShape, rectToPoly, mag2D, closestRectPoint, closestPolyPoint, polygonFromArc
from text_item import TextItem
from gfx_object import GfxObject
from labeled_gfx import LabeledGfx
from copy import deepcopy

class GraphNode(GfxObject, LabeledGfx):
    DefaultRect = QRectF(-15, -15, 30, 30)
    DefaultCornerRadius = 7
    DefaultInsetPadding = 15
    Circle, RoundedRect = range(2)
    symbolChanged = pyqtSignal(str)
    
    def __init__(self, new=True):
        super().__init__(new)
        super().__init__(new)
        self._contextMenu = None
        self._shape = self.RoundedRect
        if new:
            self._insetPadding = self.DefaultInsetPadding
            self._defaultRect = self.DefaultRect
            self._cornerRadius = self.DefaultCornerRadius
            self._arrows = []
            self._boundScale = (1.0, 1.0)
            self._brush = SimpleBrush(Qt.cyan)
            self._pen = Pen(Qt.yellow, 2.0)
            self.setupConnections()                   
        self.setFiltersChildEvents(True)
        self._renderHints = QPainter.Antialiasing | QPainter.HighQualityAntialiasing | QPainter.SmoothPixmapTransform            
        self.setAcceptHoverEvents(True)
        self._hover = False
        
    def __setstate__(self, data):
        super().__setstate__(data)
        super().__setstate__(data)
        self._insetPadding = data["inset padding"]
        self._defaultRect = data["default rect"]
        self._cornerRadius = data["corner radius"]
        self._arrows = data["arrows"]
        self._boundScale = data["bound scale"]        
        self.setupConnections()
        self.updateArrowsAndClearResidual()
        
    def __getstate__(self):
        data = super().__getstate__()
        data = {**data, **super().__getstate__()}
        data["inset padding"] = self._insetPadding
        data["default rect"] = self._defaultRect
        data["corner radius"] = self._cornerRadius
        data["arrows"] = self._arrows
        data["bound scale"] = self._boundScale
        return data
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._shape = self._shape
        copy._defaultRect = QRectF(self._defaultRect)
        copy._insetPadding = self._insetPadding
        copy._cornerRadius = self._cornerRadius
        copy._arrows = deepcopy(self._arrows, memo)
        #for arr in copy._arrows:
            #assert(arr.toNode() is self or arr.fromNode() is self)
        copy._boundScale = tuple(self._boundScale)
        copy._brush = deepcopy(self._brush, memo)
        copy.setupConnections()
        return copy        

    def hoverEnterEvent(self, event):
        self._hover = True
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self._hover = False
        super().hoverLeaveEvent(event)
        
    def sceneEventFilter(self, watched, event):
        if event.type() == QEvent.GraphicsSceneMouseMove and mag2D(event.scenePos() - event.lastScenePos()) > 1:
            self.updateArrows()
            self.scene().update()
        return False
    
    def cornerRadius(self):
        return self._cornerRadius
    
    def setCornerRadius(self, radius):
        self._cornerRadius = radius
        self.changed.emit()
        self.update()
    
    def setupConnections(self):
        self.setFlags(self.ItemIsMovable | self.ItemIsFocusable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
        self._brushColorDlg = QColorDialog(self.brush().color())
        self._brushColorDlg.setOption(QColorDialog.ShowAlphaChannel, True)
        self._brushColorDlg.currentColorChanged.connect(lambda col: self.setBrush(SimpleBrush(col)))
        self._penColorDlg = QColorDialog(self.pen().color())
        self._penColorDlg.setOption(QColorDialog.ShowAlphaChannel, True)
        self._penColorDlg.currentColorChanged.connect(lambda col: self.setPen(setPenColor(self.pen(), col)))        
      
    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            self.updateArrows()
            if self.scene():
                self.scene().update()
        return super().itemChange(change, value)    

    def arrows(self):
        return self._arrows
    
    def attachArrow(self, arr):
        self._arrows.append(arr)
        self.updateArrows()
        
    def detachArrow(self, arr):
        if arr in self._arrows:
            self._arrows.remove(arr)
            self.updateArrows()
            
    def boundingRect(self):
        w = self._insetPadding
        rect = self.childrenBoundingRect()
        rect.translate(-rect.center())
        rect.adjust(-w, -w, w, w)
        return rect        
    
    def setDefaultBoundingRect(self, rect=None):
        if rect is None:
            rect = self.DefaultRect
        self._defaultRect = rect
        self.changed.emit()
        self.update()
        
    def defaultBoundingRect(self):
        return self._defaultRect
        
    def paint(self, painter, option, widget):
        if self.scene():
            if self.isSelected():
                paintSelectionShape(painter, self)
            painter.setRenderHints(self.renderHints())
            painter.setBrush(self.brush())
            if self._hover:
                painter.setPen(self.pen())
            else:
                painter.setPen(QPen(Qt.NoPen))
            if self._shape == self.RoundedRect:
                painter.drawRoundedRect(self.boundingRect(), self.cornerRadius(), self.cornerRadius())
            elif self._shape == self.Circle:
                rect = self.boundingRect()
                if rect.width() > rect.height():
                    rect.setX(rect.x() - (rect.height() - rect.width()) / 2)
                    rect.setWidth(rect.height())
                elif rect.height() > rect.width():
                    rect.setY(rect.y() - (rect.width() - rect.height()) / 2)
                    rect.setHeight(rect.width())
                pen_w = self.pen().width()
                rect.adjust(pen_w, pen_w, -pen_w, -pen_w)
                painter.drawEllipse(rect)
            painter.setPen(QPen(Qt.red, 2.0))

    def setRenderHints(self, hints):
        self._renderHints = hints
        self.update()
        
    def renderHints(self):
        return self._renderHints

    def centerChild(self, child):
        rect = child.boundingRect()
        center = self.boundingRect().center()
        delta = center - rect.center()
        child.setPos(child.pos() + delta)

    def closestBoundaryPos(self, pos):
        rect = self.boundingRect()
        #s = self._boundScale
        #T = QTransform.fromScale(1/s[0], 1/s[1])
        #rect = T.mapRect(rect)
        if pos.x() < rect.left():
            x = rect.left()
        elif pos.x() > rect.right():
            x = rect.right()
        else:
            x = pos.x()
        if pos.y() < rect.top():
            y = rect.top()
        elif pos.y() > rect.bottom():
            y = rect.bottom()
        else:
            y = pos.y()
        rect_point = QPointF(x, y)
        r = self.cornerRadius()
        poly = None
        if mag2D(rect_point - rect.bottomRight()) <= r:
            poly = polygonFromArc(rect.bottomRight() + QPointF(-r, -r), r, 0, 90, seg=30)
        elif mag2D(rect_point - rect.topRight()) <= r:
            poly = polygonFromArc(rect.topRight() + QPointF(-r, r), r, 270, 360, seg=30)
        elif mag2D(rect_point - rect.topLeft()) <= r:
            poly = polygonFromArc(rect.topLeft() + QPointF(r, r), r, 180, 270, seg=30)
        elif mag2D(rect_point - rect.bottomLeft()) <= r:
            poly = polygonFromArc(rect.bottomLeft() + QPointF(r, -r), r, 90, 180, seg=30)
        if poly is None:
            return rect_point
        else:
            return closestPolyPoint(poly, pos)[0]
    
    def updateArrows(self):
        for arr in self._arrows:
            arr.updatePosition()
                
    def updateArrowsAndClearResidual(self):
        self.updateArrows()
        if self.scene(): 
            self.scene().update()
            
    def contextMenuEvent(self, event):
        if self._contextMenu:
            self._contextMenu.exec_(event.screenPos())
            
    def buildDefaultContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        col_menu = menu.addMenu("Color")
        col_menu.addAction("Brush").triggered.connect(lambda: self._brushColorDlg.exec_())
        col_menu.addAction("Pen").triggered.connect(lambda: self._penColorDlg.exec_())
        return menu
    
    def setContextMenu(self, menu):
        self._contextMenu = menu
    
    def brush(self):
        return self._brush
    
    def setBrush(self, brush):
        self._brush = brush
        self._brushColorDlg.setCurrentColor(brush.color())
        self.update()
    
    def pen(self):  
        return self._pen
    
    def setPen(self, pen):
        self._pen = pen
        self._penColorDlg.setCurrentColor(pen.color())
        self.update()
        
    def saveTextPosition(self):
        pass
    
    def updateTextPosition(self):
        pass
    
    def addLabel(self, label):
        label = super().addLabel(label)
        if isinstance(label, TextItem):
            label.onPositionChanged = self.updateArrowsAndClearResidual
        return label
    
    def updateGraph(self):
        self.updateArrows()
    
    def delete(self, deleted=None):
        if deleted is None:
            deleted = {}
        deleted["arrows"] = []
        for arr in self.arrows():
            if arr.toNode() is self:
                arr.setTo(None)
                deleted["arrows"].append((arr, 1))
            else:
                arr.setFrom(None)
                deleted["arrows"].append((arr, 0))
        super().delete(deleted)
        return deleted

    def undelete(self, deleted, emit=True):
        super().undelete(deleted, emit=False)
        for arr, isstart in deleted["arrows"]:
            if isstart == 0:
                arr.setFrom(self)
            else:
                arr.setTo(self)
        if emit:
            self.undeleted.emit(self)

    def setEditable(self, editable):
        super().setEditable(editable)
        super().setEditable(editable)        