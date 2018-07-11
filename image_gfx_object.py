from gfx_object import GfxObject
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import QRectF
from qt_tools import unpicklePixmap, picklePixmap


class ImageGfxObject(GfxObject):
    def __init__(self, pixmap=None):
        super().__init__()
        if isinstance (pixmap, str):
            pixmap = QPixmap.fromImage(QImage(pixmap))
        self._pixmap = pixmap
        self.setFlags(self.ItemIsMovable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
               
    def __setstate__(self, data):
        self.__init__(None, None)
        super().__setstate__(data)
        self._pixmap = unpicklePixmap(data['pixmap'])
        self._name = data['name']
        
    def __getstate__(self):
        data = super().__getstate__()
        data['pixmap'] = picklePixmap(self._pixmap)
        data['name'] = self._name
        return data
    
    def __deepcopy__(self, memo):
        copy = type(self)(None)
        memo[id(self)] = self
        super()._deepcopy(copy, memo)
        copy._pixmap = self._pixmap.copy()
        copy._name = self._name
        return copy
    
    def paint(self, painter, option, widget):
        if self._pixmap:
            super().paint(painter, option, widget)
            painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)
            w = self._pixmap.width()
            h = self._pixmap.height()
            painter.drawPixmap(-w/2, -h/2, self._pixmap)
        
    def boundingRect(self):
        if self._pixmap:
            w = self._pixmap.width()
            h = self._pixmap.height()
            return QRectF(-w/2, -h/2, w, h).adjusted(-5, -5, 5, 5)
        return QRectF()
    
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()