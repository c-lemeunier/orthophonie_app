"""Dialog générique de gestion d'un annuaire simple (id + libellé) : ajout,
renommage, suppression. Réutilisé pour les types de bilan et de réunion.

`service` doit exposer `list_all()`, `create(libelle)`, `update(id, libelle)`,
`delete(id)` — c'est le cas de `services.type_bilan_service` et
`services.type_reunion_service` (même forme, pas de classe/protocole formel
nécessaire pour deux usages)."""
from __future__ import annotations

from types import ModuleType

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

from ui import theme


class LibelleManagerDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        title: str,
        service: ModuleType,
        item_singular: str,
        delete_warning: str,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._item_singular = item_singular
        self._delete_warning = delete_warning

        self.setWindowTitle(title)
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
        for entry in self._service.list_all():
            item = QListWidgetItem(entry.libelle)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self._list.addItem(item)

    def _selected_id(self) -> int | None:
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self) -> None:
        libelle, ok = QInputDialog.getText(self, f"Nouveau {self._item_singular}", "Libellé :")
        if ok and libelle.strip():
            self._service.create(libelle.strip())
            self._reload()

    def _on_rename(self) -> None:
        entry_id = self._selected_id()
        if entry_id is None:
            return
        libelle, ok = QInputDialog.getText(
            self, f"Renommer le {self._item_singular}", "Libellé :", text=self._list.currentItem().text()
        )
        if ok and libelle.strip():
            self._service.update(entry_id, libelle.strip())
            self._reload()

    def _on_delete(self) -> None:
        entry_id = self._selected_id()
        if entry_id is None:
            return
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer le {self._item_singular} « {self._list.currentItem().text()} » ? {self._delete_warning}",
        )
        if reponse == QMessageBox.StandardButton.Yes:
            self._service.delete(entry_id)
            self._reload()
