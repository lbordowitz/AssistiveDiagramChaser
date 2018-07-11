from text_item import TextItem

class CodeItem(TextItem):
    def __init__(self, code=None):
        super().__init__(code)
        
    def isStateMachine(self):
        return self._isStateMachine
    
    def stateMachine(self):
        return self._stateMachine