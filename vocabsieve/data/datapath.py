from PyQt5.QtCore import QStandardPaths
from os import path
from pathlib import Path

datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
Path(datapath).mkdir(parents=True, exist_ok=True)

def mk_data_dir(abs_path: str):
    Path(abs_path).mkdir(parents=True, exist_ok=True)
def get_data_abs_path(*rel_path: str):
    return path.join(datapath, *rel_path)