"""Onglet Derniers bilans : date, type (annuaire géré par l'utilisateur),
document (texte) et note, chaque bilan affiché en entier sur une carte."""
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

from services import bilan_service, type_bilan_service
from services.dto import BilanDTO
from ui import theme
from ui.tabs.base_tab import PatientTabWidget
from ui.type_bilan_dialog import TypeBilanManagerDialog
from ui.widgets.document_drop_field import DocumentDropField, document_link_html, open_document
from ui.widgets.searchable_combo_box import SearchableComboBox

_ACCENT = theme.TAB_ACCENTS["bilans"]


def _add_one_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # 29 février sur une année non bissextile
        return d.replace(month=2, day=28, year=d.year + 1)


class _BilanFormDialog(QDialog):
    def __init__(self, title: str, bilan: BilanDTO | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setDate(bilan.date if bilan else date.today())
        layout.addWidget(self._date_edit)

        type_row = QHBoxLayout()
        self._type_combo = SearchableComboBox()
        btn_manage_types = QPushButton("Gérer les types…")
        btn_manage_types.clicked.connect(self._on_manage_types)
        type_row.addWidget(self._type_combo, stretch=1)
        type_row.addWidget(btn_manage_types)
        layout.addLayout(type_row)
        self._reload_types(selected_id=bilan.type_bilan.id if bilan and bilan.type_bilan else None)

        layout.addWidget(QLabel("Document :"))
        self._document_field = DocumentDropField(bilan.document_path if bilan else None)
        layout.addWidget(self._document_field)

        layout.addWidget(QLabel("Note :"))
        self._note_edit = QTextEdit()
        self._note_edit.setPlainText(bilan.note if bilan else "")
        layout.addWidget(self._note_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _reload_types(self, selected_id: int | None) -> None:
        types = type_bilan_service.list_all()
        items = [("(Aucun type)", None)] + [(t.libelle, t.id) for t in types]
        self._type_combo.set_items(items)
        if selected_id is not None:
            self._type_combo.set_current_data(selected_id)

    def _on_manage_types(self) -> None:
        current = self._type_combo.current_data()
        TypeBilanManagerDialog(self).exec()
        self._reload_types(selected_id=current)

    def values(self) -> dict:
        return {
            "entry_date": self._date_edit.date().toPython(),
            "type_bilan_id": self._type_combo.current_data(),
            "document_path": self._document_field.path(),
            "note": self._note_edit.toPlainText().strip(),
        }


class _BilanCard(QFrame):
    clicked = Signal(int)

    def __init__(self, bilan: BilanDTO, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry_id = bilan.id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        header_row = QHBoxLayout()
        date_label = QLabel(bilan.date.strftime("%d/%m/%Y"))
        date_label.setStyleSheet(f"font-weight: bold; color: {_ACCENT};")
        header_row.addWidget(date_label)
        if bilan.type_bilan is not None:
            type_label = QLabel(bilan.type_bilan.libelle)
            type_label.setStyleSheet(
                f"color: {theme.TEXT_ON_DARK}; background-color: {_ACCENT}; "
                "border-radius: 3px; padding: 1px 8px;"
            )
            header_row.addWidget(type_label)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        if bilan.document_path:
            layout.addWidget(self._make_field_label("Document :"))
            document_label = QLabel(document_link_html(bilan.document_path))
            document_label.linkActivated.connect(lambda _href: open_document(bilan.document_path, self))
            layout.addWidget(document_label)

        layout.addWidget(self._make_field_label("Note :"))
        note_label = QLabel(bilan.note)
        note_label.setWordWrap(True)
        note_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(note_label)

        self.set_selected(False)

    @staticmethod
    def _make_field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-style: italic; color: palette(mid);")
        return label

    def set_selected(self, selected: bool) -> None:
        border_width = 4 if selected else 2
        self.setStyleSheet(
            f"_BilanCard {{ border: 1px solid {theme.BORDER}; "
            f"border-left: {border_width}px solid {_ACCENT}; "
            f"border-radius: 4px; background-color: {theme.CREAM}; }}"
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.entry_id)
        super().mousePressEvent(event)


class TabBilans(PatientTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        theme.apply_tab_accent(self, "bilans")

        self._bilans_cache: list[BilanDTO] = []
        self._selected_entry_id: int | None = None
        self._cards: list[_BilanCard] = []

        layout = QVBoxLayout(self)

        self._prochain_bilan_label = QLabel()
        self._prochain_bilan_label.setStyleSheet(f"font-weight: bold; color: {_ACCENT};")
        layout.addWidget(self._prochain_bilan_label)

        self._empty_label = QLabel("Aucun bilan enregistré.")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {theme.CREAM}; border: none; }}")
        self._cards_container = QWidget()
        self._cards_container.setStyleSheet(f"background-color: {theme.CREAM};")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.addStretch(1)
        scroll_area.setWidget(self._cards_container)
        layout.addWidget(scroll_area)

        buttons_row = QHBoxLayout()
        self._btn_add = QPushButton("Ajouter un bilan")
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

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_add.setEnabled(enabled)
        self._btn_edit.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)

    def _update_prochain_bilan_label(self, bilans: list[BilanDTO]) -> None:
        if not bilans:
            self._prochain_bilan_label.setText("Prochain bilan : aucun bilan enregistré pour l'instant.")
            return
        dernier = bilans[0].date  # la liste est triée par date décroissante
        prochain = _add_one_year(dernier)
        self._prochain_bilan_label.setText(
            f"Dernier bilan : {dernier.strftime('%d/%m/%Y')}    —    "
            f"Prochain bilan prévu : {prochain.strftime('%d/%m/%Y')}"
        )

    def _render_cards(self, bilans: list[BilanDTO]) -> None:
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards = []

        self._empty_label.setVisible(not bilans)

        still_selected = any(b.id == self._selected_entry_id for b in bilans)
        if not still_selected:
            self._selected_entry_id = None

        for bilan in bilans:
            card = _BilanCard(bilan)
            card.clicked.connect(self._on_card_clicked)
            card.set_selected(bilan.id == self._selected_entry_id)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
            self._cards.append(card)

    def _on_card_clicked(self, entry_id: int) -> None:
        self._selected_entry_id = entry_id
        for card in self._cards:
            card.set_selected(card.entry_id == entry_id)

    def refresh(self) -> None:
        self._set_buttons_enabled(True)
        bilans = bilan_service.list_for_patient(self.patient_id)
        self._bilans_cache = bilans
        self._render_cards(bilans)
        self._update_prochain_bilan_label(bilans)

    def clear_view(self) -> None:
        self._bilans_cache = []
        self._selected_entry_id = None
        self._render_cards([])
        self._update_prochain_bilan_label([])
        self._set_buttons_enabled(False)

    def _on_add(self) -> None:
        if self.patient_id is None:
            return
        dialog = _BilanFormDialog("Ajouter un bilan", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.values()
            if values["note"]:
                bilan_service.add_entry(self.patient_id, values.pop("entry_date"), **values)
                self.refresh()

    def _on_edit(self) -> None:
        if self._selected_entry_id is None:
            return
        bilan = next((b for b in self._bilans_cache if b.id == self._selected_entry_id), None)
        if bilan is None:
            return
        dialog = _BilanFormDialog("Modifier le bilan", bilan=bilan, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.values()
            if values["note"]:
                bilan_service.update_entry(bilan.id, **values)
                self.refresh()

    def _on_delete(self) -> None:
        if self._selected_entry_id is None:
            return
        bilan_service.delete_entry(self._selected_entry_id)
        self._selected_entry_id = None
        self.refresh()
