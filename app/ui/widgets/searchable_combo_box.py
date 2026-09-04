"""QComboBox éditable dont la liste déroulante se filtre en direct pendant la
frappe (utilisé pour le sélecteur de patients et les listes recherchables)."""
from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QWidget


class SearchableComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self._source_model = QStandardItemModel(self)
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._source_model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterRole(Qt.ItemDataRole.DisplayRole)
        self.setModel(self._proxy_model)

        self.lineEdit().textEdited.connect(self._on_text_edited)
        self.lineEdit().editingFinished.connect(self._clear_filter)
        self.activated.connect(self._on_activated)

    def _on_text_edited(self, text: str) -> None:
        self._proxy_model.setFilterFixedString(text)
        if not self.view().isVisible():
            self.showPopup()

    def _clear_filter(self) -> None:
        if self._proxy_model.filterRegularExpression().pattern():
            self._proxy_model.setFilterFixedString("")

    def _on_activated(self, proxy_row: int) -> None:
        data = self.itemData(proxy_row, Qt.ItemDataRole.UserRole)
        self._clear_filter()
        if data is not None:
            self.set_current_data(data)

    def set_items(self, items: list[tuple[str, object]]) -> None:
        """items : liste de (label, data)."""
        current_data = self.current_data()
        self._clear_filter()
        self._source_model.clear()
        for label, data in items:
            item = QStandardItem(label)
            item.setData(data, Qt.ItemDataRole.UserRole)
            item.setEditable(False)
            self._source_model.appendRow(item)
        if current_data is not None:
            self.set_current_data(current_data)

    def current_data(self) -> object | None:
        return self.currentData()

    def set_current_data(self, data: object) -> None:
        index = self.findData(data)
        if index >= 0:
            self.setCurrentIndex(index)
