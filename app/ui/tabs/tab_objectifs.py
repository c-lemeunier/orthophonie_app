from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services import objectifs_service
from ui.objectif_form_dialog import ObjectifFormDialog
from ui.style_constants import STATUT_LABELS, statut_icon
from ui.tabs.base_tab import PatientTabWidget

_ROLE_KIND = Qt.ItemDataRole.UserRole
_ROLE_ID = Qt.ItemDataRole.UserRole + 1

_KIND_GRAND = "grand"
_KIND_PETIT = "petit"


class TabObjectifs(PatientTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Objectif", "Statut"])
        self._tree.setColumnWidth(0, 400)
        layout.addWidget(self._tree)

        buttons_row = QHBoxLayout()
        self._btn_add_grand = QPushButton("Ajouter grand objectif")
        self._btn_add_grand.clicked.connect(self._on_add_grand)
        self._btn_add_petit = QPushButton("Ajouter petit objectif")
        self._btn_add_petit.clicked.connect(self._on_add_petit)
        self._btn_edit = QPushButton("Modifier")
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.clicked.connect(self._on_delete)
        buttons_row.addWidget(self._btn_add_grand)
        buttons_row.addWidget(self._btn_add_petit)
        buttons_row.addWidget(self._btn_edit)
        buttons_row.addWidget(self._btn_delete)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self._set_buttons_enabled(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._btn_add_grand.setEnabled(enabled)
        self._btn_add_petit.setEnabled(enabled)
        self._btn_edit.setEnabled(enabled)
        self._btn_delete.setEnabled(enabled)

    def refresh(self) -> None:
        self._set_buttons_enabled(True)
        self._tree.clear()
        grands = objectifs_service.list_for_patient(self.patient_id)
        for grand in grands:
            grand_item = QTreeWidgetItem([grand.libelle, STATUT_LABELS[grand.statut]])
            grand_item.setIcon(1, statut_icon(grand.statut))
            grand_item.setData(0, _ROLE_KIND, _KIND_GRAND)
            grand_item.setData(0, _ROLE_ID, grand.id)
            for petit in grand.petits_objectifs:
                petit_item = QTreeWidgetItem([petit.libelle, STATUT_LABELS[petit.statut]])
                petit_item.setIcon(1, statut_icon(petit.statut))
                petit_item.setData(0, _ROLE_KIND, _KIND_PETIT)
                petit_item.setData(0, _ROLE_ID, petit.id)
                grand_item.addChild(petit_item)
            self._tree.addTopLevelItem(grand_item)
        self._tree.expandAll()

    def clear_view(self) -> None:
        self._tree.clear()
        self._set_buttons_enabled(False)

    def _selected_item(self) -> QTreeWidgetItem | None:
        items = self._tree.selectedItems()
        return items[0] if items else None

    def _on_add_grand(self) -> None:
        if self.patient_id is None:
            return
        dialog = ObjectifFormDialog("Ajouter un grand objectif", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            libelle, statut = dialog.values()
            objectifs_service.add_grand_objectif(self.patient_id, libelle, statut=statut)
            self.refresh()

    def _on_add_petit(self) -> None:
        item = self._selected_item()
        if item is None or item.data(0, _ROLE_KIND) != _KIND_GRAND:
            QMessageBox.information(
                self, "Sélection requise",
                "Sélectionnez d'abord un grand objectif pour lui ajouter un petit objectif."
            )
            return
        grand_id = item.data(0, _ROLE_ID)
        dialog = ObjectifFormDialog("Ajouter un petit objectif", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            libelle, statut = dialog.values()
            objectifs_service.add_petit_objectif(grand_id, libelle, statut=statut)
            self.refresh()

    def _on_edit(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        kind = item.data(0, _ROLE_KIND)
        item_id = item.data(0, _ROLE_ID)
        current_libelle = item.text(0)
        dialog = ObjectifFormDialog(
            "Modifier l'objectif", libelle=current_libelle, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            libelle, statut = dialog.values()
            if kind == _KIND_GRAND:
                objectifs_service.update_grand_objectif(item_id, libelle=libelle, statut=statut)
            else:
                objectifs_service.update_petit_objectif(item_id, libelle=libelle, statut=statut)
            self.refresh()

    def _on_delete(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        kind = item.data(0, _ROLE_KIND)
        item_id = item.data(0, _ROLE_ID)
        if kind == _KIND_GRAND and item.childCount() > 0:
            reponse = QMessageBox.question(
                self, "Confirmer la suppression",
                "Ce grand objectif contient des petits objectifs qui seront "
                "également supprimés. Continuer ?",
            )
            if reponse != QMessageBox.StandardButton.Yes:
                return
        if kind == _KIND_GRAND:
            objectifs_service.delete_grand_objectif(item_id)
        else:
            objectifs_service.delete_petit_objectif(item_id)
        self.refresh()
