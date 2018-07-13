# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'int_spin_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_IntSpinDialog(object):
    def setupUi(self, IntSpinDialog):
        IntSpinDialog.setObjectName("IntSpinDialog")
        IntSpinDialog.resize(174, 82)
        self.gridLayout = QtWidgets.QGridLayout(IntSpinDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.spinBox = QtWidgets.QSpinBox(IntSpinDialog)
        self.spinBox.setMinimumSize(QtCore.QSize(0, 35))
        self.spinBox.setObjectName("spinBox")
        self.gridLayout.addWidget(self.spinBox, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(IntSpinDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(IntSpinDialog)
        self.buttonBox.accepted.connect(IntSpinDialog.accept)
        self.buttonBox.rejected.connect(IntSpinDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(IntSpinDialog)

    def retranslateUi(self, IntSpinDialog):
        _translate = QtCore.QCoreApplication.translate
        IntSpinDialog.setWindowTitle(_translate("IntSpinDialog", "Dialog"))

