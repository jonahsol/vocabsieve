from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ext.api_server.server import APIServer
from ext.reader import ReaderServer
from funcs.text_manipulation import *
from constants import *
from ui.widgets import *
from hid import *
from controllers.controller import *
from ui.layout import *
from app_text import *
from settings import *
from hid import *
from updates import *

QCoreApplication.setApplicationName(app_title)
QCoreApplication.setOrganizationName(app_organization)

class AppWindow(QMainWindow):
    prev_clipboard = ""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(app_title)
        self.setFocusPolicy(Qt.StrongFocus)

        # Widgets, controller and HID
        self.widgets = Widgets(on_close_app=self.close)
        self.setCentralWidget(self.widgets.centralWidget)
        self.setMenuBar(self.widgets.menuBar)
        self.setStatusBar(self.widgets.statusBar)

        self.controller = Controller(self.widgets)
        self.hid = HID(self, self.controller, self.widgets)

        # Layout
        scale_font(self)
        if settings.get("orientation") == "VERTICAL": 
            draw_layout_v(self, self.widgets) 
        else: draw_layout_h(self, self.widgets) 

        check_updates(self)

    def focusInEvent(self, event):
        if platform.system() == "Darwin":
            if self.prev_clipboard != QApplication.clipboard().text():
                self.hid.readClipboard(evenWhenFocused=True)
            self.prev_clipboard = QApplication.clipboard().text()
        super().focusInEvent(event)
