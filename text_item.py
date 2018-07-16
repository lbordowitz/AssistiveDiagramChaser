from PyQt5.QtWidgets import QGraphicsTextItem, QUndoStack, QUndoCommand, QGraphicsItem, QGraphicsSceneMouseEvent
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QEvent, QRectF, QTimer
from PyQt5.QtGui import QColor, QTextCursor, QPainter, QFontMetrics
from qt_tools import PseudoSignal, Pen, unpickleGfxItemFlags
from copy import deepcopy
from uuid import uuid4

class KeyPressedSignal(PseudoSignal):
    signal = pyqtSignal()

class TextItem(QGraphicsTextItem):
    DispatchSignalDelay = 50    # milliseconds
    
    def __init__(self, text=None, new=True):
        super().__init__(text)
        if new:
            self._editable = None
            self._editableColor = QColor(255, 255, 0, 240)
            self._colorSave = None
            self.setEditable(False)
            self.setupConnections()
        self.setDefaultTextColor(QColor(Qt.darkMagenta))
        self.onTextChanged = []
        self.setFlags(self.ItemIsMovable | self.ItemIsFocusable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
        self.pressedEventHandler = None
        self.onPositionChanged = None
        self._uid = uuid4()        
        self._dispatchTimer = None        
        
    def setupConnections(self):
        self.keyPressed = KeyPressedSignal()
        self.keyPressed.connect(self.dispatchOnTextChanged)
        self.mouseDoubleClickHandler = lambda event: self.setTextInteraction(True, select_all=True)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        # HACKFIX: gets rid of single-click selection rect around text when it first appears.  Now only shows selection rect when double-clicked:
        self.setTextInteraction(True)
        self.setTextInteraction(False)        
        
    def dispatchOnTextChanged(self):
        if self._dispatchTimer:
            self._dispatchTimer.stop()
        self._dispatchTimer = QTimer()
        self._dispatchTimer.setInterval(self.DispatchSignalDelay)
        self._dispatchTimer.timeout.connect(self._dispatchOnTextChanged)
        self._dispatchTimer.setSingleShot(True)
        self._dispatchTimer.start()
        
    def _dispatchOnTextChanged(self):
        text = self.toPlainText()
        for slot in self.onTextChanged:
            slot(text)
        
    def uid(self):
        return self._uid
        
    def __setstate__(self, data):
        self.__init__(data['text'])
        self.setFlags(unpickleGfxItemFlags(data['flags']))
        self.setDefaultTextColor(data['color'])
        self._undoStack = data['undo stack']
        self.setPos(data['pos'])
        
    def __getstate__(self):
        return {
            'text' : self.toPlainText(),
            'flags' : int(self.flags()),
            'color' : self.defaultTextColor(),
            'undo stack' : self._undoStack,
            'pos' : self.pos(),
        }
    
    def __deepcopy__(self, memo):
        copy = type(self)(new=False)
        copy._editable = self._editable
        copy._editableColor = QColor(self._editableColor)
        copy._colorSave = QColor(self._colorSave)
        copy.setPlainText(self.toPlainText())
        memo[id(self)] = copy
        copy.setFlags(self.flags())
        copy.setDefaultTextColor(self.defaultTextColor())
        copy._undoStack = None              # Can't copy an undo stack since it holds references to this item and will change /it/
        copy.setPos(self.pos())
        copy.setupConnections()
        return copy
    
    def keyPressEvent(self, event):
        self.keyPressed.emit()
        super().keyPressEvent(event)
                
    def setUndoStack(self):
        return self._undoStack
                    
    def focusOutEvent(self, event):
        #self.setTextInteraction(False)
        super().focusOutEvent(event)            
    
    def setPlainText(self, text):
        if self.toPlainText() != text:
            super().setPlainText(text)
            if self.onTextChanged:
                for slot in self.onTextChanged:
                    slot(text)
                      
    def setTextInteraction(self, state, select_all=True):
        text = self.toPlainText()
        if self.editable() and state and self.textInteractionFlags() == Qt.NoTextInteraction:
            # switch on editor mode:
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            # manually do what a mouse click would do else:
            self.setFocus(Qt.MouseFocusReason)  # give the item keyboard focus
            self.setSelected(True)  # ensure itemChange() gets called when we click out of the item
            if select_all:  # option to select the whole text (e.g. after creation of the TextItem)
                c = self.textCursor()
                c.select(QTextCursor.WordUnderCursor)
                self.setTextCursor(c)
        elif not state and self.textInteractionFlags() == Qt.TextEditorInteraction:
            # turn off editor mode:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            # deselect text (else it keeps gray shade):
            c = self.textCursor()
            c.clearSelection()
            self.setTextCursor(c)
            self.clearFocus()
            
    def mouseDoubleClickEvent(self, event):
        if self.mouseDoubleClickHandler:
            self.mouseDoubleClickHandler(event)
        else:
            super().mouseDoubleClickEvent(event)
            
    def mousePressEvent(self, event):
        if self.pressedEventHandler:
            self.pressedEventHandler(event)
        super().mousePressEvent(event)
            
    def itemChange(self, change, value):
        if change == self.ItemSelectedChange:
            if self.textInteractionFlags() != Qt.NoTextInteraction and not value:
                # item received SelectedChange event AND is in editor mode AND is about to be deselected
                self.setTextInteraction(False)  # leave editor mode
        elif change == self.ItemPositionChange:
            if self.onPositionChanged:
                self.onPositionChanged()
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget):
        painter.setRenderHints(QPainter.HighQualityAntialiasing | QPainter.Antialiasing | QPainter.TextAntialiasing)
        super().paint(painter, option, widget)
        
    def setSelected(self, selected):
        super().setSelected(selected)
        if selected:
            if self.parentItem():
                self.parentItem().setSelected(False)
                
    def delete(self, deleted=None):
        if deleted is None:
            deleted = {}
        deleted["parent"] = self.parentItem()
        deleted["scene"] = self.scene()
        self.setParentItem(None)
        if self.scene():
            self.scene().removeItem(self)
        return deleted        
            
    def undelete(self, deleted):
        self.setParentItem(deleted["parent"])
        if deleted["scene"]:
            deleted["scene"].addItem(self)
            
    def setEditable(self, editable):
        if self._editable != editable:
            self._editable = editable
            if editable:
                self._colorSave = self.color()
                self.setColor(self._editableColor)
            else:
                if self._colorSave:
                    self.setColor(self._colorSave)
                self._colorSave = None
            self.update()
            
    def setEditableColor(self, color):
        self._editableColor = color
        self.update()
            
    def editable(self):
        return self._editable            
    
    def setColor(self, color):
        self.setDefaultTextColor(color)
        
    def color(self):
        return self.defaultTextColor()