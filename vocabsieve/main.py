import sys
from PyQt5.QtWidgets import *
from app_window import *

def main():
    app = QApplication(sys.argv)
    w = AppWindow()

    w.show()
    sys.exit(app.exec())

main()
