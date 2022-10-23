from email.mime import audio
from controllers.state import State
from ui.widgets import *
from settings import *
from dictionary.dictionary import getAudio
import json
from funcs.errors import raise_bad_path_exception

class WordAudioController():
    def __init__(self, widgets: Widgets):
        self.state = State(widgets)

    def lookupAndUpdateState(self, word):
        if settings.get("audio_dict") != DISABLED:
            try:
                self.state.setAudios(
                    getAudio(
                        word,
                        settings.get("target_language"),
                        dictionary=settings.get("audio_dict"),
                        custom_dicts=json.loads(settings.get("custom_dicts"))))
            except Exception:
                pass

    def selectAudio(self, audio_key):
        if self.state.audio_options != None \
            and hasattr(self.state.audio_options, audio_key):
            self.state.audio_path = self.state.audio_options[audio_key]
        else:
            raise_bad_path_exception()