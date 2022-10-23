from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QStatusBar

class StatusBar(QStatusBar):
    def status(self, msg, t=4000):
        self.showMessage(self.time() + " " + msg, t)

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')
