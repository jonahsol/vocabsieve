#!/usr/bin/env python3
import sys


class dummyStream:
    ''' dummyStream behaves like a stream but does nothing. '''

    def __init__(self): pass
    def write(self, data): pass
    def read(self, data): pass
    def flush(self): pass
    def close(self): pass


# redirect all streams to dummy to stop error on stdout
sys.stdout = dummyStream()
sys.stderr = dummyStream()
sys.stdin = dummyStream()
sys.__stdout__ = dummyStream()
sys.__stderr__ = dummyStream()
sys.__stdin__ = dummyStream()
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VocabSieve")
    app.setOrganizationName("FreeLanguageTools")
    from vocabsieve.main import AppWindow
    w = AppWindow()
    w.show()
    sys.exit(app.exec())
