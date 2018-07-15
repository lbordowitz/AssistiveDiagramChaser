from category_arrow import CategoryArrow
from category import Category
from PyQt5.QtWidgets import QGraphicsSceneHoverEvent
from commands import MethodCallCommand
from category_object import CategoryObject
from copy import deepcopy

class Functor(CategoryArrow):
    def __init__(self, new=True):
        super().__init__(new)
        if new:
            self._map = {}
        self._memo = {}
        
    def takeImage(self, undoable=False):
        if self.isFullyAttachedFunctor():
            if undoable:
                self.editor().pushCommand(MethodCallCommand("Take functor image", self.takeImage, [], self.undoTakeImage, [], self.editor()))
            else:            
                G = self
                C = G.domain()
                D = G.codomain()
                for x in C.objects().values():
                    if x.uid() not in G:
                        y = G[x.uid()] = G(x)
                        D.addObject(y, emit=False)
                        x.nameChanged.connect(lambda name: y.setName(G(name)))
                        self.connectObjectToItsImage(x, y)
                        for f in x.outgoingArrows():
                            if f.uid() not in G:
                                g = G[f.uid()] = G(f)
                                D.addMorphism(g, emit=False)
                                self.connectMorphismToItsImage(f, g)
                                f.nameChanged.connect(lambda name: g.setName(G(name)))
    
    def connectObjectToItsImage(self, x, y):
        F = self
        x.nameChanged.connect(lambda name: y.setName(F(name)))
        x.deleted.connect(y.delete)
        x.deleted.connect(lambda: self.deleteFromMap(x))
        # TODO make this optional
        x.positionChangedDelta.connect(lambda delta: y.setPos(y.pos() + delta))
        
    def deleteFromMap(self, item):
        del self._map[item.uid()]
        
    def connectMorphismToItsImage(self, f, g):
        F = self
        f.nameChanged.connect(lambda name: g.setName(F(name)))
        f.deleted.connect(g.delete)
        f.deleted.connect(lambda: self.deleteFromMap(f))
        #TODO make these to tandem optional
        f.bezierToggled.connect(g.toggleBezier)
        f.controlPointsPosChanged.connect(g.setPointPositions)
    
    def deleteFromMap(self, item):
        del self._map[item.uid()]
    
    def undoTakeImage(self, undoable=False):
        if self.isFullyAttachedFunctor():
            if undoable:
                command = MethodCallCommand("Undo take functor image", self.undoTakeImage, [], self.takeImage, [], self.editor())
                self.nameChanged.connect(lambda name: self.setCommandText(command, "Undo take functor " + str(self) + "'s image"))
                self.editor().pushCommand(command)
            else:
                G = self
                C = G.domain()
                D = G.codomain()
                for x in C.objects().values():
                    if x.uid() in G:
                        y = G[x.uid()]
                        D.removeObject(y, emit=False)
                        for f in y.outgoingArrows():
                            if f.uid() in G:
                                g = G[f.uid()]
                                D.removeMorphism(g, emit=False) 
                self._memo.clear()
                self._map.clear()
                                
    def updateImage(self):
        if self.isFullyAttachedFunctor():
            C = self.domain()
            D = self.codomain()
            F = self
            for x in C.objects().values():
                if x.uid() not in self._map:
                    y = F[x.uid()] = F(x)
                    D.addObject(y, emit=False)
                    self.connectObjectToItsImage(x, y)
            for f in C.morphisms().values():
                if f.uid() not in self._map:
                    g = F[f.uid()] = F(f)
                    D.addMorphism(g, emit=False)    # BUFIX add g here not f!
                    self.connectMorphismToItsImage(f, g)
                            
    def setTo(self, cod, undoable=False):
        assert(cod is None or isinstance(cod, Category))
        if cod is not self.codomain():
            super().setTo(cod, undoable)
            self.takeImage(undoable)
            
    def setFrom(self, dom, undoable=False):
        assert(dom is None or isinstance(dom, Category))
        if dom is not self.domain():
            self.undoTakeImage(undoable)
            super().setFrom(dom, undoable)
        
    def isFullyAttachedFunctor(self):
        return isinstance(self.codomain(), Category) and isinstance(self.domain(), Category)
        
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
        
