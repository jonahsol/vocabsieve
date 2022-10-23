def exportNotes(self):
    """
    First ask for a file path, then save a CSV there.
    """
    path, _ = QFileDialog.getSaveFileName(
        self,
        "Save CSV to file",
        os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
            f"vocabsieve-notes-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
        ),
        "CSV (*.csv)"
    )
    if path:
        with open(path, 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['timestamp', 'content', 'anki_export_success', 'sentence', 'word', 
                'definition', 'definition2', 'pronunciation', 'image', 'tags']
            )
            writer.writerows(rec.getAllNotes())
    else:
        return

def exportLookups(self):
    """
    First ask for a file path, then save a CSV there.
    """
    path, _ = QFileDialog.getSaveFileName(
        self,
        "Save CSV to file",
        os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
            f"vocabsieve-lookups-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
        ),
        "CSV (*.csv)"
    )
    if path:
        with open(path, 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['timestamp', 'word', 'definition', 'language', 'lemmatize', 'dictionary', 'success']
            )
            writer.writerows(rec.getAllLookups())
    else:
        return
