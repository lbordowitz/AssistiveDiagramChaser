from functor import Functor
from category_diagram import CategoryDiagram
from category_arrow import CategoryArrow

class OpFunctor(Functor):
    def __init__(self, new=True):
        super().__init__(new)
        self.setLabelText(0, "op")
        self.label(0).setEditable(False)
        self.setContravariant(True)
        
    def setDomain(self, dom, undoable=False):
        if dom is not self.domain():
            super().setDomain(dom, undoable)
            cod = self.codomain()
            if cod and dom:
                cod.setSymbol(self.imageString(dom))
                cod.categoryLabel().addConstraint(lambda: cod.category() == self.imageString(dom))
    
    def setCodomain(self, cod, undoable=False):
        prev_cod = self.codomain()
        if cod is not prev_cod:
            if prev_cod:  prev_cod.symbolLabel().setEditable(True)
            super().setCodomain(cod, undoable)
            dom = self.domain()
            if dom and cod:                
                cod.categoryLabel().setEditable(False)
                cod.setCategory(self.imageString(dom))
                cod.symbolLabel().addConstraint(lambda: cod.category() == self.imageString(dom))
                
    def canConnectTo(self, item, at_tail):
        if super().canConnectTo(item, at_tail) == False:
            return False
        if at_tail == False:
            if isinstance(item, CategoryDiagram) and not item.categoryLabel().isConstrained():
                return True
        return True
        
    def takeImage(self, dom=None, cod=None, contra=False):
        super().takeImage(dom, cod, not contra)    # This is flag to invert the arrows in the image
        
    def imageString(self, x):
        if isinstance(x, (CategoryDiagram, CategoryArrow)):
            return str(x) + "^op"
        return str(x)