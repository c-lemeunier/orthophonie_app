"""Dialog d'ajout d'un patient (nom + prénom minimum, le reste se complète
ensuite dans l'onglet Infos personnelles)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class PatientFormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter un patient")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._nom = QLineEdit()
        self._prenom = QLineEdit()
        form.addRow("Nom :", self._nom)
        form.addRow("Prénom :", self._prenom)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self._nom.text().strip() or not self._prenom.text().strip():
            QMessageBox.warning(self, "Champs requis", "Le nom et le prénom sont obligatoires.")
            return
        self.accept()

    def values(self) -> tuple[str, str]:
        return self._nom.text().strip(), self._prenom.text().strip()
