from graph_arrow import GraphArrow
from text_item import TextItem
from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF
from PyQt5.QtWidgets import QMenu, QActionGroup
from PyQt5.QtGui import QPainter, QBrush, QPainterPath, QPainterPathStroker, QPen
from qt_tools import Pen
from geom_tools import mag2D, dot2D, paintSelectionShape
from math import pi

class CategoryArrow(GraphArrow):
    def __init__(self):
        super().__init__()
        label = self.addLabel(TextItem("f"))
        label.setPos(self.pointCenter())
        self._exists = False
        self._epi = False
        self._mono = False
        self._isom = False
        self._firstTimeNonzero = True

    def buildDefaultContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        action = menu.addAction('"There exists"')
        action.toggled.connect(lambda b: self.setExists(b))
        action.setCheckable(True)
        action.setChecked(False)
        menu.addSeparator()
        act = menu.addAction("Monomorphism")
        act.toggled.connect(self.setMonomorphism)
        act.setCheckable(True)
        act = menu.addAction("Epimorphism")
        act.toggled.connect(self.setEpimorphism)
        act.setCheckable(True)
        act = menu.addAction("Isomorphism")
        act.toggled.connect(self.setIsomorphism)
        act.setCheckable(True)
        menu.addSeparator()
        return super().buildDefaultContextMenu(menu)
        
    def setExists(self, exists):
        if exists != self._exists:
            pen = self.pen()
            if exists:
                style = Qt.DotLine
            else:
                style = Qt.SolidLine
            self.setPen(Pen(pen.color(), pen.widthF(), style, pen.capStyle(), pen.joinStyle()))
            self._exists = exists
            self.update()
            
    def exists(self):
        return self._exists
    
    def forall(self):
        return not self._exists
    
    def setIsomorphism(self, isom):
        label = self.findLabel("~")
        if label:
            if isom is False:
                self.removeLabel(label)
                self._isom = False
        else:
            if isom:
                self.addLabel(TextItem("~")).setPos(self.pointCenter())
                self._isom = True
                
    def isIsomorphism(self):
        return self._isom
    
    def setEpimorphism(self, epi):
        if self._epi != epi:
            self._epi = epi
            if self.scene():
                self.scene().update()
            else:
                self.update()
        
    def isEpimorphism(self):
        return self._epi
    
    def setMonomorphism(self, mono):
        if self._mono != mono:
            self._mono = mono
            if self.scene():
                self.scene().update()
            else:
                self.update()
            
    def isMonomorphism(self):
        return self._mono
        
    def type(self):
        return self._type
    
    def paint(self, painter, option, widget):
        if self.isSelected():
            paintSelectionShape(painter, self)
        painter.setRenderHints(QPainter.HighQualityAntialiasing | QPainter.Antialiasing)
        painter.setPen(self.pen())
        painter.setBrush(QBrush(Qt.NoBrush))
        if self._epi:
            self._paintEpiHead(painter)
        else:
            painter.drawPath(self._arrowHead) 
        painter.drawPath(self.tailPath())
            
    def tailPath(self):
        path = QPainterPath()
        path.moveTo(self._points[-1].pos())
        line = self.tailLine()
        u = line.p2() - line.p1()
        v = QPointF(u.y(), -u.x())
        mag_u = mag2D(u)
        if mag_u != 0:
            if self._firstTimeNonzero:
                self._firstTimeNonzero = False
                self.label(0).setPos(self.pointCenter())
            u /= mag_u
            v /= mag_u
        r = self.arrowHeadSize() 
        if self._mono:
            line_end = line.p1() + u * r
        else:
            line_end = line.p1()
        if not self.isBezier():
            path.lineTo(line_end)
        else:
            path.cubicTo(self._points[-2].pos(), self._points[-3].pos(), line_end)
        if self._mono:
            perp_end = 1.5 * r * v
            path.cubicTo(line.p1(), line.p1() + perp_end, line_end + perp_end)
        return path        
    
    def _paintEpiHead(self, painter):
        path = QPainterPath()
        path.moveTo(QPointF(0,0))
        path.addPath(self._arrowHead)
        line = self.headLine()
        u = line.p1() - line.p2()
        mag_u = mag2D(u)
        if mag_u != 0:
            u /= mag_u
        path.addPath(self._arrowHead.translated(u * self.arrowHeadSize()))
        painter.drawPath(path)
        
    def headLine(self):
        if self.isBezier():
            return QLineF(self._points[-2].pos(), self._points[-1].pos())
        return QLineF(self._points[0].pos(), self._points[1].pos())
    
    def tailLine(self):
        return QLineF(self._points[0].pos(), self._points[1].pos())
    
    def shape(self):
        stroker = QPainterPathStroker(QPen(Qt.black, self.arrowHeadSize() * 2))
        return stroker.createStroke(self.tailPath())