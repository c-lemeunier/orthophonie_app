"""Widget générique (date, note) réutilisé par coordinations/bilans/notes.

Deux modes d'affichage :
- table (par défaut) : un tableau compact avec un aperçu (1re ligne) par entrée.
- cartes (`wrap_full_note=True`) : chaque entrée est affichée intégralement,
  texte complet et retour à la ligne, dans une liste déroulante de blocs —
  plus robuste qu'un calcul manuel de hauteur de ligne de tableau (qui dépend
  du moment où le widget est réellement affiché).
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services import journal_service
from services.dto import JournalEntryDTO
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


class _EntryCard(QFrame):
    """Bloc affichant une entrée en entier (date + note complète, wrap)."""

    clicked = Signal(int)

    _STYLE_NORMAL = "_EntryCard { border: 1px solid palette(mid); border-radius: 4px; }"
    _STYLE_SELECTED = "_EntryCard { border: 2px solid palette(highlight); border-radius: 4px; }"

    def __init__(self, entry: JournalEntryDTO, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry_id = entry.id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        date_label = QLabel(entry.date.strftime("%d/%m/%Y"))
        date_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(date_label)

        note_label = QLabel(entry.note)
        note_label.setWordWrap(True)
        note_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(note_label)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        self.setStyleSheet(self._STYLE_SELECTED if selected else self._STYLE_NORMAL)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.entry_id)
        super().mousePressEvent(event)


class JournalTabBase(PatientTabWidget):
    """kind : 'coordinations' | 'bilans' | 'notes'."""

    def __init__(
        self,
        kind: JournalKind,
        title_singulier: str,
        parent: QWidget | None = None,
        *,
        wrap_full_note: bool = False,
    ) -> None:
        super().__init__(parent)
        self._kind = kind
        self._title_singulier = title_singulier
        self._wrap_full_note = wrap_full_note
        self._entries_cache: list[JournalEntryDTO] = []
        self._selected_entry_id: int | None = None
        self._table: QTableWidget | None = None
        self._cards: list[_EntryCard] = []

        layout = QVBoxLayout(self)

        header = self._create_header_widget()
        if header is not None:
            layout.addWidget(header)

        if self._wrap_full_note:
            self._build_cards_view(layout)
        else:
            self._build_table_view(layout)

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

    # ---- Vue tableau (coordinations, bilans) ----
    def _build_table_view(self, layout: QVBoxLayout) -> None:
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Date", "Note"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_table_selection_changed)
        layout.addWidget(self._table)

    def _on_table_selection_changed(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            self._selected_entry_id = None
        else:
            self._selected_entry_id = self._table.item(row, _COL_DATE).data(Qt.ItemDataRole.UserRole)

    def _render_table(self, entries: list[JournalEntryDTO]) -> None:
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            date_item = QTableWidgetItem(entry.date.strftime("%d/%m/%Y"))
            date_item.setData(Qt.ItemDataRole.UserRole, entry.id)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            apercu = entry.note.splitlines()[0] if entry.note else ""
            apercu_item = QTableWidgetItem(apercu)
            apercu_item.setFlags(apercu_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, _COL_DATE, date_item)
            self._table.setItem(row, _COL_APERCU, apercu_item)

    # ---- Vue cartes (notes) ----
    def _build_cards_view(self, layout: QVBoxLayout) -> None:
        self._empty_label = QLabel("Aucune entrée enregistrée.")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        # Barre de défilement verticale uniquement (pour lire les notes plus
        # anciennes) — la barre horizontale est désactivée explicitement pour
        # forcer le contenu à tenir dans la largeur disponible, ce qui est ce
        # qui permet au retour à la ligne de fonctionner.
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.addStretch(1)
        scroll_area.setWidget(self._cards_container)
        layout.addWidget(scroll_area)

    def _render_cards(self, entries: list[JournalEntryDTO]) -> None:
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards = []

        self._empty_label.setVisible(not entries)

        still_selected = any(e.id == self._selected_entry_id for e in entries)
        if not still_selected:
            self._selected_entry_id = None

        for entry in entries:
            card = _EntryCard(entry)
            card.clicked.connect(self._on_card_clicked)
            card.set_selected(entry.id == self._selected_entry_id)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
            self._cards.append(card)

    def _on_card_clicked(self, entry_id: int) -> None:
        self._selected_entry_id = entry_id
        for card in self._cards:
            card.set_selected(card.entry_id == entry_id)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_add.setEnabled(enabled)
        self._btn_edit.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)

    def _create_header_widget(self) -> QWidget | None:
        """À surcharger pour ajouter un encart au-dessus (ex. TabBilans)."""
        return None

    def _after_refresh(self, entries: list[JournalEntryDTO]) -> None:
        """À surcharger pour réagir aux données rechargées (ex. TabBilans)."""

    def refresh(self) -> None:
        self._set_buttons_enabled(True)
        entries = journal_service.list_for_patient(self._kind, self.patient_id)
        self._entries_cache = entries
        if self._wrap_full_note:
            self._render_cards(entries)
        else:
            self._render_table(entries)
        self._after_refresh(entries)

    def clear_view(self) -> None:
        self._entries_cache = []
        self._selected_entry_id = None
        if self._wrap_full_note:
            self._render_cards([])
        else:
            self._table.setRowCount(0)
        self._set_buttons_enabled(False)
        self._after_refresh([])

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
        if self._selected_entry_id is None:
            return
        entry = next((e for e in self._entries_cache if e.id == self._selected_entry_id), None)
        if entry is None:
            return
        dialog = _EntryFormDialog(f"Modifier {self._title_singulier}", entry.date, entry.note, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry_date, note = dialog.values()
            if note:
                journal_service.update_entry(self._kind, entry.id, entry_date=entry_date, note=note)
                self.refresh()

    def _on_delete(self) -> None:
        if self._selected_entry_id is None:
            return
        journal_service.delete_entry(self._kind, self._selected_entry_id)
        self._selected_entry_id = None
        self.refresh()
