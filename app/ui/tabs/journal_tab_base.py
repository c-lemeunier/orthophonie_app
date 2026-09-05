"""Widget générique (date, note) réutilisé par coordinations/bilans/notes.

Chaque entrée est affichée intégralement (texte complet, retour à la ligne)
sur une carte, dans une liste défilant verticalement — la barre horizontale
est désactivée pour forcer le contenu à tenir dans la largeur disponible,
ce qui est ce qui permet au retour à la ligne de fonctionner.
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services import journal_service
from services.dto import JournalEntryDTO
from services.journal_service import JournalKind
from ui import theme
from ui.tabs.base_tab import PatientTabWidget


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
    """Bloc affichant une entrée en entier (date + note complète, wrap). Le
    liseré gauche reprend la couleur d'accent de l'onglet."""

    clicked = Signal(int)

    def __init__(self, entry: JournalEntryDTO, accent_color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry_id = entry.id
        self._accent_color = accent_color
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        date_label = QLabel(entry.date.strftime("%d/%m/%Y"))
        date_label.setStyleSheet(f"font-weight: bold; color: {accent_color};")
        layout.addWidget(date_label)

        note_label = QLabel(entry.note)
        note_label.setWordWrap(True)
        note_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(note_label)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        border_width = 2 if selected else 1
        self.setStyleSheet(
            f"_EntryCard {{ border: 1px solid {theme.BORDER}; "
            f"border-left: {border_width + 2}px solid {self._accent_color}; "
            f"border-radius: 4px; background-color: {theme.CREAM}; }}"
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.entry_id)
        super().mousePressEvent(event)


class JournalTabBase(PatientTabWidget):
    """kind : 'coordinations' | 'bilans' | 'notes'."""

    def __init__(
        self, kind: JournalKind, title_singulier: str, accent_key: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._kind = kind
        self._title_singulier = title_singulier
        self._accent_color = theme.TAB_ACCENTS[accent_key]
        self._entries_cache: list[JournalEntryDTO] = []
        self._selected_entry_id: int | None = None
        self._cards: list[_EntryCard] = []

        theme.apply_tab_accent(self, accent_key)

        layout = QVBoxLayout(self)

        header = self._create_header_widget()
        if header is not None:
            layout.addWidget(header)

        self._empty_label = QLabel("Aucune entrée enregistrée.")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Le viewport interne de la scroll area a sa propre palette et
        # n'hérite pas automatiquement du fond du thème via le QSS global.
        scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {theme.CREAM}; border: none; }}")
        self._cards_container = QWidget()
        self._cards_container.setStyleSheet(f"background-color: {theme.CREAM};")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.addStretch(1)
        scroll_area.setWidget(self._cards_container)
        layout.addWidget(scroll_area)

        buttons_row = QHBoxLayout()
        self._btn_add = QPushButton(f"Ajouter {self._title_singulier}")
        self._btn_add.clicked.connect(self._on_add)
        theme.tag_button(self._btn_add, "add")
        self._btn_edit = QPushButton("Modifier")
        self._btn_edit.clicked.connect(self._on_edit)
        theme.tag_button(self._btn_edit, "edit")
        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.clicked.connect(self._on_delete)
        theme.tag_button(self._btn_delete, "delete")
        buttons_row.addWidget(self._btn_add)
        buttons_row.addWidget(self._btn_edit)
        buttons_row.addWidget(self._btn_delete)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self._set_buttons_enabled(False)

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
            card = _EntryCard(entry, self._accent_color)
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
        self._render_cards(entries)
        self._after_refresh(entries)

    def clear_view(self) -> None:
        self._entries_cache = []
        self._selected_entry_id = None
        self._render_cards([])
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
