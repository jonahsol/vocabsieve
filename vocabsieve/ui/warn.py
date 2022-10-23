from PyQt5.QtWidgets import QMessageBox

def warn(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(text)
    msg.exec()