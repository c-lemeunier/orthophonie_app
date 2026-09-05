"""Fenêtre principale : sélection du patient + 6 onglets."""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from services import patient_service
from ui import theme
from ui.patient_window import PatientFormDialog
from ui.reunions_windows import ReunionsWindow
from ui.tabs.base_tab import PatientTabWidget
from ui.tabs.tab_bilans import TabBilans
from ui.tabs.tab_coordinations import TabCoordinations
from ui.tabs.tab_equipe import TabEquipe
from ui.tabs.tab_infos import TabInfos
from ui.tabs.tab_notes import TabNotes
from ui.tabs.tab_objectifs import TabObjectifs
from ui.widgets.searchable_combo_box import SearchableComboBox


_PLACEHOLDER_LABEL = "— Cliquez sur un patient —"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Orthophonie — Dossiers patients")
        self.resize(1000, 650)

        self._reunions_window: ReunionsWindow | None = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_row = QHBoxLayout()
        self._patient_combo = SearchableComboBox()
        self._patient_combo.currentIndexChanged.connect(self._on_patient_changed)
        top_row.addWidget(self._patient_combo, stretch=1)

        btn_add = QPushButton("Ajouter patient")
        btn_add.clicked.connect(self._on_add_patient)
        theme.tag_button(btn_add, "add")
        top_row.addWidget(btn_add)

        btn_delete = QPushButton("Supprimer patient")
        btn_delete.clicked.connect(self._on_delete_patient)
        theme.tag_button(btn_delete, "delete")
        top_row.addWidget(btn_delete)

        btn_reunions = QPushButton("Réunions équipe / synthèses")
        btn_reunions.clicked.connect(self._on_open_reunions)
        top_row.addWidget(btn_reunions)

        layout.addLayout(top_row)

        self._tabs = QTabWidget()
        self._tab_infos = TabInfos()
        self._tab_infos.patient_updated.connect(self._reload_patients)
        self._tab_equipe = TabEquipe()
        self._tab_objectifs = TabObjectifs()
        self._tab_coordinations = TabCoordinations()
        self._tab_bilans = TabBilans()
        self._tab_notes = TabNotes()

        self._patient_tabs: list[PatientTabWidget] = [
            self._tab_infos,
            self._tab_equipe,
            self._tab_objectifs,
            self._tab_coordinations,
            self._tab_bilans,
            self._tab_notes,
        ]

        self._tabs.addTab(self._tab_infos, "Infos personnelles")
        self._tabs.addTab(self._tab_equipe, "Équipe pluri")
        self._tabs.addTab(self._tab_objectifs, "Objectifs orthophoniques")
        self._tabs.addTab(self._tab_coordinations, "Coordinations")
        self._tabs.addTab(self._tab_bilans, "Derniers bilans")
        self._tabs.addTab(self._tab_notes, "Notes")
        layout.addWidget(self._tabs)

        # Couleur du libellé de chaque onglet = sa couleur d'accent, en plus
        # du liseré appliqué sur chaque page (theme.apply_tab_accent).
        for index, accent_key in enumerate(
            ["infos", "equipe", "objectifs", "coordinations", "bilans", "notes"]
        ):
            self._tabs.tabBar().setTabTextColor(index, QColor(theme.TAB_ACCENTS[accent_key]))

        self._reload_patients()

    def _reload_patients(self) -> None:
        patients = patient_service.list_all()
        items = [(_PLACEHOLDER_LABEL, None)] + [(p.nom_complet, p.id) for p in patients]
        self._patient_combo.set_items(items)
        # set_items préserve la sélection si le patient existe encore ; sinon
        # (patient supprimé, ou aucune sélection au démarrage) on retombe sur
        # le placeholder (index 0) — on force le rafraîchissement des onglets
        # dans tous les cas car set_items bloque les signaux pendant le reset.
        self._on_patient_changed(self._patient_combo.currentIndex())

    def _on_patient_changed(self, _index: int) -> None:
        patient_id = self._patient_combo.current_data()
        for tab in self._patient_tabs:
            tab.load_patient(patient_id)

    def _on_add_patient(self) -> None:
        dialog = PatientFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nom, prenom = dialog.values()
            patient = patient_service.create(nom, prenom)
            self._reload_patients()
            self._patient_combo.set_current_data(patient.id)
            self._tabs.setCurrentWidget(self._tab_infos)

    def _on_delete_patient(self) -> None:
        patient_id = self._patient_combo.current_data()
        if patient_id is None:
            return
        label = self._patient_combo.currentText()
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement le dossier de {label} ainsi que toutes "
            "ses données (objectifs, notes, bilans, coordinations) ?",
        )
        if reponse == QMessageBox.StandardButton.Yes:
            patient_service.delete(patient_id)
            self._reload_patients()

    def _on_open_reunions(self) -> None:
        if self._reunions_window is None:
            self._reunions_window = ReunionsWindow()
        self._reunions_window.refresh()
        self._reunions_window.show()
        self._reunions_window.raise_()
        self._reunions_window.activateWindow()
