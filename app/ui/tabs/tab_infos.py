from __future__ import annotations

from datetime import date

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from db.seed import SUGGESTIONS_FREQUENCE
from services import patient_service
from services.dto import compute_age
from ui.tabs.base_tab import PatientTabWidget
from ui.widgets.searchable_combo_box import SearchableComboBox


def _format_age(date_naissance: date) -> str:
    age = compute_age(date_naissance)
    return f"{age} an" + ("s" if age != 1 else "")


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
        self._date_naissance.dateChanged.connect(self._on_date_naissance_changed)
        self._age_label = QLabel()
        self._date_debut = QDateEdit()
        self._date_debut.setCalendarPopup(True)
        self._date_debut.setDisplayFormat("dd/MM/yyyy")
        self._date_debut.setDate(date.today())
        self._classe = QLineEdit()
        self._diagnostic = QTextEdit()
        self._frequence = SearchableComboBox()
        self._frequence.set_items([(f, f) for f in SUGGESTIONS_FREQUENCE])
        self._frequence.setEditable(True)
        self._email_parent1 = QLineEdit()
        self._email_parent2 = QLineEdit()

        form.addRow("Nom :", self._nom)
        form.addRow("Prénom :", self._prenom)
        form.addRow("Date de naissance :", self._date_naissance)
        form.addRow("Âge :", self._age_label)
        form.addRow("Date début de prise en charge :", self._date_debut)
        form.addRow("Classe :", self._classe)
        form.addRow("Diagnostic :", self._diagnostic)
        form.addRow("Fréquence :", self._frequence)
        form.addRow("E-mail parent 1 :", self._email_parent1)
        form.addRow("E-mail parent 2 :", self._email_parent2)
        layout.addLayout(form)

        self._btn_save = QPushButton("Enregistrer")
        self._btn_save.clicked.connect(self._on_save)
        layout.addWidget(self._btn_save)
        layout.addStretch(1)

        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        for widget in (
            self._nom, self._prenom, self._date_naissance, self._date_debut,
            self._classe, self._diagnostic, self._frequence,
            self._email_parent1, self._email_parent2, self._btn_save,
        ):
            widget.setEnabled(enabled)

    def _on_date_naissance_changed(self) -> None:
        self._age_label.setText(_format_age(self._date_naissance.date().toPython()))

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
        self._on_date_naissance_changed()
        if patient.date_debut:
            self._date_debut.setDate(patient.date_debut)
        self._classe.setText(patient.classe or "")
        self._diagnostic.setPlainText(patient.diagnostic or "")
        self._frequence.setCurrentText(patient.frequence or "")
        self._email_parent1.setText(patient.email_parent1 or "")
        self._email_parent2.setText(patient.email_parent2 or "")

    def clear_view(self) -> None:
        self._nom.clear()
        self._prenom.clear()
        self._age_label.clear()
        self._classe.clear()
        self._diagnostic.clear()
        self._frequence.setCurrentText("")
        self._email_parent1.clear()
        self._email_parent2.clear()
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
            classe=self._classe.text().strip() or None,
            email_parent1=self._email_parent1.text().strip() or None,
            email_parent2=self._email_parent2.text().strip() or None,
        )
        QMessageBox.information(self, "Enregistré", "Les informations ont été enregistrées.")
        self.patient_updated.emit()
