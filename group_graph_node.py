from graph_node import GraphNode

class GroupGraphNode(GraphNode):
    def __init__(self, new=True):
        super().__init__(new)
        if new:
            pass
        
    def addToGroup(self, item):
        item.setParentItem(self)
        
    def removeFromGroup(self, item):
        item.setParentItem(None)
                
    #def buildDefaultContextMenu(self, menu=None):
        #if menu is None:
            #menu = QMenu()
        #col_menu = menu.addMenu("Color")
        #col_menu.addAction("Brush").triggered.connect(lambda: self._brushColorDlg.exec_())
        #col_menu.addAction("Pen").triggered.connect(lambda: self._penColorDlg.exec_())
        #fit = menu.addAction("Fit Contents")
        #fit.triggered.connect(self.setFitContents)
        #fit.setCheckable(True)
        #fit.setChecked(False)
        #return menu
    