from PyQt5.QtWidgets import *
from app_window import *
from PyQt5.QtGui import *
from typing import TypedDict
from settings import settings

class ActionsDict(TypedDict):
    about: QAction
    help: QAction
    open_reader: QAction
    import_koreader: QAction
    import_kindle: QAction
    export_notes_csv: QAction
    export_lookups_csv: QAction

class MenuBar(QMenuBar):
    def __init__(self):
        super().__init__()

        self.actionsDict: ActionsDict = {
            "about": QAction("&About"),
            "help": QAction("&Help"),
            "open_reader": QAction("&Reader"),
            "import_koreader": QAction("Import K&OReader"),
            "import_kindle": QAction("Import &Kindle"),
            "export_notes_csv": QAction("Export &notes to CSV"),
            "export_lookups_csv": QAction("Export &lookup data to CSV"),
        } 
        if not settings.value("reader_enabled", True, type=bool):
            self.actionsDict["open_reader"].setEnabled(False)

        self.addMenu("&About").addAction(self.actionsDict["about"])
        self.addMenu("&Help").addAction(self.actionsDict["help"])
        self.addMenu("&Reader").addAction(self.actionsDict["open_reader"])
        self.addMenu("&Import").addActions([
            self.actionsDict["import_kindle"], self.actionsDict["import_koreader"]])
        self.addMenu("&Export").addActions([
            self.actionsDict["export_notes_csv"], self.actionsDict["export_lookups_csv"]])