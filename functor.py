from category_arrow import CategoryArrow
from category_diagram import CategoryDiagram
from PyQt5.QtWidgets import QGraphicsSceneHoverEvent, QMenu
from commands import MethodCallCommand, TakeFunctorImage
from category_object import CategoryObject
from copy import deepcopy

class Functor(CategoryArrow):
    def __init__(self, new=True):
        self._reflectGfx = True
        super().__init__(new)
        if new:
            self._map = {}
            self._signalsSlots = {}      # Keyed by uid
        self._memo = {}
        self._contra = False    # covariance / contravariance
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._map = deepcopy(self._map, memo)
        copy._reflectForward = self._reflectForward
        copy._reflectInverse = self._reflectInverse
        copy._contra = self._contra
        
    def takeImage(self, dom=None, cod=None, contra=False):
        if dom is None:
            dom = self.domain()
        if cod is None:
            cod = self.codomain()
        if dom and cod and dom.nonempty():
            getText = lambda: "Take the functor image " + self.imageString(dom) + "."
            command = TakeFunctorImage(getText(), dom, cod, functor=self, editor=self.editor(), contra=contra)
            self.editor().pushCommand(command)
            self.symbolChanged.connect, lambda symbol: command.setText(getText())
            self.domain().symbolChanged.connect(lambda symbol: command.setText(getText()))
    
    def connectSignal(self, uid_hash, signal, slots):
        if uid_hash not in self._signalsSlots:
            self._signalsSlots[uid_hash] = []
        self._signalsSlots[uid_hash].append((signal, slots))
        for slot in slots:
            signal.connect(slot)
            
    def disconnectSignals(self, uid_hash):
        if uid_hash in self._signalsSlots:
            tuple_list = self._signalsSlots[uid_hash]
            for signal, slots in tuple_list:
                for slot in slots:
                    signal.disconnect(slot)
            del self._signalsSlots[uid_hash]
            
    def disconnectRemainingSignals(self):
        for uid_hash in self._signalsSlots:
            self.disconnectSignals(uid_hash)
        self._signalsSlots.clear()
    
    def connectObjectToItsImage(self, x, y):
        F = self
        hash = self.uidPairHash(x, y)
        self.connectSignal(hash, self.symbolChanged, [lambda sym: y.setSymbol(F.imageString(x))])
        self.connectSignal(hash, x.symbolChanged, [lambda sym: y.setSymbol(F.imageString(x))])
        self.connectSignal(hash, x.deleted, [lambda o: y.delete(), self.deleteMapping])
        self.connectSignal(hash, x.positionChangedDelta, [lambda delta: self._reflectItemPosDelta(y, delta)])
        y.setEditable(False)
                
    def disconnectObjectFromItsImage(self, x, y):
        if x and y:
            hash = self.uidPairHash(x, y)
            self.disconnectSignals(hash)
        
    def _reflectItemPosDelta(self, item, delta):
        if self._reflectGfx:
            item.setPos(item.pos() + delta)
               
    def deleteMapping(self, item):
        del self._map[item.uid()]
        
    def connectMorphismToItsImage(self, f, g):
        F = self;  C = F.domain();  D = F.codomain()
        hash = self.uidPairHash(f, g)
        self.connectSignal(hash, self.symbolChanged, [lambda sym: g.setSymbol(F.imageString(f))])
        self.connectSignal(hash, f.symbolChanged, [lambda sym: g.setSymbol(F.imageString(f))])
        self.connectSignal(hash, f.deleted, [lambda a: g.delete(), self.deleteMapping])
        if self._contra:
            self.connectSignal(hash, f.domainSet, [lambda dom: self._reflectCodomainSet(g, dom)])
            self.connectSignal(hash, f.codomainSet, [lambda cod: self._reflectDomainSet(g, cod)])
        else:
            self.connectSignal(hash, f.domainSet, [lambda dom: self._reflectDomainSet(g, dom)])
            self.connectSignal(hash, f.codomainSet, [lambda cod: self._reflectCodomainSet(g, cod)])
        self.connectSignal(hash, f.bezierToggled, [lambda b: self._reflectToggleBezier(g, b)])
        self.connectSignal(hash, f.controlPointsPosChanged, [lambda pos_list: self._reflectControlPointPos(g, pos_list)])
        g.setEditable(False)      
        
    def disconnectMorphismFromItsImage(self, f, g):
        if f and g:
            hash = self.uidPairHash(f, g)
            self.disconnectSignals(hash)
        
    def _reflectDomainSet(self, arr, dom):
        F = self;  C = self.domain();  D = self.codomain()
        if dom and D:
            d = D.getObject(F[dom.uid()])
            if d:
                arr.setDomain(d)
        else:
            arr.setDomain(None)
            
    def _reflectCodomainSet(self, arr, cod):
        F = self;  C = self.domain();  D = self.codomain()
        if cod and D:
            d = D.getObject(F[cod.uid()])
            if d:
                arr.setCodomain(d)  
        else:
            arr.setCodomain(None)
    
    def _reflectToggleBezier(self, arr, toggle):
        if self._reflectGfx:
            arr.toggleBezier(toggle)
            
    def _reflectControlPointPos(self, arr, pos_list):
        if self._reflectGfx:
            if len(pos_list) == 4:
                if not arr.isBezier():
                    arr.toggleBezier(True)
            elif len(pos_list) == 2:
                if arr.isBezier():
                    arr.toggleBezier(False)
            else:
                raise NotImplementedError
            arr.setPointPositions(pos_list)
    
    def deleteMapping(self, item):
        if isinstance(item, str):
            if item in self._map:
                del self._map[item]
        elif item.uid() in self._map:
            del self._map[item.uid()]
    
    def undoTakeImage(self, dom=None, cod=None):
        if dom is None:
            dom = self.domain()
        if cod is None:
            cod = self.codomain()
        if dom and cod and cod.nonempty():
            getText = lambda: "Undo taking the functor image " + self.imageString(dom)
            command = TakeFunctorImage(getText(), dom, cod, functor=self, editor=self.editor(), swap=True, contra=self.isContravariant())
            self.editor().pushCommand(command)
            self.symbolChanged.connect(lambda sym: command.setText(getText()))
            self.domain().symbolChanged.connect(lambda sym: command.setText(getText()))
                                
    def updateImage(self, undoable=False):
        if self.domain().nonempty():
            if undoable:
                getText = lambda: "Update functor image " + self.imageString(self.domain()) + " of diagram."
                command = TakeFunctorImage(getText(), self.domain(), self.codomain(), functor=self, editor=self.editor(), contra=self.isContravariant())
                self.symbolChanged.connect(lambda sym: command.setText(getText()))
                self.domain().symbolChanged.connect(lambda sym: command.setText(getText()))
                self.editor().pushCommand(command)
            else:
                if self.domain() and self.codomain():
                    command = TakeFunctorImage("dummy", self.domain(), self.codomain(), functor=self, editor=self.editor(), contra=self.isContravariant())
                    command.redo()
                            
    def _setCodomain(self, cod, undoable=False):
        assert(cod is None or isinstance(cod, CategoryDiagram))
        if cod is not self.codomain():
            if cod is not None:
                if undoable:
                    self.takeImage(cod=cod)
            else:
                if undoable:
                    self.undoTakeImage(cod=cod)    
            super()._setCodomain(cod, undoable)    
            
    def _setDomain(self, dom, undoable=False):
        assert(dom is None or isinstance(dom, CategoryDiagram))
        if dom is not self.domain():
            if dom is not None:
                if undoable:
                    self.takeImage()
            else:
                if undoable:
                    self.undoTakeImage()
            super()._setDomain(dom, undoable)
        
    def isFullyAttachedFunctor(self):
        return isinstance(self.codomain(), CategoryDiagram) and isinstance(self.domain(), CategoryDiagram)
        
    def __contains__(self, uid):
        return uid in self._map
    
    def __getitem__(self, preimage):
        return self._map.get(preimage, None)
    
    def __setitem__(self, preimage, image):
        self._map[preimage] = image
        return image
    
    def mapping(self):
        return self._map
    
    def clearMapping(self):
        self._map.clear()
        self._memo.clear()
        self.disconnectRemainingSignals()
        
    def setMapping(self, mapping):
        self._map = mapping
        
    def updateMapping(self, mapping):
        self._map.update(mapping)
    
    def __call__(self, *args):
        memo = self._memo
        if len(args) == 1:
            x = args[0]
            if isinstance(x, CategoryObject):
                y = deepcopy(x, memo)
                y.setSymbol(self.imageString(x))
                y.setEditable(False)
                res = y
            elif isinstance(x, CategoryArrow):
                f = x
                g = deepcopy(f, memo)        # Deepcopy memoization fixes many bugs
                g.setSymbol(self.imageString(f))
                g.setEditable(False)
                g.setReversed(self.isContravariant())
                res = g
            else:
                raise NotImplementedError
            return res
        else:
            raise NotImplementedError
        
    def imageString(self, f):
        f = str(f)
        fun_name = str(self)
        if '.' not in fun_name:
            res =  str(self) + "(" + f + ")"
        else:
            i = fun_name.index('.')   # Take first, ignore the rest
            res = fun_name[:i] + x + fun_name[i+1:] 
        return res
    
    def buildDefaultContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        super().buildDefaultContextMenu(menu)
        menu.addSeparator()
        act = menu.addAction("Contravariant")
        act.setCheckable(True)
        act.setChecked(self._contra)
        act.toggled.connect(lambda tog: self.setContravariant(tog, undoable=True))
        menu.addSeparator()
        act = menu.addAction("Reflect Graphics")
        act.setCheckable(True)
        act.setChecked(self._reflectGfx)
        act.toggled.connect(self.setReflectGraphics)
        return menu
        
    def setReflectGraphics(self, reflect):
        self._reflectGfx = reflect
        
    def isContravariant(self):
        return self._contra
    
    def setContravariant(self, contra, undoable=False):
        if contra != self._contra:
            if undoable:
                if contra:
                    word = "contravariant"
                    logic = True
                else:
                    word = "covariant"
                    logic = False
                getText = lambda: "Let functor " + str(self) + " be " + word + "."
                command = MethodCallCommand(getText(), self.setContravariant, [logic], self.setContravariant, [not logic], self.editor())
                self.symbolChanged.connect(lambda sym: command.setText(getText()))
                self.domain().symbolChanged.connect(lambda sym: command.setText(getText()))
                self.editor().pushCommand(command)
            else:
                if self.codomain():
                    revMap = { val : key for key, val in self._map.items() }
                    for g in self.codomain().morphisms().values():
                        g.setReversed(contra)
                self._contra = contra
                            