"""Dialog d'ajout/modification d'un grand ou petit objectif (libellé + statut)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db.model import StatutObjectif
from ui.style_constants import STATUT_LABELS


class ObjectifFormDialog(QDialog):
    def __init__(
        self,
        title: str,
        libelle: str = "",
        statut: StatutObjectif = StatutObjectif.A_TRAVAILLER,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._libelle = QTextEdit()
        self._libelle.setPlainText(libelle)
        self._libelle.setFixedHeight(80)
        form.addRow("Libellé :", self._libelle)

        self._statut = QComboBox()
        for s in StatutObjectif:
            self._statut.addItem(STATUT_LABELS[s], s)
        index = self._statut.findData(statut)
        if index >= 0:
            self._statut.setCurrentIndex(index)
        form.addRow("Statut :", self._statut)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self._libelle.toPlainText().strip():
            QMessageBox.warning(self, "Champ requis", "Le libellé est obligatoire.")
            return
        self.accept()

    def values(self) -> tuple[str, StatutObjectif]:
        return self._libelle.toPlainText().strip(), self._statut.currentData()
