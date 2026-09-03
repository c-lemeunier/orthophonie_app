"""Classe de base commune aux 6 onglets patient.

Chaque onglet n'a connaissance que de son propre `patient_id` et de ses
services. Il ne connaît ni la fenêtre principale, ni les autres onglets.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget


class PatientTabWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.patient_id: int | None = None

    def load_patient(self, patient_id: int | None) -> None:
        """Appelé par MainWindow à chaque changement de patient sélectionné."""
        self.patient_id = patient_id
        if patient_id is None:
            self.clear_view()
        else:
            self.refresh()

    def refresh(self) -> None:
        """À surcharger : recharge les données du patient courant depuis les services."""
        raise NotImplementedError

    def clear_view(self) -> None:
        """À surcharger : vide l'affichage quand aucun patient n'est sélectionné."""
        raise NotImplementedError
