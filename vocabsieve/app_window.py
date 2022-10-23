from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from api import LanguageServer
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

        self.startServer()
        check_updates(self)

        self.prev_clipboard = ""

    def focusInEvent(self, event):
        if platform.system() == "Darwin":
            if self.prev_clipboard != QApplication.clipboard().text():
                self.hid.readClipboard(evenWhenFocused=True)
            self.prev_clipboard = QApplication.clipboard().text()
        super().focusInEvent(event)

    def startServer(self):
        if settings.value("api_enabled", True, type=bool):
            try:
                self.thread = QThread()
                port = settings.value("port", 39284, type=int)
                host = settings.value("host", "127.0.0.1")
                self.worker = LanguageServer(self, host, port)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.start_api)
                self.worker.note_signal.connect(self.onNoteSignal)
                self.thread.start()
            except Exception as e:
                print(e)
                self.widgets.status("Failed to start API server")
        if settings.value("reader_enabled", True, type=bool):
            try:
                self.thread2 = QThread()
                port = settings.value("reader_port", 39285, type=int)
                host = settings.value("reader_host", "127.0.0.1")
                self.worker2 = ReaderServer(self, host, port)
                self.worker2.moveToThread(self.thread2)
                self.thread2.started.connect(self.worker2.start_api)
                self.thread2.start()
            except Exception as e:
                print(e)
                self.widgets.status("Failed to start reader server")

    def onNoteSignal(
            self,
            sentence: str,
            word: str,
            definition: str,
            tags: list):
        self.controller.state.setSentence(sentence)
        self.controller.state.setWord(word)
        self.widgets.definition.setText(definition)
        self.widgets.tags.setText(" ".join(tags))
        self.controller.ankiController.createNote()