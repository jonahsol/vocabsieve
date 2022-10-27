from email.mime import audio
from controllers.state import State
from ui.widgets import *
from settings import *
from dictionary.dictionary import get_audio
import json
from funcs.errors import pass_exceptions
from app_threading import *

class WordAudioController():
    def __init__(self, widgets: Widgets):
        self.state = State(widgets)

    def lookupAndUpdateState(self, word):
        if settings.get("audio_dict") != DISABLED:
            QThreadPool.globalInstance().start(
                Worker(
                    pass_exceptions(lambda: get_audio(
                        word,
                        settings.get("target_language"),
                        dictionary=settings.get("audio_dict"),
                        custom_dicts=json.loads(settings.get("custom_dicts")))),
                    self.state.setAudios
                ))

    def selectAudio(self, audio_key):
        assert self.state.audio_options != None
        if audio_key in self.state.audio_options:
            self.state.audio_path = self.state.audio_options[audio_key]