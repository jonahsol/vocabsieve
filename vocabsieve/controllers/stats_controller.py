from PyQt5.QtCore import QTimer
from ui.widgets import *
from db import Record

class StatsController():
    def __init__(self, widgets: Widgets):
        self.widgets = widgets
        rec = Record()
        self.initTimer()

    def initTimer(self):
        self.showStats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showStats)
        self.timer.start(2000)

    def showStats(self):
        lookups = rec.countLookupsToday()
        notes = rec.countNotesToday()
        self.widgets.stats_label.setText(f"L:{str(lookups)} N:{str(notes)}")
