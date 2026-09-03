"""Widget générique (date, note) réutilisé par coordinations/bilans/notes."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services import journal_service
from services.journal_service import JournalKind
from ui.tabs.base_tab import PatientTabWidget

_COL_DATE = 0
_COL_APERCU = 1


class _EntryFormDialog(QDialog):
    def __init__(self, title: str, entry_date: date | None, note: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setDate(entry_date if entry_date else date.today())
        layout.addWidget(self._date_edit)

        self._note_edit = QTextEdit()
        self._note_edit.setPlainText(note)
        layout.addWidget(self._note_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[date, str]:
        return self._date_edit.date().toPython(), self._note_edit.toPlainText().strip()


class JournalTabBase(PatientTabWidget):
    """kind : 'coordinations' | 'bilans' | 'notes'."""

    def __init__(self, kind: JournalKind, title_singulier: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._kind = kind
        self._title_singulier = title_singulier

        layout = QVBoxLayout(self)

        header = self._create_header_widget()
        if header is not None:
            layout.addWidget(header)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Date", "Note"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        buttons_row = QHBoxLayout()
        self._btn_add = QPushButton(f"Ajouter {self._title_singulier}")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_edit = QPushButton("Modifier")
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.clicked.connect(self._on_delete)
        buttons_row.addWidget(self._btn_add)
        buttons_row.addWidget(self._btn_edit)
        buttons_row.addWidget(self._btn_delete)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self._set_buttons_enabled(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_add.setEnabled(enabled)
        self._btn_edit.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)

    def _create_header_widget(self) -> QWidget | None:
        """À surcharger pour ajouter un encart au-dessus du tableau (ex. TabBilans)."""
        return None

    def _after_refresh(self, entries: list) -> None:
        """À surcharger pour réagir aux données rechargées (ex. TabBilans)."""

    def refresh(self) -> None:
        self._set_buttons_enabled(True)
        entries = journal_service.list_for_patient(self._kind, self.patient_id)
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            date_item = QTableWidgetItem(entry.date.strftime("%d/%m/%Y"))
            date_item.setData(Qt.ItemDataRole.UserRole, entry.id)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            apercu = entry.note.splitlines()[0] if entry.note else ""
            apercu_item = QTableWidgetItem(apercu)
            apercu_item.setFlags(apercu_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            apercu_item.setData(Qt.ItemDataRole.UserRole, entry.note)
            self._table.setItem(row, _COL_DATE, date_item)
            self._table.setItem(row, _COL_APERCU, apercu_item)
        self._after_refresh(entries)

    def clear_view(self) -> None:
        self._table.setRowCount(0)
        self._set_buttons_enabled(False)
        self._after_refresh([])

    def _selected_entry_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        return self._table.item(row, _COL_DATE).data(Qt.ItemDataRole.UserRole)

    def _on_add(self) -> None:
        if self.patient_id is None:
            return
        dialog = _EntryFormDialog(f"Ajouter {self._title_singulier}", None, "", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry_date, note = dialog.values()
            if note:
                journal_service.add_entry(self._kind, self.patient_id, entry_date, note)
                self.refresh()

    def _on_edit(self) -> None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        row = self._table.currentRow()
        current_note = self._table.item(row, _COL_APERCU).data(Qt.ItemDataRole.UserRole)
        current_date_str = self._table.item(row, _COL_DATE).text()
        current_date = date(*reversed([int(p) for p in current_date_str.split("/")]))
        dialog = _EntryFormDialog(f"Modifier {self._title_singulier}", current_date, current_note, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry_date, note = dialog.values()
            if note:
                journal_service.update_entry(self._kind, entry_id, entry_date=entry_date, note=note)
                self.refresh()

    def _on_delete(self) -> None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        journal_service.delete_entry(self._kind, entry_id)
        self.refresh()
