from PyQt5.QtCore import *
import traceback
import sys
from typing_extensions import Unpack
from qt_threading.types import *

class Worker(QRunnable):
    def __init__(self, 
        f, 
        **slots: Unpack[WorkerSlotKwArgs]):
        super(Worker, self).__init__()

        self.f = f
        self.signals = WorkerSignals()
        for slot_name, slot in slots.items():
            getattr(self.signals, worker_slot_to_signal[slot_name]).connect(slot)

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