from PyQt5.QtGui import QTextCursor, QTextCharFormat, QCursor
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QTextEdit
from typing import Optional

def set_complete_lookup_failure(word, defn_field, settings):
    def create_clear_text_block(cursor):
        cursor.insertBlock() 
        cursor.insertHtml("<u style='color: #599fe6;'>Want to add a note anyway?</u><br>") 
        return cursor.block()

    return _set_lookup_failure(defn_field, word, settings, create_clear_text_block)

def set_partial_lookup_failure(word, defn_field, settings):
    def create_clear_text_block(cursor):
        cursor.insertBlock() 
        cursor.insertHtml("<u style='color: #599fe6;'>Want to write something anyway?</u><br>") 
        return cursor.block()

    return _set_lookup_failure(defn_field, word, settings, create_clear_text_block)

def _set_lookup_failure(defn_field, word, settings, create_clear_text_block):
    doc = defn_field.document()
    cursor = QTextCursor(doc)

    doc.clear()
    
    # First block
    cursor.insertHtml("<b>Definition for \"" + str(word) + "\" not found.</b><br>") 
    # Parameter block
    clear_text_block = create_clear_text_block(cursor)
    # Final block
    cursor.insertBlock() 
    cursor.insertHtml(
        "Check the following:<br>" +
        "- Language setting (Current: " + settings.value("target_language", 'en') + ")<br>" +
        "- Is the correct word being looked up?<br>" +
        "- Are you connected to the Internet?<br>" +
        "Otherwise, then " + settings.value("dict_source", "Wiktionary (English)") +
        " probably just does not have this word listed.")

    return clear_text_block

def reset_text_edit(text_edit):
    text_edit.clear()
    _reset_text_cursor_format(text_edit)

# textEdit: QTextEdit
def _reset_text_cursor_format(text_edit):
    cursor = text_edit.textCursor()
    cursor.setCharFormat(QTextCharFormat())
    text_edit.setTextCursor(
        cursor
    )

def getSelectedText(text_edit: QTextEdit) -> Optional[str]:
    selected = text_edit.textCursor().selectedText()
    text = str.strip(selected)

    return None if text == "" else text

