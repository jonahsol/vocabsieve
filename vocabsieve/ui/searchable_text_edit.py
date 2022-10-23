from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QCursor
from enum import Enum, unique, auto
from typing import Optional

@unique
class FieldName(Enum):
    SENTENCE = auto()
    DEFINITION = auto()
    DEFINITION2 = auto()

class SearchableTextEdit(QTextEdit):
    def __init__(self, name: FieldName):
        super().__init__()
        self.name = name
        self.partialLookupFailureBlock = None
        self.completeLookupFailureBlock = None
    
    @pyqtSlot()
    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        self.textCursor().clearSelection()
        self.original = ""

    @pyqtSlot()
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        
    @pyqtSlot()
    def handleSelectionChanged(self):
        pass

def reset_text_edit(text_edit: QTextEdit):
    text_edit.clear()
    _reset_text_cursor_format(text_edit)

# textEdit: QTextEdit
def _reset_text_cursor_format(text_edit: QTextEdit):
    cursor = text_edit.textCursor()
    cursor.setCharFormat(QTextCharFormat())
    text_edit.setTextCursor(
        cursor
    )

def getSelectedText(text_edit: QTextEdit) -> Optional[str]:
    selected = text_edit.textCursor().selectedText()
    text = str.strip(selected)

    return None if text == "" else text
