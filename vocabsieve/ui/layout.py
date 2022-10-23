from PyQt5.QtWidgets import QMainWindow
from settings import *
from ui.widgets import *

def scale_font(app_window: QMainWindow):
    font = QApplication.font()
    font.setPointSize(
        int(font.pointSize() * settings.value("text_scale", type=int) / 100))
    app_window.setFont(font)

def draw_layout_h(app_window: QMainWindow, widgets: Widgets):
    app_window.resize(1000, 300)

    layout = QGridLayout(widgets.centralWidget)
    app_window.setLayout(layout)

    # widgets.sentence.setMaximumHeight(99999)
    layout.addWidget(widgets.namelabel, 0, 0, 1, 1)
    layout.addWidget(widgets.image_viewer, 0, 1, 2, 1)
    layout.addWidget(widgets.single_word, 0, 3, 1, 2)

    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 1, 0)
    layout.addWidget(widgets.freq_display, 0, 2)
    layout.addWidget(widgets.read_button, 6, 1)

    layout.addWidget(widgets.sentence, 2, 0, 3, 2)
    layout.addWidget(widgets.audio_selector, 5, 0, 1, 2)
    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 1, 2)

    layout.addWidget(widgets.lookup_button, 3, 2)
    layout.addWidget(widgets.lookup_exact_button, 4, 2)

    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 1, 3)
    # layout.add, language, lemmatize(widgets.web_button, 1, 4)
    layout.addWidget(widgets.word, 2, 2, 1, 1)
    if settings.value("dict_source2", DISABLED) != DISABLED:
        layout.addWidget(widgets.definition, 2, 3, 4, 1)
        layout.addWidget(widgets.definition2, 2, 4, 4, 1)
    else:
        layout.addWidget(widgets.definition, 2, 3, 4, 2)

    layout.addWidget(QLabel("Additional tags"), 5, 2, 1, 1)

    layout.addWidget(widgets.tags, 6, 2)

    layout.addWidget(widgets.toanki_button, 6, 3, 1, 1)
    layout.addWidget(widgets.config_button, 6, 4, 1, 1)
    layout.setColumnStretch(0, 2)
    layout.setColumnStretch(1, 2)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 5)
    layout.setColumnStretch(4, 5)
    layout.setRowStretch(0, 0)
    #layout.setRowStretch(1, 5)
    layout.setRowStretch(2, 5)
    layout.setRowStretch(3, 5)
    layout.setRowStretch(4, 5)
    layout.setRowStretch(5, 5)
    layout.setRowStretch(6, 0)

def draw_layout_v(app_window: QMainWindow, widgets: Widgets):
    app_window.resize(400, 700)

    layout = QGridLayout(widgets.centralWidget)
    app_window.setLayout(layout)

    layout.addWidget(widgets.namelabel, 0, 0, 1, 2)
    layout.addWidget(widgets.single_word, 1, 0, 1, 3)

    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Sentence</h3>"), 2, 0)
    layout.addWidget(widgets.read_button, 2, 1)
    layout.addWidget(widgets.image_viewer, 0, 2, 3, 1)
    layout.addWidget(widgets.sentence, 3, 0, 1, 3)
    layout.setRowStretch(3, 1)
    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Word</h3>"), 4, 0)

    if settings.value("lemmatization", True, type=bool):
        layout.addWidget(widgets.lookup_button, 4, 1)
        layout.addWidget(widgets.lookup_exact_button, 4, 2)
    else:
        layout.addWidget(widgets.lookup_button, 4, 1, 1, 2)

    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Definition</h3>"), 6, 0)
    layout.addWidget(widgets.freq_display, 6, 1)
    layout.addWidget(widgets.web_button, 6, 2)
    layout.addWidget(widgets.word, 5, 0, 1, 3)
    layout.setRowStretch(7, 2)
    layout.setRowStretch(9, 2)
    if settings.value("dict_source2", DISABLED) != DISABLED:
        layout.addWidget(widgets.definition, 7, 0, 2, 3)
        layout.addWidget(widgets.definition2, 9, 0, 2, 3)
    else:
        layout.addWidget(widgets.definition, 7, 0, 4, 3)

    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Pronunciation</h3>"),
        11,
        0,
        1,
        3)
    layout.addWidget(widgets.audio_selector, 12, 0, 1, 3)
    layout.setRowStretch(12, 1)
    layout.addWidget(
        QLabel("<h3 style=\"font-weight: normal;\">Additional tags</h3>"),
        13,
        0,
        1,
        3)

    layout.addWidget(widgets.tags, 14, 0, 1, 3)

    layout.addWidget(widgets.toanki_button, 15, 0, 1, 3)
    layout.addWidget(widgets.config_button, 16, 0, 1, 3)
