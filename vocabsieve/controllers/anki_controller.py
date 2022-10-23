from PyQt5.QtWidgets import QMessageBox
from ui.widgets import *
from ui.searchable_text_edit import *
from dictionary.dictionary import *
from settings import *
from funcs.text_manipulation import *
from ui.warn import *
from controllers.state import *
from anki_connect import *

class AnkiController():
    def __init__(self, widgets: Widgets):
        self.widgets = widgets
        self.state = State(widgets)

    def process_defi_anki(self, w: SearchableTextEdit, display_mode):
        "Process definitions before sending to Anki"
        if display_mode in ["Raw", "Plaintext"]:
            return w.toPlainText()
        elif display_mode == "Markdown":
            return markdown_nop(w.toPlainText())
        elif display_mode == "Markdown-HTML":
            return markdown_nop(w.toMarkdown())
        elif display_mode == "HTML":
            return w.original

    def createNote(self):
        sentence = self.widgets.sentence.toPlainText().replace("\n", "<br>")
        if settings.value("bold_word", True, type=bool):
            sentence = re.sub(
                re_bolded,
                r"<strong>\1</strong>",
                sentence)
        if settings.value("remove_spaces", False, type=bool):
            sentence = re.sub("\\s", "", sentence)
        tags = (settings.value("tags", "vocabsieve").strip() + " " + self.widgets.tags.text().strip()).split(" ")
        word = self.widgets.word.text()
        content = {
            "deckName": settings.value("deck_name"),
            "modelName": settings.value("note_type"),
            "fields": {
                settings.value("sentence_field"): sentence,
                settings.value("word_field"): word,
            },
            "tags": tags
        }

        def process_def_if_no_lookup_failure(dictname, defn_field: SearchableTextEdit, anki_field):
            if self.state.hasLookupFailure(defn_field):
                return None
            else:
                definition = self.process_defi_anki(
                    defn_field,
                    settings.value(
                        dictname
                        + "/display_mode",
                        "Markdown-HTML"
                    )
                )
                content['fields'][anki_field] = definition

                return definition

        definition = process_def_if_no_lookup_failure(
            settings.value("dict_source", "Wiktionary (English)"),
            self.widgets.definition,
            settings.value('definition_field'))

        definition2 = None
        if settings.value("dict_source2", "Wiktionary (English)") != DISABLED:
            if settings.value('definition2_field') == DISABLED:
                warn(
                    "Aborted.\nPlease set an anki field for Definition#2 when using two dictionaries.")
                return
            else:
                definition2 = process_def_if_no_lookup_failure(
                    settings.value("dict_source2", "Wiktionary (English)"),
                    self.widgets.definition,
                    settings.value('definition2_field'))

        if settings.get(
            "pronunciation_field") != DISABLED and self.state.audio_path:
            content['audio'] = {
                "path": self.state.audio_path,
                "filename": os.path.basename(self.state.audio_path),
                "fields": [
                    settings.value("pronunciation_field")
                ]
            }
            self.widgets.audio_selector.clear()

        if settings.get("image_field") != DISABLED and self.state.image_path:
            content['picture'] = {
                "path": self.state.image_path,
                "filename": os.path.basename(self.state.image_path),
                "fields": [
                    settings.get("image_field")
                ]
            }

        self.widgets.status("Adding note")
        api = settings.value("anki_api")
        try:
            if settings.value("enable_anki", True, type=bool):
                addNote(api, content)
                rec.recordNote(
                    json.dumps(content), 
                    sentence,
                    word,
                    definition,
                    definition2,
                    self.state.audio_path,
                    self.state.image_path,
                    " ".join(tags),
                    True
                )
            else:
                rec.recordNote(
                    json.dumps(content), 
                    sentence,
                    word,
                    definition,
                    definition2,
                    self.state.audio_path,
                    self.state.image_path,
                    " ".join(tags),
                    False
                )
            self.widgets.status(f"Note added: '{word}'")
        except Exception as e:
            rec.recordNote(
                json.dumps(content), 
                sentence,
                word,
                definition,
                definition2,
                self.state.audio_path,
                self.state.image_path,
                " ".join(tags),
                False
            )
            self.widgets.status(f"Failed to add note: {word}")
            warn(
                f"Failed to add note: {word}"
                + "<h2>Failed to add note</h2>"
                + f"Reason: {e}"
                + "<br><br>"
                + "AnkiConnect must be running to add notes."
                "<br>If you wish to only add notes to the database (and "
                "export it as CSV), click Configure and uncheck 'Enable"
                " Anki' on the Anki tab."
            )

        self.state.resetState()