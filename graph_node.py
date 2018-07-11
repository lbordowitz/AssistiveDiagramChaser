from PyQt5.QtWidgets import QGraphicsTextItem, QMenu, QColorDialog, QGraphicsSceneEvent
from geom_tools import minBoundingRect
from PyQt5.QtCore import QRectF, QPointF, Qt, QEvent
from qt_tools import unpickleGfxItemFlags, unpickleRenderHints, SimpleBrush, Pen, setPenColor
from PyQt5.QtGui import QPainter, QTransform, QPen, QBrush, QColor
from geom_tools import paintSelectionShape, rectToPoly, mag2D, closestRectPoint, closestPolyPoint, polygonFromArc
from text_item import TextItem
from gfx_object import GfxObject
from labeled_gfx import LabeledGfx

class GraphNode(GfxObject, LabeledGfx):
    defaultRect = QRectF(-15, -15, 30, 30)
    defaultCornerRadius = 10
    defaultInsetPadding = 10
    Circle, RoundedRect = range(2)
    
    def __init__(self, new=True):
        super().__init__()
        super().__init__()
        self._contextMenu = None
        self._fitContents = True
        self._shape = self.Circle
        if new:
            self._insetPadding = self.defaultInsetPadding
            self._defaultRect = self.defaultRect
            self._cornerRadius = self.defaultCornerRadius
            self.setFlags(self.ItemIsMovable | self.ItemIsFocusable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
            self._renderHints = QPainter.Antialiasing | QPainter.HighQualityAntialiasing | QPainter.SmoothPixmapTransform
            self._arrows = []
            self._boundScale = (1.0, 1.0)
            self._labels = []
            self.setFiltersChildEvents(True)
            self._brush = SimpleBrush(Qt.cyan)
            self._pen = Pen(Qt.yellow, 2.0)
            self.setupConnections()
        self.setAcceptHoverEvents(True)
        self._hover = False

    def hoverEnterEvent(self, event):
        self._hover = True
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self._hover = False
        super().hoverLeaveEvent(event)
        
    def sceneEventFilter(self, watched, event):
        if event.type() == QEvent.GraphicsSceneHoverMove:
            self.updateArrows()
            self.scene().update()
        return False
    
    def cornerRadius(self):
        return self._cornerRadius
    
    def setCornerRadius(self, radius):
        self._cornerRadius = radius
        self.update()
    
    def setupConnections(self):
        self._brushColorDlg = QColorDialog(self.brush().color())
        self._brushColorDlg.setOption(QColorDialog.ShowAlphaChannel, True)
        self._brushColorDlg.currentColorChanged.connect(lambda col: self.setBrush(SimpleBrush(col)))
        self._penColorDlg = QColorDialog(self.pen().color())
        self._penColorDlg.setOption(QColorDialog.ShowAlphaChannel, True)
        self._penColorDlg.currentColorChanged.connect(lambda col: self.setPen(setPenColor(self.pen(), col)))        
      
    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            self.updateArrows()
        return super().itemChange(change, value)    

    def arrows(self):
        return self._arrows
    
    def addArrow(self, arr):
        self._arrows.append(arr)
        
    def removeArrow(self, arr):
        self._arrows.remove(arr)
            
    def boundingRect(self):
        if not self._fitContents:
            return self._defaultRect
        w = self._insetPadding
        rect = self.childrenBoundingRect()
        rect.translate(-rect.center())
        rect.adjust(-w, -w, w, w)
        return rect        
    
    def setDefaultBoundingRect(self, rect=None):
        if rect is None:
            rect = self.defaultRect
        self._defaultRect = rect
        self.update()
        
    def defaultBoundingRect(self):
        return self._defaultRect
        
    def paint(self, painter, option, widget):
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
        if not self._fitContents:
            rect = self.boundingRect()
            radius = max(rect.width(), rect.height())/2
            r = pos - rect.center()
            mag_r = mag2D(r)
            if mag_r == 0:
                return rect.center()
            r /= mag_r
            r *= radius
            return r  
        else:
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
        fit = menu.addAction("Fit Contents")
        fit.triggered.connect(self.setFitContents)
        fit.setCheckable(True)
        fit.setChecked(self._fitContents)
        return menu
    
    def setFitContents(self, fit):
        self._fitContents = fit
        self.scene().update()
        
    def fitContents(self):
        return self._fitContents    
    
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
        