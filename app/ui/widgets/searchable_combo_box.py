"""QComboBox éditable avec complétion/recherche, utilisé pour le sélecteur de
patients et les listes d'intervenants recherchables."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCompleter, QComboBox, QWidget


class SearchableComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = QCompleter(self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)

    def set_items(self, items: list[tuple[str, object]]) -> None:
        """items : liste de (label, data)."""
        current_data = self.current_data()
        self.blockSignals(True)
        self.clear()
        for label, data in items:
            self.addItem(label, data)
        self.blockSignals(False)
        if current_data is not None:
            self.set_current_data(current_data)

    def current_data(self) -> object | None:
        return self.currentData()

    def set_current_data(self, data: object) -> None:
        index = self.findData(data)
        if index >= 0:
            self.setCurrentIndex(index)
