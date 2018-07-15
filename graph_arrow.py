from PyQt5.QtCore import pyqtSignal, Qt, QRectF, QLineF, QPointF, QTimer
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsSceneMouseEvent, QMenu, QAction
from PyQt5.QtGui import QBrush, QPainter, QPainterPath, QPolygonF, QPainterPathStroker
from geom_tools import mag2D, dot2D, rectToPoly, paintSelectionShape
from math import acos, asin, atan2, pi, sin, cos
from gfx_object import GfxObject
from labeled_gfx import LabeledGfx
from text_item import TextItem
from control_point import ControlPoint
from qt_tools import Pen
from copy import deepcopy

class GraphArrow(GfxObject, LabeledGfx):
    EditTime = 1500
    nameChanged = pyqtSignal(str)
    bezierToggled = pyqtSignal(bool)
    controlPointsPosChanged = pyqtSignal(list)    # list of points
    
    def __init__(self, new=True):
        super().__init__()
        super().__init__()
        if new:
            self._to = None
            self._from = None            
            self._points = [ControlPoint() for i in range(0, 2)]
            for point in self._points:
                point.setPos(QPointF(0,0))
            self.setupConnections()
            self._pen = Pen(Qt.black, 1.5, Qt.SolidLine)
            self._textPos = []
        self._arrowHead = None            
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemIsMovable, False)
        self.setFlag(self.ItemIsSelectable, True)
        self.setFlag(self.ItemIsFocusable, False)
        self.setFlag(self.ItemSendsGeometryChanges, True)
        self._contextMenu = None
        self._editTimer = None
        self._updatingPos = False
        self._snapToGrid = False
        
    def __setstate__(self, data):
        super().__setstate__(data)
        super().__setstate__(data)
        self._points = data["points"]
        self._to = data["to"]
        self._from = data["from"]
        self._textPos = data["text pos"]
        self.updatePosition()
        self.update()
        
    def __getstate__(self):
        data = super().__getstate__()
        data = {**data, **super().__getstate__()}
        data["points"] = self._points
        data["to"] = self._to
        data["from"] = self._from
        data["text pos"] = self._textPos
        return data
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._points = deepcopy(self._points, memo)
        for point in copy._points:
            point.setParentItem(self)
        copy._to = None
        copy._from = None
        copy._to = deepcopy(self._to, memo)
        copy._from = deepcopy(self._from, memo)
        copy._pen = deepcopy(self._pen, memo)
        copy._textPos = [None for text_pos in self._textPos]
        self.copyLabelsTo(copy)
        copy.setupConnections()
        copy.updateArrowHead()
        return copy

    def controlPointPosAboutToChange(self, ctrl_pt, crnt_pos):
        self.saveTextPosition()
        
    def controlPointPosHasChanged(self, ctrl_pt, new_pos):
        self.updateTextPosition()
        self.updatePosition()
        self.update()
        self.controlPointsPosChanged.emit([p.pos() for p in self._points])
        
    def pen(self):
        return self._pen
        
    def hoverEnterEvent(self, event):
        self.hoverEnterSlot()
        
    def hoverEnterSlot(self):
        if self._editTimer:
            self._editTimer.stop()
        for point in self._points:
            point.setVisible(True)
            
    def hoverLeaveEvent(self, event):
        self.hoverLeaveSlot()
        
    def hoverLeaveSlot(self):
        if self._editTimer:
            self._editTimer.stop()
        self._editTimer = QTimer()
        self._editTimer.setSingleShot(False)
        self._editTimer.timeout.connect(self._hoverLeaveEvent)
        self._editTimer.setInterval(self.EditTime)
        self._editTimer.start()
        
    def _hoverLeaveEvent(self):
        for point in self._points:
            if point.isSelected():
                return
        for point in self._points:
            point.setVisible(False)  
        self._editTimer.stop()
        self._editTimer = None
            
    def setupConnections(self):
        self._points[0].positionAboutToChange.connect(lambda pos: self.controlPointPosAboutToChange(self._points[0], pos))
        self._points[-1].positionAboutToChange.connect(lambda pos: self.controlPointPosAboutToChange(self._points[-1], pos))
        self._points[0].positionHasChanged.connect(lambda pos: self.controlPointPosHasChanged(self._points[0], pos))
        self._points[-1].positionHasChanged.connect(lambda pos: self.controlPointPosHasChanged(self._points[-1], pos))            
        for point in self._points:
            point.setParentItem(self)
        if len(self._points) == 4:
            self._points[1].positionHasChanged.connect(lambda pos: self.controlPointPosHasChanged(self._points[1], pos))         
            self._points[2].positionHasChanged.connect(lambda pos: self.controlPointPosHasChanged(self._points[2], pos))
        #self._contextMenu = self.buildDefaultContextMenu()
  
    def source(self):
        if self._from is None:
            return self.fromPoint()
        return self._from
    
    def dest(self):
        if self._to is None:
            return self.toPoint()
        return self._to
    
    def target(self):
        return self.dest()
        
    def setTo(self, to):
        if to != self._to:
            if self._to is not None:
                self._to.detachArrow(self)
            self._to = to
            if to is not None:
                to.attachArrow(self)
            self.updatePosition()
            
    def setFrom(self, fro):
        if fro != self._from:
            if self._from is not None:
                self._from.detachArrow(self)
            self._from = fro         
            if fro is not None:
                fro.attachArrow(self)
            self.updatePosition()
        
    def fromNode(self):
        return self._from
    
    def toNode(self):
        return self._to    
        
    def toPoint(self):
        return self._points[-1]
    
    def fromPoint(self):
        return self._points[0]
    
    def boundingRect(self):
        #TODO: try removing "adjusted part"
        return self.childrenBoundingRect().adjusted(-20, -20, 20, 20)
    
    def paint(self, painter, option, widget):
        if self.isSelected():
            paintSelectionShape(painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen())
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawPath(self._arrowHead)        
        bezier_path = QPainterPath()
        bezier_path.moveTo(self._points[0].pos())
        if not self.isBezier():
            bezier_path.lineTo(self._points[-1].pos())
        else:
            bezier_path.cubicTo(self._points[1].pos(), self._points[2].pos(), self._points[3].pos())
        painter.drawPath(bezier_path)

    def isBezier(self):
        return len(self._points) == 4

    def setLine(self, line):
        self._points[0].setPos(line.p1())
        self._points[-1].setPos(line.p2())
        self.updateArrowHead()
        self.update()
        
    def updateArrowHead(self):
        if not self.isBezier():
            u = self.line().p2() - self.line().p1()
        else:
            u = self._points[-1].pos() - self._points[-2].pos()
        mag_u = mag2D(u)
        if mag_u == 0.0:
            self._arrowHead = QPainterPath()
            return
        u /= mag_u
        v = QPointF(-u.y(), u.x())      # perp vector
        path = QPainterPath()
        tip = self.line().p2()
        size = self.arrowHeadSize()
        p = tip - (u + v) * size
        q = tip + (v - u) * size
        r = tip - u * size
        path.moveTo(p)
        path.quadTo((p + tip + r) / 3, tip)
        path.quadTo((q + tip + r)/3, q)
        self._arrowHead = path        
        
    def setLinePoints(self, pos0, pos1):
        u = pos1 - pos0
        mag_u = mag2D(u)
        if mag_u == 0.0:
            for k in range(0, len(self._points)):
                self._points[k].setPos(pos0)
            return
        u /= mag_u
        u *= mag_u / (len(self._points) - 1)
        for k in range(0, len(self._points)):
            self._points[k].setPos(pos0 + k*u)
        self.updateArrowHead()
        self.update()
    
    def contextMenuEvent(self, event):
        if self._contextMenu:
            self._contextMenu.exec_(event.screenPos())
        
    def buildDefaultContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        self._bezierAct = menu.addAction("Bezier")
        self._bezierAct.setCheckable(True)
        self._bezierAct.setChecked(False)
        self._bezierAct.toggled.connect(self.toggleBezier)
        return menu
        
    def toggleBezier(self, toggled):
        if toggled != self.isBezier():
            if toggled:
                for k in range(0, 2):
                    ctrl_pt = ControlPoint()
                    ctrl_pt.setParentItem(self)
                    self._points.insert(1, ctrl_pt)
                    ctrl_pt.positionHasChanged.connect(lambda pos: self.controlPointPosHasChanged(ctrl_pt, pos))         
            else:
                point = self._points.pop(1)
                self.scene().removeItem(point)
                point.setParentItem(None)
                point = self._points.pop(1)
                self.scene().removeItem(point)
                point.setParentItem(None)
                self.updatePosition()
            self.setLinePoints(self._points[0].pos(), self._points[-1].pos())
            self.bezierToggled.emit(toggled)
    
    def arrowHeadSize(self):
        return 15
    
    def shape(self):
        if len(self._points) == 2:
            path = QPainterPath()
            u = self.line().p2() - self.line().p1()
            u /= mag2D(u)
            v = QPointF(-u.y(), u.x())      # perp vector        
            v *= self.arrowHeadSize()
            p1 = self.line().p1()
            p2 = self.line().p2()
            size = self.arrowHeadSize()
            poly = QPolygonF([p1 + v, p1 - v, p2 - v, p2 + v, p1 + v])
            path.addPolygon(poly)            
            return path    
        else:
            path = QPainterPath()
            path.moveTo(self._points[0].pos())
            path.cubicTo(self._points[1].pos(), self._points[2].pos(), self._points[3].pos())
            stroker = QPainterPathStroker(QPen(Qt.black, self.arrowHeadSize() * 2))
            return stroker.createStroke(path)
    
    def line(self):
        return QLineF(self._points[0].pos(), self._points[-1].pos())
    
    def updatePosition(self, force=False):
        #if self.toNode() is None and self.fromNode() is None:
            #if not force:
                #self.updateArrowHead()
                #self.updateTextPosition()                
                #return
        if self.dest() and self.source():
            self._updatingPos = True
            #self.saveTextPosition()
            self.prepareGeometryChange()
            if len(self._points) == 2:
                a = self.source().closestBoundaryPosToItem(self.dest())
                b = self.dest().closestBoundaryPosToItem(self.source())
                a = self.mapFromItem(self.source(), a)
                b = self.mapFromItem(self.dest(), b)        
            else:
                a = self.source().closestBoundaryPosToItem(self._points[1])
                b = self.dest().closestBoundaryPosToItem(self._points[-2])
                a = self.mapFromItem(self.source(), a)
                b = self.mapFromItem(self.dest(), b)
            line = QLineF(a, b)
            length = line.length()
            # BUGFIX
            if abs(length) == 0:
                line = QLineF(a, QPointF(a.x() + 1, a.y()))
                length = 1
            dx = line.dx()
            dx /= length
            if dx > 1:
                dx = 1
            elif dx < -1:
                dx = -1
            angle = acos(dx)
            size = self.arrowHeadSize()
            head = self._arrowHead
            if line.dy() >= 0:
                angle = pi*2 - angle
            p2 = line.p2()
            u = p2 + QPointF(sin(angle + pi + pi/3) * size, cos(angle + pi + pi/3) * size)
            v = p2 + QPointF(sin(angle - pi/3) * size, cos(angle - pi/3) * size)
            if self.dest() != self.toPoint():
                self.toPoint().setPos(line.p2()) 
            if self.source() != self.fromPoint():
                self.fromPoint().setPos(line.p1())          
            self.updateArrowHead()
            #self.updateTextPosition()
            self._updatingPos = False
        else:
            self.updateArrowHead()
            self.updateTextPosition()
                   
    def saveTextPosition(self, k=None):
        line = self.line()
        u = line.p2() - line.p1()
        mag_u = mag2D(u)
        if mag_u != 0:
            u /= mag_u
        v = QPointF(-u.y(), u.x())
        if k is not None:
            label = self._labels[k]
            a = label.pos() - line.p1()
            self._textPos[k] = (dot2D(a, u), dot2D(a, v), mag_u)
        else:
            for k in range(len(self._labels)):
                label = self._labels[k]
                a = label.pos() - line.p1()
                a_proj_u = dot2D(a, u) 
                a_proj_v = dot2D(a, v)
                self._textPos[k] = (a_proj_u, a_proj_v, mag_u)
                
    def updateTextPosition(self):
        line = self.line()
        u = line.p2() - line.p1()
        mag_u1 = mag2D(u)
        u /= mag_u1
        v = QPointF(-u.y(), u.x())
        for k in range(len(self._labels)):
            pos = self._textPos[k]
            label = self._labels[k]
            a_proj_u = pos[0]
            a_proj_v = pos[1]
            mag_u = pos[2]
            if mag_u == 0.0:
                f = 1.0
            else:
                f = mag_u1 / mag_u            
            a_proj_u *= f
            v_a = v * a_proj_v
            u_a = u * a_proj_u
            a = line.p1() + u_a + v_a
            label.setPos(a)
        self.saveTextPosition()      
        
    def controlPoints(self):
        return self._points
    
    def isUpdatingPosition(self):
        return self._updatingPos
    
    def setContextMenu(self, menu):
        self._contextMenu = menu
        
    def addLabel(self, label):
        k = self.labelCount()
        label = super().addLabel(label)
        if isinstance(label, TextItem):
            label.onPositionChanged = lambda: self.saveTextPosition(k)
        return label
        
    def mouseMoveEvent(self, event):
        if self.flags() & self.ItemIsMovable:
            delta = event.lastScenePos() - event.scenePos()
            self.setPos(self.pos() + delta)
    
    def isEndControlPoint(self, ctrl_pt):
        points = self.controlPoints()
        if points[-1] is ctrl_pt or points[0] is ctrl_pt:
            return True
        return False
    
    def setNodeAtControlPoint(self, node, ctrl_pt):
        if ctrl_pt is self._points[0]:
            self.setFrom(node)
        elif ctrl_pt is self._points[-1]:
            self.setTo(node)
            
    def pointCenter(self):
        center = QPointF()
        for point in self._points:
            center += point.pos()
        center /= len(self._points)
        return center
            
    def itemChange(self, change, value):
        if change == self.ItemSelectedChange:
            if value == True:
                for point in self._points:
                    point.setVisible(True)
                    point.setSelected(True)
        elif change == self.ItemPositionChange:
            center = self.pointCenter()
            delta = value - center
            for point in self._points:
                point.setPos(point.pos() + delta)
            value = QPointF()
            return super().itemChange(change, value)
        return super().itemChange(change, value)            
    
    def updateGraph(self):
        self.updatePosition()
        
    def setPointPositions(self, pos_list):
        if isinstance(pos_list[0], ControlPoint):
            pos_list = [p.pos() for p in pos_list]
        for k in range(0, len(pos_list)):
            self._points[k].setPos(pos_list[k])
        
    #def setPos(self, pos):
        #center = self.pointCenter()
        #delta = pos - center
        #for point in self._points:
            #point.setPos(point.pos() + delta)
        #self.updatePosition()
        
    def delete(self):
        self.setTo(None)
        self.setFrom(None)
        super().delete()