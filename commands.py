from PyQt5.QtWidgets import QUndoCommand, QApplication
from category_object import CategoryObject

class Command(QUndoCommand):
    def __init__(self, text, editor=None, skip1st=False):
        super().__init__(text)
        self._skip1st = skip1st
        self._subcommands = []
        self._editor = editor
        
    def redo(self):
        if self._skip1st:
            self._skip1st = False
        else:
            self._redo()
            
    def undo(self):
        for cmd in reversed(self._subcommands):
            cmd.undo()
                
    def _redo(self):
        for cmd in self._subcommands:
            cmd.redo()
            
    def editor(self):
        return self._editor
    
    def addSubcommand(self, command):
        self._subcommands.append(command)
        
    def setText(self, text):
        super().setText(text)
        fw = QApplication.focusWidget()
        self.editor().undoView().setFocus()        
        fw.setFocus()
        

class MethodCallCommand(Command):
    def __init__(self, text, method, args, undomethod, undoargs, editor):
        super().__init__(text, editor)
        self._args = args
        self._undoargs = undoargs
        self._method = method
        self._undomethod = undomethod
        
    def undo(self):
        super().undo()
        self._undomethod(*self._undoargs)
        
    def _redo(self):
        self._method(*self._args)
        super()._redo()
        
    def method(self):
        return self._method
    

class DeleteItemsCommand(Command):
    def __init__(self, text, items, editor):
        super().__init__(text, editor)
        self._items = items
        self._deleted = []
        
    def _redo(self):
        self._deleted.clear()
        for item in self._items:
            self._deleted.append(item.delete())
        
    def undo(self):
        for k in range(0, len(self._deleted)):
            self._items[k].undelete(self._deleted[k])
            
            
class TakeFunctorImage(Command):
    def __init__(self, text, dom, cod, functor, editor, swap=False):
        super().__init__(text, editor)
        self._functor = functor
        self._map = functor.mapping()
        self._reverseMap = { val : key for key, val in self._map.items() }
        self._cod = cod
        self._dom = dom
        self._swap = swap
        
    def _redo(self):
        if self._swap:
            self._undo()
        else:
            self.__redo()
        
    def undo(self):
        if self._swap:
            self.__redo()
        else:
            self._undo()
            
    def __redo(self):
        if self._dom and self._dom.nonempty():
            G = self._functor
            C = self._dom
            D = self._cod
            for x in list(C.objects().values()):    # So we can add to objects() during iteration  (endofunctors)
                if x.uid() not in self._map:
                    y = G(x)
                    self._map[x.uid()] = y.uid()
                else:
                    y = D.getObject(G[x.uid()])
                if y:
                    D.addObject(y)
                    G.connectObjectToItsImage(x, y)
            for f in list(C.morphisms().values()):
                if f.uid() not in self._map:
                    g = G(f)
                    self._map[f.uid()] = g.uid()
                else:
                    g = D.getMorphism(G[f.uid()])
                if g:
                    D.addMorphism(g)
                    G.connectMorphismToItsImage(f, g)
            self.editor().scene().update()
            G.setMapping(self._map)
                
    def _undo(self):
        if self._cod.nonempty():
            G = self._functor
            C = self._dom
            D = self._cod
            for y in list(D.objects().values()):
                if y.uid() in self._reverseMap:
                    D.removeObject(y)
                    G.disconnectObjectFromItsImage(C.getObject(self._reverseMap[y.uid()]), y)
                    xuid = self._reverseMap[y.uid()]
                    del self._reverseMap[y.uid()]
                    del self._map[xuid]                    
            for g in list(D.morphisms().values()):
                if g.uid() in self._reverseMap:
                    D.removeMorphism(g)
                    G.disconnectMorphismFromItsImage(C.getMorphism(self._reverseMap[g.uid()]), g)
                    fuid = self._reverseMap[g.uid()]
                    del self._reverseMap[g.uid()]
                    del self._map[fuid]                    
            self.editor().scene().update()
            G.setMapping(self._map)
                
        
class UpdateFunctorImage(Command):
    def __init__(self, text, functor, editor):
        super().__init__(text, editor)
        self._functor = functor
        self._map = dict(functor.mapping())
        self._reverseMap = set(self._map.values())
        self._cod = functor.codomain()
        self._dom = functor.domain()
        self._update = {}
        
    def _redo(self):
        F = self._functor
        C = self._dom
        D = self._cod
        self._update.clear()
        for x in C.objects().values():
            if x.uid() not in self._map:
                y = F(x)
                self._update[x.uid()] = y.uid()
                D.addObject(y)
                F.connectObjectToItsImage(x, y)
        for f in C.morphisms().values():
            if f.uid() not in self._map:
                g = F(f)
                self._update[f.uid()] = g.uid()
                D.addMorphism(g)
                F.connectMorphismToItsImage(f, g)
        F.updateMapping(self._update)
        
    def undo(self):
        F = self._functor
        C = self._dom
        D = self._cod
        for xuid, yuid in self._update.items():
            if yuid in D.objects():
                D.removeObject(D.getObject(yuid))
                xuid = self._reverseMap[yuid]
                del self._reverseMap[yuid]
                del self._map[xuid]
                F.disconnectObjectFromItsImage(C.getObject(xuid), D.getObject(yuid))
            elif yuid in D.morphisms():
                D.removeMorphism(D.getMorphism(yuid))
                xuid = self._reverseMap[yuid]
                del self._reverseMap[yuid]
                del self._map[xuid]               
                F.disconnectMorphismFromItsImage(C.getMorphism(xuid), D.getMorphism(yuid))
        F.setMapping(self._map)
                    
        