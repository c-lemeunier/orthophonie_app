from __future__ import annotations

from datetime import date

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db.seed import SUGGESTIONS_FREQUENCE
from services import patient_service
from ui.tabs.base_tab import PatientTabWidget
from ui.widgets.searchable_combo_box import SearchableComboBox


class TabInfos(PatientTabWidget):
    patient_updated = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._nom = QLineEdit()
        self._prenom = QLineEdit()
        self._date_naissance = QDateEdit()
        self._date_naissance.setCalendarPopup(True)
        self._date_naissance.setDisplayFormat("dd/MM/yyyy")
        self._date_naissance.setDate(date(2000, 1, 1))
        self._date_debut = QDateEdit()
        self._date_debut.setCalendarPopup(True)
        self._date_debut.setDisplayFormat("dd/MM/yyyy")
        self._date_debut.setDate(date.today())
        self._diagnostic = QTextEdit()
        self._frequence = SearchableComboBox()
        self._frequence.set_items([(f, f) for f in SUGGESTIONS_FREQUENCE])
        self._frequence.setEditable(True)

        form.addRow("Nom :", self._nom)
        form.addRow("Prénom :", self._prenom)
        form.addRow("Date de naissance :", self._date_naissance)
        form.addRow("Date début de prise en charge :", self._date_debut)
        form.addRow("Diagnostic :", self._diagnostic)
        form.addRow("Fréquence :", self._frequence)
        layout.addLayout(form)

        self._btn_save = QPushButton("Enregistrer")
        self._btn_save.clicked.connect(self._on_save)
        layout.addWidget(self._btn_save)
        layout.addStretch(1)

        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        for widget in (
            self._nom, self._prenom, self._date_naissance, self._date_debut,
            self._diagnostic, self._frequence, self._btn_save,
        ):
            widget.setEnabled(enabled)

    def refresh(self) -> None:
        self._set_enabled(True)
        patient = patient_service.get(self.patient_id)
        if patient is None:
            self.clear_view()
            return
        self._nom.setText(patient.nom)
        self._prenom.setText(patient.prenom)
        if patient.date_naissance:
            self._date_naissance.setDate(patient.date_naissance)
        if patient.date_debut:
            self._date_debut.setDate(patient.date_debut)
        self._diagnostic.setPlainText(patient.diagnostic or "")
        self._frequence.setCurrentText(patient.frequence or "")

    def clear_view(self) -> None:
        self._nom.clear()
        self._prenom.clear()
        self._diagnostic.clear()
        self._frequence.setCurrentText("")
        self._set_enabled(False)

    def _on_save(self) -> None:
        if self.patient_id is None:
            return
        nom = self._nom.text().strip()
        prenom = self._prenom.text().strip()
        if not nom or not prenom:
            QMessageBox.warning(self, "Champs requis", "Le nom et le prénom sont obligatoires.")
            return
        patient_service.update_infos(
            self.patient_id,
            nom=nom,
            prenom=prenom,
            date_naissance=self._date_naissance.date().toPython(),
            date_debut=self._date_debut.date().toPython(),
            diagnostic=self._diagnostic.toPlainText().strip() or None,
            frequence=self._frequence.currentText().strip() or None,
        )
        QMessageBox.information(self, "Enregistré", "Les informations ont été enregistrées.")
        self.patient_updated.emit()
