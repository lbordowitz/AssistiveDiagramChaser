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
    def __init__(self, text, dom, cod, functor, editor, contra=False, swap=False):
        super().__init__(text, editor)
        self._functor = functor
        self._cod = cod
        self._dom = dom
        self._swap = swap
        self._contra = contra
        if swap:
            self._changes = functor.mapping()
            self._map = {}
        else:
            self._changes = {}
            self._map = functor.mapping()
        
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
                    self._changes[x.uid()] = y.uid()
                    D.addObject(y)
                    G.connectObjectToItsImage(x, y)
            for f in list(C.morphisms().values()):
                if f.uid() not in self._map:
                    g = G(f)
                    self._changes[f.uid()] = g.uid()
                    D.addMorphism(g)
                    G.connectMorphismToItsImage(f, g)
            self.editor().scene().update()
            G.setMapping({**self._map, **self._changes})
                
    def _undo(self):
        F = self._functor
        C = self._dom
        D = self._cod
        for xuid, yuid in self._changes.items():
            if yuid in D.objects():
                D.removeObject(D.getObject(yuid))
                F.disconnectObjectFromItsImage(C.getObject(xuid), D.getObject(yuid))
            elif yuid in D.morphisms():
                D.removeMorphism(D.getMorphism(yuid))
                F.disconnectMorphismFromItsImage(C.getMorphism(xuid), D.getMorphism(yuid))
        self._changes.clear()
        F.setMapping(self._map)
            
        
           