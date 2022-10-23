from PyQt5.QtCore import QSettings
from functools import lru_cache
from typing import TypedDict, Literal, List, Optional
from enum import Enum, auto

DISABLED = "<disabled>"

# Instead of `SettingsDictKey` we'd like to do something like keyof<SettingsDict>, 
# but that doesn't seem to exist. See https://stackoverflow.com/q/65299047
SettingsDictKey = Literal[
    "target_language",
    "lem_greedily",
    "lemmatization",
    "img_format",
    "img_quality",
    "image_field",
    "pronunciation_field",
    "audio_dict",
    "custom_dicts",
    "freq_source",
    "freq_display",
    "lemfreq",
    "orientation"]
AnkiField = str

class SettingsDict(TypedDict):
    target_language: str
    lem_greedily: bool
    lemmatization: bool
    img_format: str
    img_quality: int
    audio_dict: str
    custom_dicts: str
    freq_source: str
    freq_display: str
    lemfreq: bool
    orientation: str

    config_ver: Optional[int]
    dict_source: str
    dict_source2: str
    gtrans_lang: str
    custom_url: str

    enable_anki: bool
    deck_name: str
    note_type: str
    tags: str
    sentence_field: str
    word_field: str
    frequency_field: str
    definition_field: str
    definition2_field: str
    pronunciation_field: str
    image_field: str
    anki_api: str
    allow_editing: bool

    check_updates: bool
    bold_word: bool
    web_preset: str
    api_enabled: bool
    api_host: str
    api_port: int
    reader_hlcolor: str
    reader_enabled: bool
    reader_host: str
    reader_port: int
    gtrans_api: str
    reader_font: str
    reader_fontsize: int
    freq_display: str
    allow_editing: bool
    primary: bool
    text_scale: int
    img_format: str

class _Settings(QSettings):
    def __init__(self, defaultSettings: SettingsDict):
        super().__init__()
        self.defaultSettings = defaultSettings
        self.setDefaults(self.defaultSettings)

    def setDefaults(self, defaultSettings: SettingsDict):
        def defineIfNotSet(k: str, v: object):
            if not self.contains(k):
                self.setValue(k, v)

        for t in defaultSettings.items():
            defineIfNotSet(*t)

    def get(self, k: SettingsDictKey):
        return self.value(
            k, 
            defaultValue=self.defaultSettings[k], 
            type=type(self.defaultSettings[k])
        )

default_settings: SettingsDict = {
    "target_language": "en",
    "lem_greedily": False,
    "lemmatization": True,
    "img_format": "jpg",
    "img_quality": -1,
    "image_field": DISABLED,
    "pronunciation_field": DISABLED,
    "audio_dict": "Forvo (all)",
    "custom_dicts": '[]',
    "freq_source": DISABLED,
    "freq_display": "Rank",
    "lemfreq": True,
    "orientation": "VERTICAL",

    "reader_hlcolor": "#66bb77",
    "config_ver": None,
    'dict_source': 'Wiktionary (English)',
    'dict_source2': DISABLED,
    "gtrans_lang": "en",
    "custom_url": "https://en.wiktionary.org/wiki/@@@@",
    "deck_name": "Default",
    "note_type": "Basic",
    "tags": "vocabsieve",

    "sentence_field": "Sentence",
    "word_field": "Word",
    "frequency_field": "Frequency Stars",
    "definition_field": "Definition",
    "definition2_field": DISABLED,
    "pronunciation_field": DISABLED,
    "image_field": DISABLED,

    'anki_api': 'http://127.0.0.1:8765',
    'enable_anki': True,
    "allow_editing": True,
    'check_updates': False,
    'bold_word': True,
    'web_preset': 'English Wiktionary',
    'api_enabled': True,
    'api_host': '127.0.0.1',
    'api_port': 39284,
    'reader_enabled': True,
    'reader_host': '127.0.0.1',
    'reader_port': 39285,
    'gtrans_api': 'https://lingva.ml',
        "reader_font": "serif",
        "reader_fontsize": 14,
        "freq_display": "Stars (like Migaku)",
        'allow_editing': True,
        'primary': False,
        'text_scale': 100,
        'img_format': 'jpg',
        'img_quality': -1,
    }

def get_nested_setting_key(nest: str, key: str):
    return f"{nest}/{key}"
def set_per_dict_values(settings_dict: SettingsDict, dict_key: str):
    settings_dict[get_nested_setting_key(dict_key, "display_mode")] = "Markdown-HTML"
    settings_dict[get_nested_setting_key(dict_key, "skip_top")] = 0
    settings_dict[get_nested_setting_key(dict_key, "collapse_newlines")] = 0
    settings_dict[get_nested_setting_key(dict_key, "cleanup_html")] = False
set_per_dict_values(default_settings, default_settings["dict_source"])

settings = _Settings(default_settings)