"""Dialog réutilisé pour choisir un intervenant dans l'annuaire (ou en créer
un nouveau) — utilisé par l'onglet équipe pluri et par la fenêtre réunions."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from services import intervenant_service
from services.dto import IntervenantDTO
from ui.widgets.searchable_combo_box import SearchableComboBox


class IntervenantCreateDialog(QDialog):
    """Dialog minimal pour ajouter un intervenant à l'annuaire global, sans
    passer par la sélection (utilisé par ex. depuis la fenêtre réunions)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvel intervenant")
        self.setMinimumWidth(360)
        self.result_intervenant: IntervenantDTO | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._nom = QLineEdit()
        self._fonction = QLineEdit()
        form.addRow("Nom :", self._nom)
        form.addRow("Fonction :", self._fonction)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        nom = self._nom.text().strip()
        fonction = self._fonction.text().strip()
        if not nom or not fonction:
            QMessageBox.warning(self, "Champs requis", "Le nom et la fonction sont obligatoires.")
            return
        self.result_intervenant = intervenant_service.create_intervenant(nom, fonction)
        self.accept()


class IntervenantPickerDialog(QDialog):
    """Retourne un IntervenantDTO choisi dans l'annuaire, ou nouvellement créé."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter un intervenant")
        self.setMinimumWidth(380)
        self.result_intervenant: IntervenantDTO | None = None

        layout = QVBoxLayout(self)
        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack)

        self._pick_page = self._build_pick_page()
        self._create_page = self._build_create_page()
        self._stack.addWidget(self._pick_page)
        self._stack.addWidget(self._create_page)

        self._reload_annuaire()

    def _build_pick_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._combo = SearchableComboBox()
        layout.addWidget(self._combo)

        new_button = QDialogButtonBox()
        new_btn = new_button.addButton("Nouvel intervenant…", QDialogButtonBox.ButtonRole.ActionRole)
        new_btn.clicked.connect(lambda: self._stack.setCurrentWidget(self._create_page))
        layout.addWidget(new_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_pick_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        return page

    def _build_create_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QFormLayout()
        self._new_nom = QLineEdit()
        self._new_fonction = QLineEdit()
        form.addRow("Nom :", self._new_nom)
        form.addRow("Fonction :", self._new_fonction)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_create_accept)
        buttons.rejected.connect(lambda: self._stack.setCurrentWidget(self._pick_page))
        layout.addWidget(buttons)
        return page

    def _reload_annuaire(self) -> None:
        intervenants = intervenant_service.list_annuaire()
        self._combo.set_items([(i.libelle, i) for i in intervenants])

    def _on_pick_accept(self) -> None:
        data = self._combo.current_data()
        if data is None:
            QMessageBox.warning(self, "Sélection requise", "Choisissez un intervenant ou créez-en un.")
            return
        self.result_intervenant = data
        self.accept()

    def _on_create_accept(self) -> None:
        nom = self._new_nom.text().strip()
        fonction = self._new_fonction.text().strip()
        if not nom or not fonction:
            QMessageBox.warning(self, "Champs requis", "Le nom et la fonction sont obligatoires.")
            return
        self.result_intervenant = intervenant_service.create_intervenant(nom, fonction)
        self.accept()
