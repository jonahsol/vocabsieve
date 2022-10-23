from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QVBoxLayout()
        message = QLabel(
            '''
© 2022 FreeLanguageTools<br><br>
Visit <a href="https://freelanguagetools.org">FreeLanguageTools.org</a> for more info on how to use this tool.<br>
You can also talk to us on <a href="https://webchat.kde.org/#/room/#flt:midov.pl">Matrix</a>
or <a href="https://t.me/fltchat">Telegram</a> for support.<br><br>

Consult <a href="https://freelanguagetools.org/2021/08/dictionaries-and-frequency-lists-for-ssm/">this link</a>
to find compatible dictionaries. <br><br>

VocabSieve (formerly SSM, ssmtool) is free software available to you under the terms of
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.
If you found a bug, or have enhancement ideas, please open an issue on the
Github <a href=https://github.com/FreeLanguageTools/vocabsieve>repository</a>.<br><br>

This program is yours to keep. There is no EULA you need to agree to.
No data is sent to any server other than the configured dictionary APIs.
Statistics data are stored locally.
<br><br>
Credits: <br><a href="https://en.wiktionary.org/wiki/Wiktionary:Main_Page">Wiktionary API</a><br>
If you find this tool useful, you can give it a star on Github and tell others about it. Any suggestions will also be appreciated.
            '''
        )
        message.setTextFormat(Qt.RichText)
        message.setOpenExternalLinks(True)
        message.setWordWrap(True)
        message.adjustSize()
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)