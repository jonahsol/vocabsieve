from optparse import Option
from PyQt5.QtCore import QCoreApplication
from ui.widgets import *
from ui.searchable_text_edit import *
from settings import *
from ui.lookup_failure import *
from funcs.text_manipulation import *
from dictionary.dictionary import *
from controllers.freq_controller import *
from controllers.word_audio_controller import *
from controllers.state import *
from qt_threading.worker import *
from db import *

class LookupController():
    rawWordLookup = None

    def __init__(self, widgets: Widgets):
        self.widgets = widgets
        self.freqController = FreqController(widgets)
        self.wordAudioController = WordAudioController(widgets)
        self.state = State(widgets)

    def setPartialLookupFailure(self, word, defn_field):
        defn_field.partialLookupFailureBlock = \
            set_partial_lookup_failure(word, defn_field, settings)
        defn_field.completeLookupFailureBlock = None

    def setCompleteLookupFailure(self, word, defn_field):
        defn_field.completeLookupFailureBlock = \
            set_complete_lookup_failure(word, defn_field, settings)
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
        self.state.updateAnkiButtonState(True)

    def getOtherDefField(self, field: SearchableTextEdit):
        if (field.name == FieldName.DEFINITION):
            return self.widgets.definition2
        if (field.name == FieldName.DEFINITION2):
            return self.widgets.definition

    def clearAllLookupFailures(self):
        def clearLookupFailures(defn_field):
            if (defn_field.partialLookupFailureBlock
                or defn_field.completeLookupFailureBlock):
                reset_text_edit(defn_field)

            defn_field.completeLookupFailureBlock = None
            defn_field.partialLookupFailureBlock = None

        clearLookupFailures(self.widgets.definition)
        clearLookupFailures(self.widgets.definition2)

    def clearCompleteFailure(self, defn_field: SearchableTextEdit):
        self.state.updateAnkiButtonState(False)

        self.clearPartialFailure(defn_field)
        defn_field.completeLookupFailureBlock = None

        other_defn_field = self.getOtherDefField(defn_field)
        self.setPartialLookupFailure(self.state.getWord(), other_defn_field)

    def clearPartialFailure(self, defn_field: SearchableTextEdit):
        reset_text_edit(defn_field)
        defn_field.setReadOnly(False)
        defn_field.partialLookupFailureBlock = None

    def lookupAndUpdateState(self, word: str, use_lemmatize=True):
        """ Lookup @word and modify GUI state accordingly.
        """
        lemmatize_word = use_lemmatize and settings.get("lemmatization")

        # word was just looked up
        if word == self.rawWordLookup:
            return

        # Save the unlemmatized word so that it can be used by `lookup_exact_button`
        self.rawWordLookup = word
        # Clear any lookup failures from the last lookup
        self.clearAllLookupFailures()
        
        # Bold text
        sentence_text = self.widgets.sentence.toPlainText()
        if settings.value("bold_word", True, type=bool):
            without_bold = remove_bold(sentence_text)
            sentence_text = bold_word_in_text(
                word, 
                without_bold, 
                settings.get("target_language"), 
                lemmatize_word, 
                settings.get("lem_greedily"))
        self.widgets.sentence.setText(sentence_text)

        # Lemmatize word and set word field
        word = re.sub('[«»…,()\\[\\]_]*', "", word)
        if lemmatize_word:
            word = apply_lemmatization(word, settings.get("target_language"), settings.get("lem_greedily"))
        self.widgets.word.setText(word)

        # Look up the word's definition and set definition fields

        using_defn2 = settings.value("dict_source2") != DISABLED
        defn_dict = settings.value("dict_source")
        defn2_dict = settings.value("dict_source2")
        def set_definition_or_partial_failure(
            dictname, 
            defn_field: SearchableTextEdit, 
            defn: Optional[str]):
            if defn:
                self.setDefinitionFieldState(
                    dictname,
                    defn_field,
                    defn
                )
            else:
                self.handlePartialLookupFailure(word, defn_field)

        # SOMEDAY Lookups could be run asynchronously
        def perform_lookups():
            definition = self.lookup(word, defn_dict)
            definition2 = None
            if using_defn2:
                definition2 = self.lookup(word, defn2_dict)

            return (definition, definition2)

        def receive_lookups(definition: str, definition2: Optional[str]):
            self.recordLookupRes(word, lemmatize_word, definition, defn_dict)

            if not using_defn2:
                if not definition:
                    self.handleCompleteLookupFailure(word, self.widgets.definition)
                else: 
                    self.setDefinitionFieldState(
                        defn_dict,
                        self.widgets.definition,
                        definition
                    )
            else:
                self.recordLookupRes(word, lemmatize_word, definition2, defn2_dict)

                if not definition and not definition2:
                    self.handleCompleteLookupFailure(word, self.widgets.definition)
                    self.handleCompleteLookupFailure(word, self.widgets.definition2)
                else:
                    set_definition_or_partial_failure(
                        defn_dict,
                        self.widgets.definition,
                        definition)
                    set_definition_or_partial_failure(
                        defn2_dict,
                        self.widgets.definition2,
                        definition2)

        def toggle_lookups_loading(loading: bool):
            self.widgets.definition.setLoading(loading)
            if using_defn2:
                self.widgets.definition2.setLoading(loading)

        QThreadPool.globalInstance().start(
            Worker(
                perform_lookups, 
                result_slot=lambda t: receive_lookups(*t),
                start_slot=lambda: toggle_lookups_loading(True),
                finished_slot=lambda: toggle_lookups_loading(False)))

        self.wordAudioController.lookupAndUpdateState(word)
        self.freqController.lookupAndUpdateState(word)

    def lookup(
        self, 
        word: str, 
        dictname: str) -> Optional[str]:
        """
        Call `lookupin()` for @word in @dictname.
        """
        return lookupin(
            word,
            settings.get("target_language"),
            dictname,
            settings.get("gtrans_lang"),
            settings.get("gtrans_api"))

    def setDefinitionFieldState(self, dictname, defn_field: SearchableTextEdit, value: str):
        defn_field.original = value.strip()

        display_mode = settings.value(
            dictname + "/display_mode",
            "Markdown-HTML"
        )
        skip_top = settings.value(
            dictname + "/skip_top",
            0, type=int
        )
        collapse_newlines = settings.value(
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

    def recordLookupRes(
        self, 
        word: str, 
        word_lemmatized: bool, 
        wordLookupRes: Optional[str], 
        dictname):
        
        if not wordLookupRes:
            self.widgets.status("Word not found")

        rec.recordLookup(
            word,
            wordLookupRes,
            settings.get("target_language"),
            word_lemmatized,
            dictname,
            wordLookupRes != None)
