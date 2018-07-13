from text_item import TextItem
from copy import deepcopy

class LabeledGfx:
    def __init__(self):
        self._labels = []
        self.LabelType = TextItem
        self._textPos = []
        
    def addLabel(self, label):
        if isinstance(label, str):
            label = self.LabelType(label)
        self._labels.append(label)
        self._textPos.append(None)
        label.installSceneEventFilter(self)
        label.setFlag(label.ItemIsFocusable, True)
        label.setParentItem(self)
        self.saveTextPosition()
        return label
        
    def removeLabel(self, label):
        k = self.labelIndex(label)
        if k != -1:
            self._labels.pop(k)
            self._textPos.pop(k)
            if self.scene():
                self.scene().removeItem(label)
            label.setParentItem(None)
            label.removeSceneEventFilter(self)

    def labelText(self, label):
        if isinstance(label, int):
            label = self.label(label)
        if isinstance(label, TextItem):
            return label.toPlainText()
        else:
            raise NotImplementedError
        
    def setLabelText(self, k, text):
        label = self._labels[k]
        if isinstance(label, TextItem):
            label.setPlainText(text)
        else:
            raise NotImplementedError
        
    def labelIndex(self, label_text):
        if isinstance(label_text, str):
            for k in range(0, self.labelCount()):
                label = self.label(k)
                if self.labelText(label) == label_text:
                    return k
        else:
            for k in range(0, self.labelCount()):
                label = self.label(k)
                if label_text is label:
                    return k
        return -1
    
    def findLabel(self, text):
        for label in self._labels:
            if self.labelText(label) == text:
                return label
        return None
    
    def findLabels(self, text):
        labels = []
        for lab in self._labels:
            if self.labelText(lab) == text:
                labels.append(lab)
        return labels
    
    def textIndex(self, text):
        for k in range(0, len(self._labels)):
            if self.labelText(self.label(k)) == text:
                return k
        return -1
    
    def labelCount(self):
        return len(self._labels)
    
    def labels(self):
        return self._labels    
    
    def label(self, k):
        return self._labels[k]
    
    def saveTextPosition(self):
        raise NotImplementedError
    
    def updateTextPosition(self):
        raise NotImplementedError
    
    def copyLabelsTo(self, copy):
        for label in self._labels:
            label_copy = deepcopy(label)
            copy.addLabel(label_copy)
        copy.saveTextPosition()
            
            