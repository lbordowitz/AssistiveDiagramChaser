from text_item import TextItem

class Composition(TextItem):
    def __init__(self, atom_text=None):
        super().__init__(atom_text)
        self._composition = []
        
    def __call__(self, comp):
        c = Composition(str(self) + str(comp))
        c._composition = self._composition + comp._composition
        return c
        
    def __getitem__(self, index):
        return self._composition[index]
    
    def __len__(self):
        return len(self._composition)
    