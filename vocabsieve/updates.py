from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
import requests
import importlib
from markdown import markdown
from packaging import version
from settings import settings

def check_updates(mount_to: QWidget):
    if settings.value("check_updates") is None:
        answer = QMessageBox.question(
            mount_to,
            "Check updates",
            "<h2>Would you like VocabSieve to check for updates automatically?</h2>"
            "Currently, the repository and releases are hosted on GitHub's servers, "
            "which will be queried for checking updates. <br>VocabSieve cannot and "
            "<strong>will not</strong> install any updates automatically."
            "<br>You can change this option in the configuration panel at a later date."
        )
        if answer == QMessageBox.Yes:
            settings.setValue("check_updates", True)
        if answer == QMessageBox.No:
            settings.setValue("check_updates", False)
        settings.sync()
    elif settings.value("check_updates", True, type=bool):
        try:
            res = requests.get("https://api.github.com/repos/FreeLanguageTools/vocabsieve/releases")
            data = res.json()
        except Exception:
            return
        latest_version = (current := data[0])['tag_name'].strip('v')
        current_version = importlib.metadata.version('vocabsieve')
        if version.parse(latest_version) > version.parse(current_version):
            answer2 = QMessageBox.information(
                mount_to,
                "New version",
                "<h2>There is a new version available!</h2>"
                + f"<h3>Version {latest_version}</h3>"
                + markdown(current['body']),
                buttons=QMessageBox.Open | QMessageBox.Ignore
            )
            if answer2 == QMessageBox.Open:
                QDesktopServices.openUrl(QUrl(current['html_url']))