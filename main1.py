import sys

from functools import partial

from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QPushButton, QLabel, \
                             QStackedWidget, QUndoStack, QUndoCommand, QApplication, \
                             QUndoView)
from PyQt5.QtCore import QObject, pyqtSignal, Qt

class Command(QUndoCommand):
    def undo(self):
        print("Command Undone")

    def redo(self):
        print("Command Redone")


class CommandTimeline(QDockWidget):
    def __init__(self):
        super().__init__()
        self.stackedWidget = QStackedWidget()
        self.setWidget(self.stackedWidget)

    def addUndoView(self, stack):
        view = QUndoView(stack)
        self.stackedWidget.addWidget(view)
        return view


class Obj(QObject):
    nameChanged = pyqtSignal(str)

    def __init__(self, name):
        super().__init__()
        self._name = name

    def setName(self, name):
        self._name = name
        self.nameChanged.emit(name)

    def __str__(self):
        return self._name


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.undoStack = QUndoStack()
        self.commandTimeline = CommandTimeline()
        self.view = self.commandTimeline.addUndoView(self.undoStack)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.commandTimeline)
        button = QPushButton("Click")
        self.setCentralWidget(button)
        button.clicked.connect(self.changeObjName)
        self.obj = Obj("A")
        self.addCommand()


    def addCommand(self):
        command = Command()
        command.setText("The command text: {}".format(self.obj))
        self.obj.nameChanged.connect(partial(self.onNameChanged, command))
        self.undoStack.push(command)

    def changeObjName(self):
        self.obj.setName("B")

    def onNameChanged(self, command, name):
        fw = QApplication.focusWidget()
        command.setText("The command text: {}".format(name))
        self.view.setFocus()
        fw.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())