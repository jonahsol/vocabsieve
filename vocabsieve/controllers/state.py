from functools import lru_cache
from PyQt5.QtGui import QPixmap
from typing import Optional, Dict
import time
from os import path
from ui.widgets import *
from settings import *
from data.datapath import *
from ui.searchable_text_edit import *

images_path = get_data_abs_path("images")
mk_data_dir(images_path)
get_image_dir = lambda img_fl_name: path.join(images_path, img_fl_name)

@lru_cache(maxsize=1)
class State():
    def __init__(self, widgets: Widgets):
        self.widgets = widgets
        self.image_path: Optional[str] = None
        self.audio_path: Optional[str] = None 
        self.audio_options: Optional[Dict[str, str]] = None 

    def hasLookupFailure(self, defn_field: SearchableTextEdit):
        return defn_field.partialLookupFailureBlock \
                or defn_field.completeLookupFailureBlock

    def getWord(self):
        return self.widgets.word.text()

    def updateAnkiButtonState(self, forceDisable=False):
        if self.widgets.sentence.toPlainText() == "" or forceDisable:
            self.widgets.toanki_button.setEnabled(False)
        else:
            self.widgets.toanki_button.setEnabled(True)

    def setSentence(self, text):
        self.widgets.sentence.setText(str.strip(text))

    def setWord(self, text):
        self.widgets.word.setText(str.strip(text))

    def setImage(self, content: Optional[QPixmap]):
        if content == None:
            self.widgets.image_viewer.setPixmap(QPixmap())
            self.widgets.image_viewer.setText("<center><b>&lt;No image selected&gt;</center>")
            self.image_path = None
            return

        filename = str(int(time.time()*1000)) + '.' + settings.get("img_format")
        self.image_path = get_image_dir(filename)
        content.save(
            self.image_path, quality=settings.get("img_quality")
        )
        self.widgets.image_viewer.setPixmap(content)

    def setAudios(self, audios: Optional[Dict[str, str]]):
        if audios == None:
            self.widgets.audio_selector.clear()
            self.audio_options = audios
            self.audio_path = None
        elif len(audios) > 0:
            self.audio_options = audios
            for item in audios:
                self.widgets.audio_selector.addItem("🔊 " + item)
            self.widgets.audio_selector.setCurrentItem(
                self.widgets.audio_selector.item(0)
            )

    def reset(self):
        self.widgets.sentence.clear()
        self.widgets.word.clear()
        self.widgets.definition.clear()
        self.widgets.definition2.clear()
        self.setImage(None)
        self.setAudios(None)
