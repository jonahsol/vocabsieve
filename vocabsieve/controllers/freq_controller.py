from optparse import Option
from ui.widgets import *
from settings import *
from dictionary.dictionary import apply_lemmatization, getFreq
from app_threading import *
from typing import Tuple

class FreqController():
    def __init__(self, widgets: Widgets):
        self.widgets = widgets

    def lookupAndUpdateState(self, word: str):
        freqname = settings.get("freq_source")
        if freqname == DISABLED:
            return

        freq_display = settings.get("freq_display")
        lemfreq = settings.get("lemfreq")

        def perform_lookup() -> Optional[Tuple[int, int]]:
            try:
                word_copy = str(word)
                if lemfreq:
                    word_copy = apply_lemmatization(
                        word_copy, 
                        settings.get("target_language"), 
                        settings.get("lem_greedily"))
                return getFreq(word_copy, settings.get("target_language"), freqname)
            except TypeError:
                pass

        def receive_lookup(lookup_res: Optional[Tuple[int, int]]):
            if lookup_res != None:
                freq, max_freq = lookup_res
                if freq_display == "Rank":
                    self.widgets.freq_display.setText(f'{str(freq)}/{str(max_freq)}')
                elif freq_display == "Stars":
                    self.widgets.freq_display.setText(freq_to_stars(freq, lemfreq))
            else:
                if freq_display == "Rank":
                    self.widgets.freq_display.setText('-1')
                elif freq_display == "Stars":
                    self.widgets.freq_display.setText(freq_to_stars(1e6, lemfreq))
        
        QThreadPool.globalInstance().start(Worker(perform_lookup, receive_lookup))


def freq_to_stars(freq_num, lemmatize):
    if lemmatize:
        if freq_num <= 1000:
            return "★★★★★"
        elif freq_num <= 3000:
            return "★★★★☆"
        elif freq_num <= 8000:
            return "★★★☆☆"
        elif freq_num <= 20000:
            return "★★☆☆☆"
        elif freq_num <= 40000:
            return "★☆☆☆☆"
        else:
            return "☆☆☆☆☆"
    else:
        if freq_num <= 1500:
            return "★★★★★"
        elif freq_num <= 5000:
            return "★★★★☆"
        elif freq_num <= 15000:
            return "★★★☆☆"
        elif freq_num <= 30000:
            return "★★☆☆☆"
        elif freq_num <= 60000:
            return "★☆☆☆☆"
        else:
            return "☆☆☆☆☆"