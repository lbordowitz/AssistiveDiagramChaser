from PyQt5.QtCore import QObject

class Project(QObject):
    def __init__(self, name=None, new=True):
        super().__init__()
        if new:
            self._name = name
        
    def name(self):
        return self._name
    
    def setName(self, name):
        self._name = name