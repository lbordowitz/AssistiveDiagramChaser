# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'command_timeline.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CommandTimeline(object):
    def setupUi(self, CommandTimeline):
        CommandTimeline.setObjectName("CommandTimeline")
        CommandTimeline.resize(270, 365)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.gridLayout.setObjectName("gridLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(self.dockWidgetContents)
        self.stackedWidget.setObjectName("stackedWidget")
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        CommandTimeline.setWidget(self.dockWidgetContents)

        self.retranslateUi(CommandTimeline)
        QtCore.QMetaObject.connectSlotsByName(CommandTimeline)

    def retranslateUi(self, CommandTimeline):
        _translate = QtCore.QCoreApplication.translate
        CommandTimeline.setWindowTitle(_translate("CommandTimeline", "Command Timeline"))

