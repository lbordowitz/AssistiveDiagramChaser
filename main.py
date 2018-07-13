from PyQt5.QtWidgets import QMainWindow, QApplication
from graph_editor import GraphEditor
import sys
from graph_node import GraphNode
from PyQt5.QtCore import QPointF
import _pickle as pickle
from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QTransform
from graph_scene import GraphScene
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication([])

    main_win = MainWindow()
    main_win.show()
    
    sys.exit(app.exec_())