"""Gestion de l'annuaire des types de bilan : ajout, renommage, suppression.
L'appelant doit recharger son propre combo après la fermeture de ce dialog
(les types ne sont pas notifiés en direct, l'annuaire est petit)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services import type_bilan_service
from ui import theme


class TypeBilanManagerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gérer les types de bilan")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self._list)

        buttons_row = QHBoxLayout()
        btn_add = QPushButton("Ajouter")
        btn_add.clicked.connect(self._on_add)
        theme.tag_button(btn_add, "add")
        btn_rename = QPushButton("Renommer")
        btn_rename.clicked.connect(self._on_rename)
        theme.tag_button(btn_rename, "edit")
        btn_delete = QPushButton("Supprimer")
        btn_delete.clicked.connect(self._on_delete)
        theme.tag_button(btn_delete, "delete")
        buttons_row.addWidget(btn_add)
        buttons_row.addWidget(btn_rename)
        buttons_row.addWidget(btn_delete)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self._reload()

    def _reload(self) -> None:
        self._list.clear()
        for type_bilan in type_bilan_service.list_all():
            item = QListWidgetItem(type_bilan.libelle)
            item.setData(Qt.ItemDataRole.UserRole, type_bilan.id)
            self._list.addItem(item)

    def _selected_id(self) -> int | None:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self) -> None:
        libelle, ok = QInputDialog.getText(self, "Nouveau type de bilan", "Libellé :")
        if ok and libelle.strip():
            type_bilan_service.create(libelle.strip())
            self._reload()

    def _on_rename(self) -> None:
        type_id = self._selected_id()
        if type_id is None:
            return
        libelle, ok = QInputDialog.getText(
            self, "Renommer le type de bilan", "Libellé :", text=self._list.currentItem().text()
        )
        if ok and libelle.strip():
            type_bilan_service.update(type_id, libelle.strip())
            self._reload()

    def _on_delete(self) -> None:
        type_id = self._selected_id()
        if type_id is None:
            return
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer le type « {self._list.currentItem().text()} » ? "
            "Les bilans qui l'utilisaient perdront simplement ce type (ils ne sont pas supprimés).",
        )
        if reponse == QMessageBox.StandardButton.Yes:
            type_bilan_service.delete(type_id)
            self._reload()
