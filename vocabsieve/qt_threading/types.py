from PyQt5.QtCore import pyqtSignal, QObject
from typing import Callable, Any, TypedDict, Tuple
from typing_extensions import NotRequired

class WorkerSlotKwArgs(TypedDict):
    start_slot: NotRequired[Callable[[], None]]
    finished_slot: NotRequired[Callable[[], None]]
    error_slot: NotRequired[Callable[[Tuple], None]]
    result_slot: NotRequired[Callable[[Any], None]]
    progress_slot: NotRequired[Callable[[Any], None]]
worker_slot_to_signal = {
    'start_slot': "start",
    'finished_slot': "finished",
    'error_slot': "error",
    'result_slot': "result",
    'progress_slot': "progress",
}

class WorkerSignals(QObject):
    start = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)

def type_check_worker_slot_to_signal():
    test_signals = WorkerSignals()
    for _, signal in worker_slot_to_signal.items():
        assert hasattr(test_signals, signal)
type_check_worker_slot_to_signal()
