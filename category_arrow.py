from graph_arrow import GraphArrow
from text_item import TextItem
from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF, QEvent, pyqtSignal
from PyQt5.QtWidgets import QMenu, QActionGroup
from PyQt5.QtGui import QPainter, QBrush, QPainterPath, QPainterPathStroker
from qt_tools import Pen
from geom_tools import mag2D, dot2D, paintSelectionShape
from math import pi
from diagram import Diagram
from copy import deepcopy
import re
from commands import MethodCallCommand
import category_object

class CategoryArrow(GraphArrow):
    domainSet = pyqtSignal(category_object.CategoryObject)
    codomainSet = pyqtSignal(category_object.CategoryObject)
    
    def __init__(self, new=True):
        super().__init__(new)
        if new:
            label = self.addLabel(TextItem("f"))
            self._exists = False
            self._epi = False
            self._mono = False
            self._isom = False
            self._editor = None
        self._graphAlgoVisited = False
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._exists = self._exists
        copy._epi = self._epi
        copy._mono = self._mono
        copy._isom = self._isom
        copy._editor = self._editor
        return copy
    
    def editor(self):
        return self._editor
    
    def setEditor(self, editor):
        self._editor = editor
        
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
        if isom != self._isom:
            labels = self.findLabels("~")
            if labels:
                if isom is False:
                    for label in labels:
                        self.removeLabel(label)
                    self._isom = False
            else:
                if isom:
                    if self.findLabel("~") is None:
                        self.addLabel(TextItem("~"))
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
        if self.scene():
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
        if abs(mag_u) != 0:
            if self._firstTimeNonzero:
                self._firstTimeNonzero = False
                label = self.label(-1)
                if label:
                    label.setPos(self.pointCenter())
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
        stroker = QPainterPathStroker(Pen(Qt.black, self.arrowHeadSize() * 2))
        return stroker.createStroke(self.tailPath())
    
    def addLabel(self, label):
        self._firstTimeNonzero = True
        label = super().addLabel(label)
        label.setPos(self.pointCenter())
        label.setParentItem(self)
        return label
    
    def arrowHeadSize(self):
        return 7
            
    def graphAlgoVisited(self):
        return self._graphAlgoVisited
    
    def clearGraphAlgoVisitedFlag(self):
        self._graphAlgoVisited = False
        
    def setGraphAlgoVisitedFlag(self):
        self._graphAlgoVisited = True
        
    def functorCompositionRegex(self):
        fun = self.labelText(0)
        return re.compile(fun + r'\((?P<arg>.+)\)')
    
    def setTo(self, cod, undoable=False):
        if cod is not self.codomain():
            if undoable:
                getText = lambda: "Set codomain of " + str(self) + " to " + str(cod)
                command = MethodCallCommand(getText(), self.setTo, [cod], self.setTo, [self.domain()], self.editor())
                slot = lambda name: command.setText(getText())
                self.nameChanged.connect(slot)
                if cod is not None:
                    cod.nameChanged.connect(slot)
                self.editor().pushCommand(command)
            else:
                super().setTo(cod)
            self.codomainSet.emit(cod)
        
    def setFrom(self, dom, undoable=False):
        if dom is not self.domain():
            if undoable:
                getText = lambda: "Set domain of " + str(self) + " to " + str(dom)
                command = MethodCallCommand(getText(), self.setFrom, [dom], self.setFrom, [self.codomain()], self.editor())
                slot = lambda name: command.setText(getText())
                self.nameChanged.connect(slot)
                if dom is not None:
                    dom.nameChanged.connect(slot)
                self.editor().pushCommand(command)
            else:
                super().setFrom(dom)
            self.domainSet.emit(dom)
                
    def domain(self):
        return self.fromNode()
    
    def codomain(self):
        return self.toNode()
        
    def canConnectTo(self, item, at_start):
        if at_start:
            other_end = self.codomain()
        else:
            other_end = self.domain()
        if isinstance(other_end, category_object.CategoryObject) and \
           other_end.parentItem() is item.parentItem() and \
           isinstance(item, category_object.CategoryObject):
            return True
        elif other_end is None:
            return True
        return False
            
    def codomain(self):
        return self.toNode()
    
    def domain(self):
        return self.fromNode()
    
    def setDomain(self, dom):
        self.setFrom(dom)
                
    def setCodomain(self, cod):
        self.setTo(cod)