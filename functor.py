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
                self._memo.clear()
                for x in C.objects().values():
                    if x.uid() not in G:
                        y = G[x.uid()] = G(x)
                        D.addObject(y)
                        for f in x.outgoingArrows():
                            if f.uid() not in G:
                                g = G[f.uid()] = G(f)
                                D.addMorphism(g)
    
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
                for x in C.objects():
                    if x.uid() in G:
                        y = G[x.uid()]
                        D.removeObject(y)
                        for f in y.outgoingArrows():
                            if f.uid() in G:
                                g = G[f.uid()]
                                D.removeMorphism(g)    
                            
    def setCodomain(self, cod, undoable=False):
        assert(cod is None or isinstance(cod, Category))
        if cod is not self.codomain():
            super().setCodomain(cod, undoable)
            self.takeImage(undoable)
            
    def setDomain(self, dom, undoable=False):
        assert(dom is None or isinstance(dom, Category))
        if dom is not self.domain():
            self.undoTakeImage(undoable)
            super().setDomain(dom, undoable)
        
    def isFullyAttachedFunctor(self):
        return isinstance(self.codomain(), Category) and isinstance(self.domain(), Category)
        
    def __contains__(self, uid):
        return uid in self._map
    
    def __getitem__(self, preimage):
        return self._map.get(preimage, d=None)
    
    def __setitem__(self, preimage, image):
        self._map[preimage] = image
        return image
    
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