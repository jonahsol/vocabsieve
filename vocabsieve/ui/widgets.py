import platform
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from typing import Callable
from ui.about_dialog import AboutDialog
from ui.menu_bar import MenuBar
from dictionary.funcs import *
from db import *
from dictionary.dictionary import *
from funcs.text_manipulation import *
from constants import *
from ui.searchable_text_edit import *
from app_text import *
from settings import settings
from ui.settings_dialog import SettingsDialog
from ui.status_bar import StatusBar

# If on macOS, display the modifier key as "Cmd", else display it as "Ctrl".
# For whatever reason, Qt automatically uses Cmd key when Ctrl is specified on Mac
# so there is no need to change the keybind, only the display text
if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"

class Widgets():
    def __init__(
        self,
        on_close_app: Callable):

        self.centralWidget = QWidget()

        self.statusBar = StatusBar()
        self.stats_label = QLabel()
        self.statusBar.addPermanentWidget(self.stats_label)

        self.settingsDialog = SettingsDialog(
            status = self.status, 
            on_close_app=on_close_app)
        self.aboutDialog = AboutDialog()
        self.menuBar = MenuBar()
        self.namelabel = QLabel(
            "<h2 style=\"font-weight: normal;\">" + app_title + "</h2>")

        self.sentence = SearchableTextEdit(FieldName.SENTENCE)
        self.sentence.setPlaceholderText(
            "Sentence copied to the clipboard will show up here.")
        self.sentence.setMinimumHeight(50)
        #self.sentence.setMaximumHeight(300)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Word will appear here when looked up.")
        self.definition = SearchableLoadableTextEdit(
            name=FieldName.DEFINITION,
            loadingText=lookup_loading,
            placeholderText=lookup_placeholder)
        self.definition.setMinimumHeight(70)
        #self.definition.setMaximumHeight(1800)
        self.definition2 = SearchableLoadableTextEdit(
            name=FieldName.DEFINITION2,
            loadingText=lookup_loading,
            placeholderText=lookup_placeholder)
        self.definition2.setMinimumHeight(70)
        #self.definition2.setMaximumHeight(1800)
        
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(
            "Type in a list of tags to be used, separated by spaces (same as in Anki).")
        self.sentence.setToolTip(lookup_tooltip)

        self.lookup_button = QPushButton(f"Define [{MOD}-D]")
        self.lookup_exact_button = QPushButton(f"Define Direct [Shift-{MOD}-D]")
        self.lookup_exact_button.setToolTip(
            "This will look up the word without lemmatization.")
        self.toanki_button = QPushButton(f"Add note [{MOD}-S]")

        self.config_button = QPushButton("Configure..")
        self.read_button = QPushButton(f"Read clipboard [{MOD}-V]")

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

        self.definition.setReadOnly(
            not (
                settings.value(
                    "allow_editing",
                    True,
                    type=bool)))
        self.definition2.setReadOnly(
            not (
                settings.value(
                    "allow_editing",
                    True,
                    type=bool)))

        self.image_viewer = QLabel("<center><b>&lt;No image selected&gt;</center>")
        self.image_viewer.setScaledContents(True)
        self.image_viewer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_viewer.setStyleSheet(
            '''
                border: 1px solid black;
            '''
        )

    def status(self, msg):
        self.statusBar.status(msg)

