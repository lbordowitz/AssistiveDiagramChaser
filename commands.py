from PyQt5.QtWidgets import QUndoCommand
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