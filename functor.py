from category_arrow import CategoryArrow
from diagram import Diagram
from PyQt5.QtWidgets import QGraphicsSceneHoverEvent, QMenu
from commands import MethodCallCommand
from category_object import CategoryObject
from copy import deepcopy

class Functor(CategoryArrow):
    def __init__(self, new=True):
        self._reflectGfx = True
        super().__init__(new)
        if new:
            self._map = {}
        self._memo = {}
        
    def __deepcopy__(self, memo):
        copy = deepcopy(super(), memo)
        memo[id(self)] = copy
        copy._map = deepcopy(self._map, memo)
        copy._reflectForward = self._reflectForward
        copy._reflectInverse = self._reflectInverse
        
    def takeImage(self, map=None, memo=None, undoable=False):
        if self.isFullyAttachedFunctor() and self.domain().nonempty():
            if map is not None:
                self._map = map
            if memo is not None:
                self._memo = memo                  
            if undoable:
                getText = lambda: "Take functor image " + self(str(self.domain()))
                command = MethodCallCommand(getText(), self.takeImage, [], self.undoTakeImage, [], self.editor())
                self.editor().pushCommand(command)
                self.nameChanged.connect(lambda name: command.setText(getText()))
                self.domain().nameChanged.connect(lambda name: command.setTExt(getText()))
            else:            
                G = self
                C = G.domain()
                D = G.codomain()
                for x in list(C.objects().values()):    # So we can add to objects() during iteration  (endofunctors)
                    if x.uid() not in G:
                        y = G(x)
                        G[x.uid()] = y.uid()
                        D.addObject(y, loops=0)
                        x.nameChanged.connect(lambda name: y.setName(G(name)))
                        self.connectObjectToItsImage(x, y)
                        for f in list(x.outgoingArrows()):
                            if f.uid() not in G:
                                g = G(f)
                                G[f.uid()] = g.uid()
                                D.addMorphism(g, loops=0)
                                self.connectMorphismToItsImage(f, g)
    
    def connectObjectToItsImage(self, x, y):
        F = self
        x.nameChanged.connect(lambda name: y.setName(F(name)))
        x.deleted.connect(y.delete)
        x.deleted.connect(lambda: self.deleteFromMap(x))
        x.positionChangedDelta.connect(lambda delta: self._reflectItemPosDelta(y, delta))
        
    def _reflectItemPosDelta(self, item, delta):
        if self._reflectGfx:
            item.setPos(item.pos() + delta)
               
    def deleteFromMap(self, item):
        del self._map[item.uid()]
        
    def connectMorphismToItsImage(self, f, g):
        F = self;  C = F.domain();  D = F.codomain()
        f.nameChanged.connect(lambda name: g.setName(F(name)))
        f.deleted.connect(g.delete)
        f.deleted.connect(lambda: self.deleteFromMap(f))
        f.domainSet.connect(lambda dom: self._reflectDomainSet(g, dom))
        f.codomainSet.connect(lambda cod: self._reflectCodomainSet(g, cod))
        f.bezierToggled.connect(lambda b: self._reflectToggleBezier(g, b))
        f.controlPointsPosChanged.connect(lambda pos_list: self._reflectControlPointPos(g, pos_list))
    
    def _reflectDomainSet(self, arr, dom):
        F = self;  C = self.domain();  D = self.codomain()
        if dom:
            d = D.getObject(F[dom.uid()])
            if d:
                arr.setDomain(d)
            
    def _reflectCodomainSet(self, arr, cod):
        F = self;  C = self.domain();  D = self.codomain()
        if cod:
            d = D.getObject(F[cod.uid()])
            if d:
                arr.setCodomain(d)            
    
    def _reflectToggleBezier(self, arr, toggle):
        if self._reflectGfx:
            arr.toggleBezier(toggle)
            
    def _reflectControlPointPos(self, arr, pos_list):
        if len(pos_list) == 4:
            if not arr.isBezier():
                arr.toggleBezier(True)
        elif len(pos_list) == 2:
            if arr.isBezier():
                arr.toggleBezier(False)
        else:
            raise NotImplementedError
        arr.setPointPositions(pos_list)
    
    def deleteFromMap(self, item):
        if item.uid() in self._map:
            del self._map[item.uid()]
    
    def undoTakeImage(self, undoable=False):
        if self.isFullyAttachedFunctor():
            if undoable:
                getText = lambda: "Undo take functor image " + self(str(self.domain()))
                command = MethodCallCommand(getText(), self.undoTakeImage, [], self.takeImage, [dict(self._map), deepcopy(self._memo)], self.editor())
                self.editor().pushCommand(command)
                self.nameChanged.connect(lambda name: command.setText(getText()))
                self.domain().nameChanged.connect(lambda name: command.setText(getText()))
            else:
                G = self
                C = G.domain()
                D = G.codomain()
                for x in C.objects().values():
                    if x.uid() in G:
                        y = G[x.uid()]   # returns a uid of an object in D
                        y = D.getObject(y)
                        if y:
                            D.removeObject(y, emit=False)
                            for f in y.outgoingArrows():
                                if f.uid() in G:
                                    g = G[f.uid()]
                                    g = D.getMorphism(g)
                                    D.removeMorphism(g, emit=False) 
                self._memo.clear()
                self._map.clear()
                                
    def updateImage(self, loops=None):
        if self.isFullyAttachedFunctor():
            if loops is None:
                loops = 1            
            C = self.domain()
            D = self.codomain()
            F = self
            for x in list(C.objects().values()):   # endofunctors require a copy here
                if x.uid() not in self._map:
                    y = F[x.uid()] = F(x)
                    D.addObject(y, loops=loops)
                    self.connectObjectToItsImage(x, y)
            for f in list(C.morphisms().values()):
                if f.uid() not in self._map:
                    g = F[f.uid()] = F(f)
                    D.addMorphism(g, loops=loops)    # BUFIX add g here not f!
                    self.connectMorphismToItsImage(f, g)
                            
    def setTo(self, cod, undoable=False):
        assert(cod is None or isinstance(cod, Diagram))
        if cod is not self.codomain():
            super().setTo(cod, undoable)
            if cod is not None:
                self.takeImage(undoable=undoable)
            else:
                self.undoTakeImage(undoable=undoable)
            
    def setFrom(self, dom, undoable=False):
        assert(dom is None or isinstance(dom, Diagram))
        if dom is not self.domain():
            if dom is None:
                self.undoTakeImage(undoable)
            super().setFrom(dom, undoable)
        
    def isFullyAttachedFunctor(self):
        return isinstance(self.codomain(), Diagram) and isinstance(self.domain(), Diagram)
        
    def __contains__(self, uid):
        return uid in self._map
    
    def __getitem__(self, preimage):
        return self._map.get(preimage, None)
    
    def __setitem__(self, preimage, image):
        self._map[preimage] = image
        return image
    
    def __delitem__(self, uid):
        del self._map[uid]
    
    def __call__(self, *args):
        memo = self._memo
        if len(args) == 1:
            x = args[0]
            if isinstance(x, CategoryObject):
                y = deepcopy(x, memo)
                y.setName(self(str(y)))
                res = y
            elif isinstance(x, CategoryArrow):
                g = deepcopy(x, memo)        # Deepcopy memoization fixes many bugs
                g.setName(self(str(g)))
                res = g
            elif isinstance(x, str):
                res =  str(self) + "(" + x + ")"
            return res
        else:
            raise NotImplementedError
    
    def buildDefaultContextMenu(self, menu=None):
        if menu is None:
            menu = QMenu()
        super().buildDefaultContextMenu(menu)
        menu.addSeparator()
        act = menu.addAction("Reflect Graphics")
        act.setCheckable(True)
        act.setChecked(self._reflectGfx)
        act.toggled.connect(self.setReflectGraphics)
        return menu
        
    def setReflectGraphics(self, reflect):
        self._reflectGfx = reflect
        