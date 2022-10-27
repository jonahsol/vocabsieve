from PyQt5.QtCore import *
import traceback
import sys
from typing import Optional, Callable, Any

class WorkerSignals(QObject):
    start = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)

class Worker(QRunnable):
    def __init__(self, f, result_slot: Optional[Callable[[Any], None]] = None):
        super(Worker, self).__init__()

        self.f = f
        self.signals = WorkerSignals()
        if (result_slot):
            self.signals.result.connect(result_slot)

    @pyqtSlot()
    def run(self):
        self.signals.start.emit()
        try:
            result = self.f()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()