from logging import getLevelName
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qt import QDesktopServices, QUrl
from PyQt5.QtCore import *
from typing import Optional

DEBUGGING = None
if os.environ.get("VOCABSIEVE_DEBUG"):
    DEBUGGING = True

def getDebugDescription():
    return "(debug=" + os.environ.get("VOCABSIEVE_DEBUG", "") + ")"
def getAppTitle():
    name = "VocabSieve"
    if DEBUGGING: 
        return name + " " + getDebugDescription()
    else:
        return name

QCoreApplication.setApplicationName(getAppTitle())
QCoreApplication.setOrganizationName("FreeLanguageTools")

from .config import *
from .tools import *
from .db import *
from .dictionary import *
from .api import LanguageServer
from . import __version__
from .ext.reader import ReaderServer
from .ext.importer import KindleImporter, KoreaderImporter
from .text_manipulation import *
from .gui import *
from .constants import *
import sys
import importlib
import functools
import requests
import platform
import time
import json
import csv
from packaging import version
from markdown import markdown
from markdownify import markdownify
from datetime import datetime
from collections import defaultdict
from enum import Enum, unique, auto
import re
Path(os.path.join(datapath, "images")).mkdir(parents=True, exist_ok=True)
# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text
if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"

@unique
class Field(Enum):
    SENTENCE = auto()
    DEFINITION = auto()
    DEFINITION2 = auto()

@unique
class Event(Enum):
    DOUBLECLICK = auto()
    MOUSEPRESS = auto()
    SELECTION = auto()

events = {}
for ev in Event:
    events[ev] = { fieldEnum: ev.name + fieldEnum.name for fieldEnum in Field }

@functools.lru_cache()
class GlobalObject(QObject):
    """
    We need this to enable the textedit widget to communicate with the main window
    """

    def __init__(self):
        super().__init__()
        self._events = defaultdict(list)

    def addEventListener(self, name, func):
        self._events[name].append(func)

    def dispatchEvent(self, name, **args):
        functions = self._events[name]
        for func in functions:
            QTimer.singleShot(0, lambda: func(**args))


class MyTextEdit(QTextEdit):

    def __init__(self, fieldEnum):
        super().__init__()
        self.fieldEnum = fieldEnum
        self.partialLookupFailureBlock = None
        self.completeLookupFailureBlock = None

        self.selectionChanged.connect(self.handleSelectionChanged)
    
    @pyqtSlot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        GlobalObject().dispatchEvent(events[Event.DOUBLECLICK][self.fieldEnum])
        self.textCursor().clearSelection()
        self.original = ""

    @pyqtSlot()
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        GlobalObject().dispatchEvent(events[Event.MOUSEPRESS][self.fieldEnum])

    @pyqtSlot()
    def handleSelectionChanged(self):
        GlobalObject().dispatchEvent(events[Event.SELECTION][self.fieldEnum])


class DictionaryWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # State
        self.audio_path = ""
        self.prev_clipboard = ""
        self.image_path = None 
        self.rawWordLookup = None

        # App
        self.setWindowTitle(getAppTitle())
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget = QWidget()
        self.settings = QSettings()
        self.rec = Record()
        self.setCentralWidget(self.widget)
        self.scaleFont()
        self.initWidgets()
        if self.settings.value("orientation", "Vertical") == "Vertical":
            self.resize(400, 700)
            self.setupWidgetsV()
        else:
            self.resize(1000, 300)
            self.setupWidgetsH()
        self.setupMenu()
        self.setupButtons()
        self.startServer()
        self.initTimer()
        self.updateAnkiButtonState()
        self.setupShortcuts()
        self.checkUpdates()

        # Sentence listeners
        GlobalObject().addEventListener(events[Event.DOUBLECLICK][Field.SENTENCE],
                                        lambda: self.textEditDoubleClicked(Field.SENTENCE))
        GlobalObject().addEventListener(events[Event.SELECTION][Field.SENTENCE],
                                        lambda: self.selectionMade(Field.SENTENCE))
        # Definition listeners
        GlobalObject().addEventListener(events[Event.DOUBLECLICK][Field.DEFINITION],
                                        lambda: self.textEditDoubleClicked(Field.DEFINITION))
        GlobalObject().addEventListener(events[Event.MOUSEPRESS][Field.DEFINITION],
                                        lambda: self.defnFieldPressed(Field.DEFINITION))
        GlobalObject().addEventListener(events[Event.SELECTION][Field.DEFINITION],
                                        lambda: self.selectionMade(Field.DEFINITION))
        # Definition 2 listeners
        GlobalObject().addEventListener(events[Event.DOUBLECLICK][Field.DEFINITION2],
                                        lambda: self.textEditDoubleClicked(Field.DEFINITION2))
        GlobalObject().addEventListener(events[Event.MOUSEPRESS][Field.DEFINITION2],
                                        lambda: self.defnFieldPressed(Field.DEFINITION2))
        GlobalObject().addEventListener(events[Event.SELECTION][Field.DEFINITION2],
                                        lambda: self.selectionMade(Field.DEFINITION2))

        # Connect to OS clipboard
        if self.settings.value("primary", False, type=bool)\
                and QClipboard.supportsSelection(QApplication.clipboard()):
            QApplication.clipboard().selectionChanged.connect(
                lambda: self.clipboardChanged(False, True))
        QApplication.clipboard().dataChanged.connect(self.clipboardChanged)

    def scaleFont(self):
        font = QApplication.font()
        font.setPointSize(
            int(font.pointSize() * self.settings.value("text_scale", type=int) / 100))
        self.setFont(font)

    def focusInEvent(self, event):
        if platform.system() == "Darwin":
            if self.prev_clipboard != QApplication.clipboard().text():
                self.clipboardChanged(evenWhenFocused=True)
            self.prev_clipboard = QApplication.clipboard().text()
        super().focusInEvent(event)

    def checkUpdates(self):
        if self.settings.value("check_updates") is None:
            answer = QMessageBox.question(
                self,
                "Check updates",
                "<h2>Would you like VocabSieve to check for updates automatically?</h2>"
                "Currently, the repository and releases are hosted on GitHub's servers, "
                "which will be queried for checking updates. <br>VocabSieve cannot and "
                "<strong>will not</strong> install any updates automatically."
                "<br>You can change this option in the configuration panel at a later date."
            )
            if answer == QMessageBox.Yes:
                self.settings.setValue("check_updates", True)
            if answer == QMessageBox.No:
                self.settings.setValue("check_updates", False)
            self.settings.sync()
        elif self.settings.value("check_updates", True, type=bool):
            try:
                res = requests.get("https://api.github.com/repos/FreeLanguageTools/vocabsieve/releases")
                data = res.json()
            except Exception:
                return
            latest_version = (current := data[0])['tag_name'].strip('v')
            current_version = importlib.metadata.version('vocabsieve')
            if version.parse(latest_version) > version.parse(current_version):
                answer2 = QMessageBox.information(
                    self,
                    "New version",
                    "<h2>There is a new version available!</h2>"
                    + f"<h3>Version {latest_version}</h3>"
                    + markdown(current['body']),
                    buttons=QMessageBox.Open | QMessageBox.Ignore
                )
                if answer2 == QMessageBox.Open:
                    QDesktopServices.openUrl(QUrl(current['html_url']))
        else:
            pass

    def initWidgets(self):
        self.namelabel = QLabel(
            "<h2 style=\"font-weight: normal;\">" + getAppTitle() + "</h2>")
        self.menu = QMenuBar(self)

        self.sentence = MyTextEdit(Field.SENTENCE)
        self.sentence.setPlaceholderText(
            "Sentence copied to the clipboard will show up here.")
        self.sentence.setMinimumHeight(50)
        #self.sentence.setMaximumHeight(300)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Word will appear here when looked up.")
        self.definition = MyTextEdit(Field.DEFINITION)
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = MyTextEdit(Field.DEFINITION2)
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)

        self.fieldEnumToField = {}
        self.fieldEnumToField[Field.SENTENCE] = self.sentence
        self.fieldEnumToField[Field.DEFINITION] = self.definition
        self.fieldEnumToField[Field.DEFINITION2] = self.definition2
        
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Type in a list of tags to be used, separated by spaces (same as in Anki).")
        self.sentence.setToolTip(
            "Look up a word by double clicking it. Or, select it"
            ", then press \"Get definition\".")

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton(f"Define Direct [Shift-{MOD}-D]")
        self.lookup_exact_button.setToolTip(
            "This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}-S]")

        self.config_button = QPushButton("Configure..")
        self.read_button = QPushButton(f"Read clipboard [{MOD}-V]")
        self.bar = QStatusBar()
        self.setStatusBar(self.bar)
        self.stats_label = QLabel()

        self.single_word = QCheckBox("Single word lookups")
        self.single_word.setToolTip(
            "If enabled, vocabsieve will act as a quick dictionary and look up any single words copied to the clipboard.\n"
            "This can potentially send your clipboard contents over the network if an online dictionary service is used.\n"
            "This is INSECURE if you use password managers that copy passwords to the clipboard.")

        self.web_button = QPushButton(f"Open webpage [{MOD}-1]")
        self.freq_display = QLineEdit()
        self.freq_display.setPlaceholderText("Word frequency")
        self.freq_display_lcd = QLCDNumber()
        self.freq_display_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.freq_display_lcd.display(0)

        self.audio_selector = QListWidget()
        self.audio_selector.setMinimumHeight(50)
        self.audio_selector.setFlow(QListView.TopToBottom)
        self.audio_selector.setResizeMode(QListView.Adjust)
        self.audio_selector.setWrapping(True)

        self.audio_selector.currentItemChanged.connect(lambda x: (
            self.play_audio(x.text()[2:]) if x is not None else None
        ))

        self.definition.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition2.setReadOnly(
            not (
                self.settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition.setPlaceholderText(
            'Look up a word by double clicking it. Or, select it, then press "Get definition".')
        self.definition2.setPlaceholderText(
            'Look up a word by double clicking it. Or, select it, then press "Get definition".')

        self.image_viewer = QLabel("<center><b>&lt;No image selected&gt;</center>")
        self.image_viewer.setScaledContents(True)
        self.image_viewer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_viewer.setStyleSheet(
            '''
                border: 1px solid black;
            '''
        )

    def play_audio(self, x):
        QCoreApplication.processEvents()
        if x is not None:
            self.audio_path = play_audio(
                x, self.audios, self.settings.value(
                    "target_language", "en"))

    
    def setupWidgetsV(self):
        self.layout = QGridLayout(self.widget)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 2)

        self.layout.addWidget(self.single_word, 1, 0, 1, 3)

        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 2, 0)
        self.layout.addWidget(self.read_button, 2, 1)
        self.layout.addWidget(self.image_viewer, 0, 2, 3, 1)
        self.layout.addWidget(self.sentence, 3, 0, 1, 3)
        self.layout.setRowStretch(3, 1)
        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 4, 0)

        if self.settings.value("lemmatization", True, type=bool):
            self.layout.addWidget(self.lookup_button, 4, 1)
            self.layout.addWidget(self.lookup_exact_button, 4, 2)
        else:
            self.layout.addWidget(self.lookup_button, 4, 1, 1, 2)

        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 6, 0)
        self.layout.addWidget(self.freq_display, 6, 1)
        self.layout.addWidget(self.web_button, 6, 2)
        self.layout.addWidget(self.word, 5, 0, 1, 3)
        self.layout.setRowStretch(7, 2)
        self.layout.setRowStretch(9, 2)
        if self.settings.value("dict_source2", DISABLED) != DISABLED:
            self.layout.addWidget(self.definition, 7, 0, 2, 3)
            self.layout.addWidget(self.definition2, 9, 0, 2, 3)
        else:
            self.layout.addWidget(self.definition, 7, 0, 4, 3)

        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Pronunciation</h3>"),
            11,
            0,
            1,
            3)
        self.layout.addWidget(self.audio_selector, 12, 0, 1, 3)
        self.layout.setRowStretch(12, 1)
        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Additional tags</h3>"),
            13,
            0,
            1,
            3)

        self.layout.addWidget(self.tags, 14, 0, 1, 3)

        self.layout.addWidget(self.toanki_button, 15, 0, 1, 3)
        self.layout.addWidget(self.config_button, 16, 0, 1, 3)


    def setupButtons(self):
        self.lookup_button.clicked.connect(
            lambda: self.lookupCurrentSelectionOrPrevWord(True))
        self.lookup_exact_button.clicked.connect(
            lambda: self.lookupCurrentSelectionOrPrevWord(False))

        self.web_button.clicked.connect(self.onWebButton)

        self.config_button.clicked.connect(self.configure)
        self.toanki_button.clicked.connect(self.createNote)
        self.read_button.clicked.connect(lambda: self.clipboardChanged(True))

        self.sentence.textChanged.connect(self.updateAnkiButtonState)

        self.bar.addPermanentWidget(self.stats_label)

    def setupMenu(self):
        self.open_reader_action = QAction("&Reader")
        self.menu.addAction(self.open_reader_action)
        if not self.settings.value("reader_enabled", True, type=bool):
            self.open_reader_action.setEnabled(False)
        importmenu = self.menu.addMenu("&Import")
        exportmenu = self.menu.addMenu("&Export")
        helpmenu = self.menu.addMenu("&Help")
        self.help_action = QAction("&Help")
        self.about_action = QAction("&About")
        helpmenu.addAction(self.help_action)
        helpmenu.addAction(self.about_action)

        self.import_koreader_action = QAction("Import K&OReader")
        self.import_kindle_action = QAction("Import &Kindle")

        self.export_notes_csv_action = QAction("Export &notes to CSV")
        self.export_lookups_csv_action = QAction("Export &lookup data to CSV")

        self.help_action.triggered.connect(self.onHelp)
        self.about_action.triggered.connect(self.onAbout)
        self.open_reader_action.triggered.connect(self.onReaderOpen)
        self.import_koreader_action.triggered.connect(self.importkoreader)
        self.import_kindle_action.triggered.connect(self.importkindle)
        self.export_notes_csv_action.triggered.connect(self.exportNotes)
        self.export_lookups_csv_action.triggered.connect(self.exportLookups)

        importmenu.addActions(
            [self.import_koreader_action, self.import_kindle_action]
        )

        exportmenu.addActions(
            [self.export_notes_csv_action, self.export_lookups_csv_action]
        )

        self.setMenuBar(self.menu)

    def exportNotes(self):
        """
        First ask for a file path, then save a CSV there.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV to file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-notes-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
            ),
            "CSV (*.csv)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(
                    ['timestamp', 'content', 'anki_export_success', 'sentence', 'word', 
                    'definition', 'definition2', 'pronunciation', 'image', 'tags']
                )
                writer.writerows(self.rec.getAllNotes())
        else:
            return

    def exportLookups(self):
        """
        First ask for a file path, then save a CSV there.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV to file",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"vocabsieve-lookups-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
            ),
            "CSV (*.csv)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(
                    ['timestamp', 'word', 'definition', 'language', 'lemmatize', 'dictionary', 'success']
                )
                writer.writerows(self.rec.getAllLookups())
        else:
            return

    def onHelp(self):
        url = f"https://wiki.freelanguagetools.org/vocabsieve_setup"
        QDesktopServices.openUrl(QUrl(url))

    def onAbout(self):
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()

    def setupWidgetsH(self):
        self.layout = QGridLayout(self.widget)
        # self.sentence.setMaximumHeight(99999)
        self.layout.addWidget(self.namelabel, 0, 0, 1, 1)
        self.layout.addWidget(self.image_viewer, 0, 1, 2, 1)
        self.layout.addWidget(self.single_word, 0, 3, 1, 2)

        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 1, 0)
        self.layout.addWidget(self.freq_display, 0, 2)
        self.layout.addWidget(self.read_button, 6, 1)

        self.layout.addWidget(self.sentence, 2, 0, 3, 2)
        self.layout.addWidget(self.audio_selector, 5, 0, 1, 2)
        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 1, 2)

        self.layout.addWidget(self.lookup_button, 3, 2)
        self.layout.addWidget(self.lookup_exact_button, 4, 2)

        self.layout.addWidget(
            QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 1, 3)
        # self.layout.add, language, lemmatize(self.web_button, 1, 4)
        self.layout.addWidget(self.word, 2, 2, 1, 1)
        if self.settings.value("dict_source2", DISABLED) != DISABLED:
            self.layout.addWidget(self.definition, 2, 3, 4, 1)
            self.layout.addWidget(self.definition2, 2, 4, 4, 1)
        else:
            self.layout.addWidget(self.definition, 2, 3, 4, 2)

        self.layout.addWidget(QLabel("Additional tags"), 5, 2, 1, 1)

        self.layout.addWidget(self.tags, 6, 2)

        self.layout.addWidget(self.toanki_button, 6, 3, 1, 1)
        self.layout.addWidget(self.config_button, 6, 4, 1, 1)
        self.layout.setColumnStretch(0, 2)
        self.layout.setColumnStretch(1, 2)
        self.layout.setColumnStretch(2, 0)
        self.layout.setColumnStretch(3, 5)
        self.layout.setColumnStretch(4, 5)
        self.layout.setRowStretch(0, 0)
        #self.layout.setRowStretch(1, 5)
        self.layout.setRowStretch(2, 5)
        self.layout.setRowStretch(3, 5)
        self.layout.setRowStretch(4, 5)
        self.layout.setRowStretch(5, 5)
        self.layout.setRowStretch(6, 0)

    def updateAnkiButtonState(self, forceDisable=False):
        if self.sentence.toPlainText() == "" or forceDisable:
            self.toanki_button.setEnabled(False)
        else:
            self.toanki_button.setEnabled(True)

    def configure(self):
        api = self.settings.value('anki_api', 'http://127.0.0.1:8765')
        if self.settings.value('enable_anki', True, type=bool):
            try:
                _ = getVersion(api)
            except Exception as e:
                print(e)
                answer = QMessageBox.question(
                    self,
                    "Could not reach AnkiConnect",
                    "<h2>Could not reach AnkiConnect</h2>"
                    "AnkiConnect is required for changing Anki-related settings."
                    "<br>Choose 'Ignore' to not change Anki settings this time."
                    "<br>Choose 'Abort' to not open the configuration window."
                    "<br><br>If you have AnkiConnect listening to a non-default port or address, "
                    "select 'Ignore and change the Anki API option on the Anki tab, and "
                    "reopen the configuration window."
                    "<br><br>If you do not wish to use Anki with this program, select 'Ignore' "
                    "and then uncheck the 'Enable Anki' checkbox on the Anki tab.",
                    buttons=QMessageBox.Ignore | QMessageBox.Abort,
                    defaultButton=QMessageBox.Ignore
                )
                if answer == QMessageBox.Ignore:
                    pass
                if answer == QMessageBox.Abort:
                    return

        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec()

    def importkindle(self):
        fname = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            filter='Kindle clippings files (*.txt)',
        )[0]
        if not fname:
            return
        else:
            import_kindle = KindleImporter(self, fname)
            import_kindle.exec()

    def importkoreader(self):
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select the directory containers ebook files",
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        )
        if not path:
            return
        else:
            import_koreader = KoreaderImporter(self, path)
            import_koreader.exec()

    def setupShortcuts(self):
        self.shortcut_toanki = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_toanki.activated.connect(self.toanki_button.animateClick)
        self.shortcut_getdef_e = QShortcut(QKeySequence('Ctrl+Shift+D'), self)
        self.shortcut_getdef_e.activated.connect(self.lookup_exact_button.animateClick)
        self.shortcut_getdef = QShortcut(QKeySequence('Ctrl+D'), self)
        self.shortcut_getdef.activated.connect(self.lookup_button.animateClick)
        self.shortcut_paste = QShortcut(QKeySequence('Ctrl+V'), self)
        self.shortcut_paste.activated.connect(self.read_button.animateClick)
        self.shortcut_web = QShortcut(QKeySequence('Ctrl+1'), self)
        self.shortcut_web.activated.connect(self.web_button.animateClick)

    def onWebButton(self):
        url = self.settings.value("custom_url",
                                  "https://en.wiktionary.org/wiki/@@@@").replace(
            "@@@@", self.word.text()
        )
        QDesktopServices.openUrl(QUrl(url))

    def onReaderOpen(self):
        url = f"http://{self.settings.value('reader_host', '127.0.0.1', type=str)}:{self.settings.value('reader_port', '39285', type=str)}"
        QDesktopServices.openUrl(QUrl(url))

    def hasLookupFailure(self, defn_field):
        return defn_field.partialLookupFailureBlock or defn_field.completeLookupFailureBlock

    def setPartialLookupFailure(self, word, defn_field):
        defn_field.partialLookupFailureBlock = \
            set_partial_lookup_failure(word, defn_field, self.settings)
        defn_field.completeLookupFailureBlock = None
    def setCompleteLookupFailure(self, word, defn_field):
        defn_field.completeLookupFailureBlock = \
            set_complete_lookup_failure(word, defn_field, self.settings)
        defn_field.partialLookupFailureBlock = None

    def handlePartialLookupFailure(self, word, defn_field):
        self.setPartialLookupFailure(word, defn_field)

    def handleCompleteLookupFailure(self, word, defn_field):
        defn_field.setReadOnly(True)
        self.setCompleteLookupFailure(
            word,
            defn_field,
        )
        # Must call after `modify_defn_field`
        self.updateAnkiButtonState(True)

    def getOtherDefField(self, fieldEnum):
        if (fieldEnum == Field.DEFINITION):
            return self.definition2
        if (fieldEnum == Field.DEFINITION2):
            return self.definition

    def clearAllLookupFailures(self):
        def clearLookupFailures(defn_field):
            if (defn_field.partialLookupFailureBlock
                or defn_field.completeLookupFailureBlock):
                reset_text_edit(defn_field)

            defn_field.completeLookupFailureBlock = None
            defn_field.partialLookupFailureBlock = None

        clearLookupFailures(self.definition)
        clearLookupFailures(self.definition2)

    def clearCompleteFailure(self, fieldEnum):
        self.updateAnkiButtonState(False)

        defn_field = self.fieldEnumToField[fieldEnum]
        self.clearPartialFailure(fieldEnum)
        defn_field.completeLookupFailureBlock = None

        other_defn_field = self.getOtherDefField(fieldEnum)
        self.setPartialLookupFailure(self.getWord(), other_defn_field)

    def clearPartialFailure(self, fieldEnum):
        defn_field = self.fieldEnumToField[fieldEnum]

        reset_text_edit(defn_field)
        defn_field.setReadOnly(False)
        defn_field.partialLookupFailureBlock = None

    def defnFieldPressed(self, fieldEnum):
        defn_field = self.fieldEnumToField[fieldEnum]

        # Check if `completeLookupFailureBlock` was clicked
        if (defn_field.completeLookupFailureBlock and
            defn_field.completeLookupFailureBlock == defn_field.textCursor().block()):
            self.clearCompleteFailure(fieldEnum)

        # Check if `partialFailureBlock` was clicked
        elif (defn_field.partialLookupFailureBlock and
              defn_field.partialLookupFailureBlock == defn_field.textCursor().block()):
            self.clearPartialFailure(fieldEnum)

    def getWord(self):
        return self.word.text()

    def selectionMade(self, fieldEnum: Field):
        self.selectedText = getSelectedText(self.fieldEnumToField[fieldEnum])
    def textEditDoubleClicked(self, fieldEnum):
        self.lookupSet(self.selectedText)

    def lookupCurrentSelectionOrPrevWord(self, use_lemmatize: bool):
        if hasattr(self, "selectedText") and self.selectedText != None:
            self.lookupSet(self.selectedText, use_lemmatize)
        else: self.lookupSet(self.rawWordLookup, use_lemmatize)

    def setDefinitionFieldState(self, dictname, defn_field: MyTextEdit, value: str):
        defn_field.original = value.strip()

        display_mode = self.settings.value(
            dictname + "/display_mode",
            "Markdown-HTML"
        )
        skip_top = self.settings.value(
            dictname + "/skip_top",
            0, type=int
        )
        collapse_newlines = self.settings.value(
            dictname + "/collapse_newlines",
            0, type=int
        )

        if display_mode in ['Raw', 'Plaintext', 'Markdown']:
            defn_field.setPlainText(
                process_definition(
                    defn_field.original,
                    display_mode,
                    skip_top,
                    collapse_newlines
                )
            )
        else:
            defn_field.setHtml(
                process_definition(
                    defn_field.original,
                    display_mode,
                    skip_top,
                    collapse_newlines
                )
            )

    def setSentence(self, content):
        self.sentence.setText(str.strip(content))

    def setWord(self, content):
        self.word.setText(content)

    def setImage(self, content: Optional[QPixmap]):
        if content == None:
            self.image_viewer.setPixmap(QPixmap())
            self.image_viewer.setText("<center><b>&lt;No image selected&gt;</center>")
            self.image_path = None
            return
        filename = str(int(time.time()*1000)) + '.' + self.settings.value("img_format", "jpg")
        self.image_path = os.path.join(datapath, "images", filename)
        content.save(
            self.image_path, quality=self.settings.value("img_quality", -1, type=int)
        )
        self.image_viewer.setPixmap(content)

    def clipboardChanged(self, evenWhenFocused=False, selection=False):
        """
        If the input is just a single word, we look it up right away.
        If it's a json and has the required fields, we use these fields to
        populate the relevant fields.
        Otherwise we dump everything to the Sentence field.
        By default this is not activated when the window is in focus to prevent
        mistakes, unless it is used from the button.
        """
        if selection:
            text = QApplication.clipboard().text(QClipboard.Selection)
        else:
            text = QApplication.clipboard().text()
        
        if not selection: 
            # I am not sure how you can copy an image to PRIMARY
            # so here we go
            if QApplication.clipboard().mimeData().hasImage():
                self.setImage(QApplication.clipboard().pixmap())
                return

        remove_spaces = self.settings.value("remove_spaces")
        lang = self.settings.value("target_language", "en")
        if self.isActiveWindow() and not evenWhenFocused:
            return
        if is_json(text):
            copyobj = json.loads(text)
            target = copyobj['word']
            target = re.sub('[\\?\\.!«»…()\\[\\]]*', "", target)
            sentence = preprocess_clipboard(copyobj['sentence'], lang)
            self.setSentence(sentence)
            self.setWord(target)
            self.lookupSet(target)
        elif self.single_word.isChecked() and is_oneword(preprocess_clipboard(text, lang)):
            self.setSentence(word := preprocess_clipboard(text, lang))
            self.setWord(word)
            self.lookupSet(text)
        else:
            self.setSentence(preprocess_clipboard(text, lang))

    
    def lookupSet(self, word: str, use_lemmatize=True):
        """ Lookup @word and modify GUI state accordingly.
        """
        lemmatize_word = use_lemmatize and self.getLemmatize()

        # Save the unlemmatized word so that it can be used by `lookup_exact_button`
        self.rawWordLookup = word
        # Clear any lookup failures from the last lookup
        self.clearAllLookupFailures()
        
        # Bold text
        sentence_text = self.sentence.toPlainText()
        if self.settings.value("bold_word", True, type=bool):
            without_bold = remove_bold(sentence_text)
            sentence_text = bold_word_in_text(
                word, 
                without_bold, 
                self.getLanguage(), 
                lemmatize_word, 
                self.getLemGreedy())
        self.sentence.setText(sentence_text)

        QCoreApplication.processEvents()

        # Lemmatize word and set word field
        word = re.sub('[«»…,()\\[\\]_]*', "", word)
        if lemmatize_word:
            word = apply_lemmatization(word, self.getLanguage(), self.getLemGreedy())
        self.word.setText(word)

        # Set frequency fields
        freqname = self.settings.value("freq_source", DISABLED)
        if freqname != DISABLED:
            self.setFreq(word)

        # Look up the word's definition and set definition fields

        using_defn2 = self.settings.value("dict_source2") != DISABLED
        defn_dict = self.settings.value("dict_source")
        defn2_dict = self.settings.value("dict_source2")
        def set_definition_or_partial_failure(
            dictname, 
            defn_field: MyTextEdit, 
            defn: Optional[str]):
            if defn:
                self.setDefinitionFieldState(
                    dictname,
                    defn_field,
                    defn
                )
            else:
                self.handlePartialLookupFailure(word, defn_field)

        definition = self.lookup(word, defn_dict)
        self.recordLookupRes(word, lemmatize_word, definition, defn_dict)
        definition2 = None

        if not using_defn2:
            if not definition:
                self.handleCompleteLookupFailure(word, self.definition)
            else: 
                self.setDefinitionFieldState(
                    defn_dict,
                    self.definition,
                    definition
                )
        else:
            definition2 = self.lookup(word, defn2_dict)
            self.recordLookupRes(word, lemmatize_word, definition2, defn2_dict)

            if not definition and not definition2:
                self.handleCompleteLookupFailure(word, self.definition)
                self.handleCompleteLookupFailure(word, self.definition2)
            else:
                set_definition_or_partial_failure(
                    defn_dict,
                    self.definition,
                    definition)
                set_definition_or_partial_failure(
                    defn2_dict,
                    self.definition2,
                    definition2)

        # Set audio field

        QCoreApplication.processEvents()
        self.audio_path = None
        if self.settings.value("audio_dict", "Forvo (all)") != DISABLED:
            try:
                self.audios = getAudio(
                    word,
                    self.settings.value("target_language", 'en'),
                    dictionary=self.settings.value("audio_dict", "Forvo (all)"),
                    custom_dicts=json.loads(
                        self.settings.value("custom_dicts", '[]')))
            except Exception:
                self.audios = {}
            self.audio_selector.clear()
            if len(self.audios) > 0:
                for item in self.audios:
                    self.audio_selector.addItem("🔊 " + item)
                self.audio_selector.setCurrentItem(
                    self.audio_selector.item(0)
                )

    def getLanguage(self):
        return self.settings.value("target_language", "en")
    def getLemGreedy(self):
        return self.settings.value("lem_greedily", False, type=bool)
    def getLemmatize(self):
        return self.settings.value("lemmatization", True, type=bool)

    def setFreq(self, word: str):
        freq_found = False
        freq_display = self.settings.value("freq_display", "Rank")
        freqname = self.settings.value("freq_source")
        lemfreq = self.settings.value("lemfreq", True, type=bool)
        try:
            word_copy = str(word)
            if lemfreq:
                word_copy = apply_lemmatization(
                    word_copy, 
                    self.getLanguage(), 
                    self.getLemGreedy())
            freq, max_freq = getFreq(word_copy, self.getLanguage(), freqname)
            freq_found = True
        except TypeError:
            pass

        if freq_found:
            if freq_display == "Rank":
                self.freq_display.setText(f'{str(freq)}/{str(max_freq)}')
            elif freq_display == "Stars":
                self.freq_display.setText(freq_to_stars(freq, lemfreq))
        else:
            if freq_display == "Rank":
                self.freq_display.setText('-1')
            elif freq_display == "Stars":
                self.freq_display.setText(freq_to_stars(1e6, lemfreq))

    def recordLookupRes(
        self, 
        word: str, 
        word_lemmatized: bool, 
        wordLookupRes: Optional[str], 
        dictname):
        
        if not wordLookupRes:
            self.status("Word not found")

        self.rec.recordLookup(
            word,
            wordLookupRes,
            self.getLanguage(),
            word_lemmatized,
            dictname,
            wordLookupRes != None)

    def lookup(
        self, 
        word: str, 
        dictname: str) -> Optional[str]:
        """
        Call `lookupin()` for @word in @dictname.
        """
        return lookupin(
            word,
            self.getLanguage(),
            dictname,
            self.settings.value("gtrans_lang", "en"),
            self.settings.value("gtrans_api", "https://lingva.ml"))

    def createNote(self):
        sentence = self.sentence.toPlainText().replace("\n", "<br>")
        if self.settings.value("bold_word", True, type=bool):
            sentence = re.sub(
                re_bolded,
                r"<strong>\1</strong>",
                sentence)
        if self.settings.value("remove_spaces", False, type=bool):
            sentence = re.sub("\\s", "", sentence)
        tags = (self.settings.value("tags", "vocabsieve").strip() + " " + self.tags.text().strip()).split(" ")
        word = self.word.text()
        content = {
            "deckName": self.settings.value("deck_name"),
            "modelName": self.settings.value("note_type"),
            "fields": {
                self.settings.value("sentence_field"): sentence,
                self.settings.value("word_field"): word,
            },
            "tags": tags
        }

        def process_def_if_no_lookup_failure(dictname, defn_field: MyTextEdit, anki_field):
            if self.hasLookupFailure(defn_field):
                return None
            else:
                definition = self.process_defi_anki(
                    defn_field,
                    self.settings.value(
                        dictname
                        + "/display_mode",
                        "Markdown-HTML"
                    )
                )
                content['fields'][anki_field] = definition

                return definition

        definition = process_def_if_no_lookup_failure(
            self.settings.value("dict_source", "Wiktionary (English)"),
            self.definition,
            self.settings.value('definition_field'))

        definition2 = None
        if self.settings.value("dict_source2", "Wiktionary (English)") != DISABLED:
            if self.settings.value('definition2_field') == DISABLED:
                self.warn(
                    "Aborted.\nPlease set an anki field for Definition#2 when using two dictionaries.")
                return
            else:
                definition2 = process_def_if_no_lookup_failure(
                    self.settings.value("dict_source2", "Wiktionary (English)"),
                    self.definition,
                    self.settings.value('definition2_field'))

        if self.settings.value(
            "pronunciation_field",
                DISABLED) != DISABLED and self.audio_path:
            content['audio'] = {
                "path": self.audio_path,
                "filename": os.path.basename(self.audio_path),
                "fields": [
                    self.settings.value("pronunciation_field")
                ]
            }
            self.audio_selector.clear()
        if self.settings.value("image_field", DISABLED) != DISABLED and self.image_path:
            content['picture'] = {
                "path": self.image_path,
                "filename": os.path.basename(self.image_path),
                "fields": [
                    self.settings.value("image_field")
                ]
            }

        self.status("Adding note")
        api = self.settings.value("anki_api")
        try:
            if self.settings.value("enable_anki", True, type=bool):
                addNote(api, content)
                self.rec.recordNote(
                    json.dumps(content), 
                    sentence,
                    word,
                    definition,
                    definition2,
                    self.audio_path,
                    self.image_path,
                    " ".join(tags),
                    True
                )
            else:
                self.rec.recordNote(
                    json.dumps(content), 
                    sentence,
                    word,
                    definition,
                    definition2,
                    self.audio_path,
                    self.image_path,
                    " ".join(tags),
                    False
                )
            self.sentence.clear()
            self.word.clear()
            self.definition.clear()
            self.definition2.clear()
            self.status(f"Note added: '{word}'")
        except Exception as e:
            self.rec.recordNote(
                json.dumps(content), 
                sentence,
                word,
                definition,
                definition2,
                self.audio_path,
                self.image_path,
                " ".join(tags),
                False
            )
            self.status(f"Failed to add note: {word}")
            QMessageBox.warning(
                self,
                f"Failed to add note: {word}",
                "<h2>Failed to add note</h2>"
                + f"Reason: {e}"
                + "<br><br>"
                + "AnkiConnect must be running to add notes."
                "<br>If you wish to only add notes to the database (and "
                "export it as CSV), click Configure and uncheck 'Enable"
                " Anki' on the Anki tab."

            )
        self.setImage(None)

    def process_defi_anki(self, w: MyTextEdit, display_mode):
        "Process definitions before sending to Anki"
        if display_mode in ["Raw", "Plaintext"]:
            return w.toPlainText()
        elif display_mode == "Markdown":
            return markdown_nop(w.toPlainText())
        elif display_mode == "Markdown-HTML":
            return markdown_nop(w.toMarkdown())
        elif display_mode == "HTML":
            return w.original

    def errorNoConnection(self, error):
        """
        Dialog window sent when something goes wrong in configuration step
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(
            str(error) +
            "\n\nHints:" +
            "\nAnkiConnect must be running in order to add notes." +
            "\nIf you have AnkiConnect running at an alternative endpoint," +
            "\nbe sure to change it in the configuration.")
        msg.exec()

    def initTimer(self):
        self.showStats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showStats)
        self.timer.start(2000)

    def showStats(self):
        lookups = self.rec.countLookupsToday()
        notes = self.rec.countNotesToday()
        self.stats_label.setText(f"L:{str(lookups)} N:{str(notes)}")

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def status(self, msg):
        self.bar.showMessage(self.time() + " " + msg, 4000)

    def warn(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.exec()

    def startServer(self):
        if self.settings.value("api_enabled", True, type=bool):
            try:
                self.thread = QThread()
                port = self.settings.value("port", 39284, type=int)
                host = self.settings.value("host", "127.0.0.1")
                self.worker = LanguageServer(self, host, port)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.start_api)
                self.worker.note_signal.connect(self.onNoteSignal)
                self.thread.start()
            except Exception as e:
                print(e)
                self.status("Failed to start API server")
        if self.settings.value("reader_enabled", True, type=bool):
            try:
                self.thread2 = QThread()
                port = self.settings.value("reader_port", 39285, type=int)
                host = self.settings.value("reader_host", "127.0.0.1")
                self.worker2 = ReaderServer(self, host, port)
                self.worker2.moveToThread(self.thread2)
                self.thread2.started.connect(self.worker2.start_api)
                self.thread2.start()
            except Exception as e:
                print(e)
                self.status("Failed to start reader server")

    def onNoteSignal(
            self,
            sentence: str,
            word: str,
            definition: str,
            tags: list):
        self.setSentence(sentence)
        self.setWord(word)
        self.definition.setText(definition)
        self.tags.setText(" ".join(tags))
        self.createNote()


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = QLabel(
            '''
© 2022 FreeLanguageTools<br><br>
Visit <a href="https://freelanguagetools.org">FreeLanguageTools.org</a> for more info on how to use this tool.<br>
You can also talk to us on <a href="https://webchat.kde.org/#/room/#flt:midov.pl">Matrix</a>
or <a href="https://t.me/fltchat">Telegram</a> for support.<br><br>

Consult <a href="https://freelanguagetools.org/2021/08/dictionaries-and-frequency-lists-for-ssm/">this link</a>
to find compatible dictionaries. <br><br>

VocabSieve (formerly SSM, ssmtool) is free software available to you under the terms of
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.
If you found a bug, or have enhancement ideas, please open an issue on the
Github <a href=https://github.com/FreeLanguageTools/vocabsieve>repository</a>.<br><br>

This program is yours to keep. There is no EULA you need to agree to.
No data is sent to any server other than the configured dictionary APIs.
Statistics data are stored locally.
<br><br>
Credits: <br><a href="https://en.wiktionary.org/wiki/Wiktionary:Main_Page">Wiktionary API</a><br>
If you find this tool useful, you can give it a star on Github and tell others about it. Any suggestions will also be appreciated.
            '''
        )
        message.setTextFormat(Qt.RichText)
        message.setOpenExternalLinks(True)
        message.setWordWrap(True)
        message.adjustSize()
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


def main():
    app = QApplication(sys.argv)
    w = DictionaryWindow()

    w.show()
    sys.exit(app.exec())
