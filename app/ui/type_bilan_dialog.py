"""Gestion de l'annuaire des types de bilan : ajout, renommage, suppression.
L'appelant doit recharger son propre combo après la fermeture de ce dialog
(les types ne sont pas notifiés en direct, l'annuaire est petit)."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from services import type_bilan_service
from ui.libelle_manager_dialog import LibelleManagerDialog


class TypeBilanManagerDialog(LibelleManagerDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            title="Gérer les types de bilan",
            service=type_bilan_service,
            item_singular="type de bilan",
            delete_warning="Les bilans qui l'utilisaient perdront simplement ce type (ils ne sont pas supprimés).",
        )
