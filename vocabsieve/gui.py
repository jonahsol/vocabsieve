from PyQt5.QtGui import QTextCursor, QTextCharFormat, QCursor
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QCursor

# dict_window: DictionaryWindow
# word: str
def append_failed_lookup_blocks(dict_window, word):

    settings = dict_window.settings
    def_doc = dict_window.definition.document()
    def_cursor = QTextCursor(def_doc)

    def_doc.clear()

    # First block
    def_cursor.insertHtml("<b>Definition for \"" + str(word) + "\" not found.</b><br>") 

    # Second block
    def_cursor.insertBlock() 
    def_cursor.insertHtml("<u style='color: #599fe6;'>Want to add a note anyway?</u><br>") 
    clear_text_block = def_cursor.block()

    # Final block
    def_cursor.insertBlock() 
    def_cursor.insertHtml(
        "Check the following:<br>" +
        "- Language setting (Current: " + settings.value("target_language", 'en') + ")<br>" +
        "- Is the correct word being looked up?<br>" +
        "- Are you connected to the Internet?<br>" +
        "Otherwise, then " + settings.value("dict_source", "Wiktionary (English)") +
        " probably just does not have this word listed.")

    return clear_text_block

def remove_failed_lookup_blocks(dict_window):
    dict_window.definition.clear()
    reset_text_cursor_format(dict_window.definition)

# textEdit: QTextEdit
def reset_text_cursor_format(textEdit):
    cursor = textEdit.textCursor()
    cursor.setCharFormat(QTextCharFormat())
    textEdit.setTextCursor(
        cursor
    )

