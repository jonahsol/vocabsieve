from PyQt5.Qt import QDesktopServices, QUrl
import re
from ui.searchable_text_edit import *
from ui.widgets import *
from dictionary.dictionary import *
from settings import *
from funcs.define_word_json import *
from funcs.errors import *
from controllers.lookup_controller import *
from controllers.anki_controller import *
from controllers.state import *

class Controller():
    def __init__(self, widgets: Widgets):
        self.widgets = widgets
        self.lookupController = LookupController(widgets)
        self.ankiController = AnkiController(widgets)
        self.state = State(widgets)

        # State
        self.rawWordLookup = None
        self.selectedText = None

    def handleClipboardSelection(self, text):
        if ((def_word_json := parse_define_word_json(text)) != None):
            sentence = def_word_json["sentence"]
            word = re.sub('[\\?\\.!«»…()\\[\\]]*', "", def_word_json["word"])
            self.state.setSentence(sentence)
            self.lookupController.lookupAndUpdateState(word)
        elif self.widgets.single_word.isChecked() and is_oneword(text):
            self.state.setSentence(text)
            self.lookupController.lookupAndUpdateState(text)
        else:
            self.state.setSentence(text)

    def onHelp(self):
        url = f"https://wiki.freelanguagetools.org/vocabsieve_setup"
        QDesktopServices.openUrl(QUrl(url))
    def onAbout(self):
        self.widgets.aboutDialog.exec_()
    def onWebButton(self):
        url = settings.value("custom_url",
                                  "https://en.wiktionary.org/wiki/@@@@").replace(
            "@@@@", self.widgets.word.text()
        )
        QDesktopServices.openUrl(QUrl(url))
    def onReaderOpen(self):
        url = f"http://{settings.value('reader_host', '127.0.0.1', type=str)}:{settings.value('reader_port', '39285', type=str)}"
        QDesktopServices.openUrl(QUrl(url))

    def handleSearchableMousePress(self, defn_field: SearchableTextEdit):
        # Check if `completeLookupFailureBlock` was clicked
        if (defn_field.completeLookupFailureBlock and
            defn_field.completeLookupFailureBlock == defn_field.textCursor().block()):
            self.lookupController.clearCompleteFailure(defn_field)

        # Check if `partialFailureBlock` was clicked
        elif (defn_field.partialLookupFailureBlock and
              defn_field.partialLookupFailureBlock == defn_field.textCursor().block()):
            self.lookupController.clearPartialFailure(defn_field)

    def handleSearchableSelectionChanged(self, field: SearchableTextEdit):
        self.selectedText = getSelectedText(field)

    def handleSearchableDoubledClicked(self, field: SearchableTextEdit):
        assert self.selectedText != None, """
            `self.selectedText` should have be defined by 
            `handleSearchableSelectionChanged` prior to entry into 
            `handleSearchableDoubledClicked`."""

        self.lookupController.lookupAndUpdateState(self.selectedText)

    def lookupCurrentSelectionOrPrevWord(self, use_lemmatize: bool):
        if hasattr(self, "selectedText") and self.selectedText != None:
            self.lookupController.lookupAndUpdateState(self.selectedText, use_lemmatize)
        elif self.rawWordLookup != None: 
            self.lookupController.lookupAndUpdateState(self.rawWordLookup, use_lemmatize)