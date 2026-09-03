"""Dialog d'ajout/modification d'une réunion (date, type, participants,
patients concernés, note)."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db.seed import SUGGESTIONS_TYPE_REUNION
from services import intervenant_service, patient_service
from services.dto import ReunionDTO
from ui.widgets.searchable_combo_box import SearchableComboBox


class ReunionFormDialog(QDialog):
    def __init__(self, reunion: ReunionDTO | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modifier la réunion" if reunion else "Ajouter une réunion")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setDate(reunion.date if reunion else date.today())
        form.addRow("Date :", self._date_edit)

        self._type_combo = SearchableComboBox()
        self._type_combo.set_items([(t, t) for t in SUGGESTIONS_TYPE_REUNION])
        self._type_combo.setEditable(True)
        if reunion:
            self._type_combo.setCurrentText(reunion.type_reunion)
        form.addRow("Type de réunion :", self._type_combo)

        layout.addLayout(form)

        lists_row = QHBoxLayout()

        participants_col = QVBoxLayout()
        participants_col.addWidget(QLabel("Participants :"))
        self._participants_list = QListWidget()
        self._fill_checkable_list(
            self._participants_list,
            [(i.libelle, i.id) for i in intervenant_service.list_annuaire()],
            selected_ids={p.id for p in reunion.participants} if reunion else set(),
        )
        participants_col.addWidget(self._participants_list)
        lists_row.addLayout(participants_col)

        patients_col = QVBoxLayout()
        patients_col.addWidget(QLabel("Patients concernés :"))
        self._patients_list = QListWidget()
        self._fill_checkable_list(
            self._patients_list,
            [(p.nom_complet, p.id) for p in patient_service.list_all()],
            selected_ids={p.id for p in reunion.patients} if reunion else set(),
        )
        patients_col.addWidget(self._patients_list)
        lists_row.addLayout(patients_col)

        layout.addLayout(lists_row)

        layout.addWidget(QLabel("Note :"))
        self._note_edit = QTextEdit()
        self._note_edit.setPlainText(reunion.note or "" if reunion else "")
        layout.addWidget(self._note_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _fill_checkable_list(
        list_widget: QListWidget, items: list[tuple[str, int]], selected_ids: set[int]
    ) -> None:
        for label, item_id in items:
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if item_id in selected_ids else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, item_id)
            list_widget.addItem(item)

    @staticmethod
    def _checked_ids(list_widget: QListWidget) -> list[int]:
        ids = []
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
        return ids

    def _on_accept(self) -> None:
        if not self._type_combo.currentText().strip():
            QMessageBox.warning(self, "Champ requis", "Le type de réunion est obligatoire.")
            return
        self.accept()

    def values(self) -> dict:
        return {
            "date": self._date_edit.date().toPython(),
            "type_reunion": self._type_combo.currentText().strip(),
            "note": self._note_edit.toPlainText().strip() or None,
            "intervenant_ids": self._checked_ids(self._participants_list),
            "patient_ids": self._checked_ids(self._patients_list),
        }
