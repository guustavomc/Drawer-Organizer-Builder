
import sys

from PyQt6.QtWidgets import (QApplication)
from OpenGL.GL import *
from OpenGL.GLU import *

from ui.main_window import MainWindow

# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Organizer Creator")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
