from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services import intervenant_service
from ui.intervenant_form_dialog import IntervenantPickerDialog
from ui.tabs.base_tab import PatientTabWidget

_COL_FONCTION = 0
_COL_NOM = 1


class TabEquipe(PatientTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Fonction", "Nom"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        buttons_row = QHBoxLayout()
        self._btn_add = QPushButton("Ajouter")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove = QPushButton("Supprimer")
        self._btn_remove.clicked.connect(self._on_remove)
        buttons_row.addWidget(self._btn_add)
        buttons_row.addWidget(self._btn_remove)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self._set_buttons_enabled(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_add.setEnabled(enabled)
        self._btn_remove.setEnabled(enabled)

    def refresh(self) -> None:
        self._set_buttons_enabled(True)
        liens = intervenant_service.list_equipe_patient(self.patient_id)
        self._table.setRowCount(len(liens))
        for row, lien in enumerate(liens):
            fonction_item = QTableWidgetItem(lien.intervenant.fonction)
            fonction_item.setData(Qt.ItemDataRole.UserRole, lien.lien_id)
            fonction_item.setFlags(fonction_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            nom_item = QTableWidgetItem(lien.intervenant.nom)
            nom_item.setFlags(nom_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, _COL_FONCTION, fonction_item)
            self._table.setItem(row, _COL_NOM, nom_item)

    def clear_view(self) -> None:
        self._table.setRowCount(0)
        self._set_buttons_enabled(False)

    def _on_add(self) -> None:
        if self.patient_id is None:
            return
        dialog = IntervenantPickerDialog(self)
        if dialog.exec() and dialog.result_intervenant is not None:
            intervenant_service.ajouter_a_equipe(self.patient_id, dialog.result_intervenant.id)
            self.refresh()

    def _on_remove(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        lien_id = self._table.item(row, _COL_FONCTION).data(Qt.ItemDataRole.UserRole)
        intervenant_service.retirer_de_equipe(lien_id)
        self.refresh()
