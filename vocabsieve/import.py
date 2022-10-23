from ext.importer import KindleImporter, KoreaderImporter

def importkindle(self):
    fname = QFileDialog.getOpenFileName(
        parent=self,
        caption="Select a file",
        filter='Kindle clippings files (*.txt)',
    )[0]
    if not fname:
        return
    else:
        import_kindle = KindleImporter(self, fname)
        import_kindle.exec()

def importkoreader(self):
    path = QFileDialog.getExistingDirectory(
        parent=self,
        caption="Select the directory containers ebook files",
        directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
    )
    if not path:
        return
    else:
        import_koreader = KoreaderImporter(self, path)
        import_koreader.exec()
