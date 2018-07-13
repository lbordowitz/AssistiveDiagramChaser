from PyQt5.QtWidgets import QDialog
from ui_int_spin_dialog import Ui_IntSpinDialog
from PyQt5.QtCore import Qt

class IntSpinDialog(QDialog, Ui_IntSpinDialog):
    def __init__(self, prefix=None, suffix=None):
        super().__init__()
        super().__init__()
        self.setupUi(self)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint)       
        if prefix:
            self.spinBox.setPrefix(prefix)
        if suffix:
            self.spinBox.setSuffix(suffix)
            
    def exec_(self):
        crnt_val = self.spinBox.value()
        result = super().exec_()
        if result == self.Rejected:
            self.spinBox.setValue(crnt_val)