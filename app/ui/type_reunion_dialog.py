"""Gestion de l'annuaire des types de réunion : ajout, renommage, suppression.
L'appelant doit recharger son propre combo après la fermeture de ce dialog
(les types ne sont pas notifiés en direct, l'annuaire est petit)."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from services import type_reunion_service
from ui.libelle_manager_dialog import LibelleManagerDialog


class TypeReunionManagerDialog(LibelleManagerDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            title="Gérer les types de réunion",
            service=type_reunion_service,
            item_singular="type de réunion",
            delete_warning="Les réunions qui l'utilisaient perdront simplement ce type (elles ne sont pas supprimées).",
        )
