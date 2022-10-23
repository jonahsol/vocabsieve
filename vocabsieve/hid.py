from PyQt5.QtWidgets import QShortcut, QMainWindow, QApplication
from PyQt5.QtGui import QKeySequence, QClipboard
from settings import *
from controllers.controller import *
from ui.searchable_text_edit import *
from ui.widgets import *

def applyToMany(*fs):
    def apply(*xs):
        [f() if f.__code__.co_argcount == 0 else f(*xs) for f in fs]

    return apply

class HID():
    def __init__(
        self, 
        app_window: QMainWindow, 
        controller: Controller,
        widgets: Widgets):

        self.app_window = app_window
        self.controller = controller
        self.widgets = widgets

        self.connectHotkeys()
        self.connectClipboard()
        self.connectButtonHandlers()
        self.connectMenuBar()
        self.connectSearchableHandlers()

    def connectMenuBar(self):
        self.widgets.menuBar.actionsDict["about"].triggered.connect(self.controller.onAbout)
        self.widgets.menuBar.actionsDict["help"].triggered.connect(self.controller.onHelp)
        self.widgets.menuBar.actionsDict["open_reader"].triggered.connect(self.controller.onReaderOpen)
        # self.widgets.menuBar.actions.import_koreader.triggered.connect(self.controller.importkoreader)
        # self.widgets.menuBar.actions.import_kindle.triggered.connect(self.controller.importkindle)
        # self.widgets.menuBar.actions.export_notes_csv.triggered.connect(self.controller.exportNotes)
        # self.widgets.menuBar.actions.export_lookups_csv.triggered.connect(self.controller.exportLookups)

    def connectHotkeys(self):
        QShortcut(QKeySequence('Ctrl+S'), self.app_window) \
            .activated.connect(self.widgets.toanki_button.animateClick)
        QShortcut(QKeySequence('Ctrl+Shift+D'), self.app_window) \
            .activated.connect(self.widgets.lookup_exact_button.animateClick)
        QShortcut(QKeySequence('Ctrl+D'), self.app_window) \
            .activated.connect(self.widgets.lookup_button.animateClick)
        QShortcut(QKeySequence('Ctrl+V'), self.app_window) \
            .activated.connect(self.widgets.read_button.animateClick)
        QShortcut(QKeySequence('Ctrl+1'), self.app_window) \
            .activated.connect(self.widgets.web_button.animateClick)

    def connectButtonHandlers(self):
        self.widgets.lookup_button.clicked.connect(
            lambda: self.controller.lookupCurrentSelectionOrPrevWord(True))
        self.widgets.lookup_exact_button.clicked.connect(
            lambda: self.controller.lookupCurrentSelectionOrPrevWord(False))

        self.widgets.web_button.clicked.connect(self.controller.onWebButton)

        self.widgets.config_button.clicked.connect(self.widgets.settingsDialog.exec)
        self.widgets.toanki_button.clicked.connect(self.controller.ankiController.createNote)
        self.widgets.read_button.clicked.connect(lambda: self.readClipboard(True))

    def connectFields(self):
        self.widgets.sentence.textChanged.connect(self.controller.state.updateAnkiButtonState)
        # self.widgets.audio_selector.connect(self.controller.state.updateAnkiButtonState)

    def connectSearchableHandlers(self):
        def connect_slot_handlers(searchable_text_edit: SearchableTextEdit):
            setattr(
                searchable_text_edit, 
                "mouseDoubleClickEvent",
                applyToMany(
                    searchable_text_edit.mouseDoubleClickEvent,
                    lambda: self.controller.handleSearchableDoubledClicked(searchable_text_edit)
                ))
            setattr(
                searchable_text_edit, 
                "mousePressEvent",
                applyToMany(
                    searchable_text_edit.mousePressEvent,
                    lambda: self.controller.handleSearchableMousePress(searchable_text_edit)
                ))

        def connect_selection_changed_handler(searchable_text_edit: SearchableTextEdit):
            searchable_text_edit.selectionChanged.connect(
                lambda: self.controller.handleSearchableSelectionChanged(searchable_text_edit)
            )

        connect_selection_changed_handler(self.widgets.sentence)
        connect_slot_handlers(self.widgets.sentence)

        connect_selection_changed_handler(self.widgets.definition)
        connect_slot_handlers(self.widgets.definition)

        connect_selection_changed_handler(self.widgets.definition2)
        connect_slot_handlers(self.widgets.definition2)

    def connectClipboard(self):
        # Connect to OS clipboard
        if settings.value("primary", False, type=bool)\
                and QClipboard.supportsSelection(QApplication.clipboard()):
            QApplication.clipboard().selectionChanged.connect(
                lambda: self.readClipboard(False, True))

        QApplication.clipboard().dataChanged.connect(self.readClipboard)

    def readClipboard(self, evenWhenFocused=False, selection=False):
        """
        If the text is just a single word, we look it up right away.
        If it's a json and has the required fields, we use these fields to
        populate the relevant fields.
        Otherwise we dump everything to the Sentence field.
        By default this is not activated when the window is in focus to prevent
        mistakes, unless it is used from the button.
        """
        if selection:
            text = QApplication.clipboard().text(QClipboard.Selection)
        else:
            text = QApplication.clipboard().text()
        
        if not selection: 
            # I am not sure how you can copy an image to PRIMARY
            # so here we go
            if QApplication.clipboard().mimeData().hasImage():
                self.controller.state.setImage(QApplication.clipboard().pixmap())
                return

        if self.app_window.isActiveWindow() and not evenWhenFocused:
            return

        self.controller.handleClipboardSelection(text)