"""Fenêtre séparée listant toutes les réunions équipe/synthèses, avec tri par
colonne et recherche libre sur toutes les colonnes."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from services import reunion_service
from services.dto import ReunionDTO
from ui import theme
from ui.intervenant_form_dialog import IntervenantCreateDialog
from ui.reunion_form_dialog import ReunionFormDialog

_HEADERS = ["Date", "Type", "Participants", "Patients concernés", "Note"]
_COL_DATE, _COL_TYPE, _COL_PARTICIPANTS, _COL_PATIENTS, _COL_NOTE = range(5)


class ReunionTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._reunions: list[ReunionDTO] = []

    def set_reunions(self, reunions: list[ReunionDTO]) -> None:
        self.beginResetModel()
        self._reunions = reunions
        self.endResetModel()

    def reunion_at(self, row: int) -> ReunionDTO:
        return self._reunions[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._reunions)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        return _HEADERS[section]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        reunion = self._reunions[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.UserRole and col == _COL_DATE:
            return reunion.date

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if col == _COL_DATE:
            return reunion.date.strftime("%d/%m/%Y")
        if col == _COL_TYPE:
            return reunion.type_reunion
        if col == _COL_PARTICIPANTS:
            return "\n".join(p.libelle for p in reunion.participants)
        if col == _COL_PATIENTS:
            return "\n".join(p.nom_complet for p in reunion.patients)
        if col == _COL_NOTE:
            return reunion.note or ""
        return None


class _ReunionFilterProxy(QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self._search_text = ""

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if not self._search_text:
            return True
        model = self.sourceModel()
        for col in range(model.columnCount()):
            index = model.index(source_row, col, source_parent)
            value = model.data(index, Qt.ItemDataRole.DisplayRole)
            if value and self._search_text in str(value).lower():
                return True
        return False

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        if left.column() == _COL_DATE:
            left_date = self.sourceModel().data(left, Qt.ItemDataRole.UserRole)
            right_date = self.sourceModel().data(right, Qt.ItemDataRole.UserRole)
            if isinstance(left_date, date) and isinstance(right_date, date):
                return left_date < right_date
        return super().lessThan(left, right)


class ReunionsWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Réunions équipe / synthèses")
        self.resize(900, 500)
        self.setMinimumSize(600, 350)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        search_row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Rechercher (date, type, participants, patient, note)…")
        self._search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_edit)
        layout.addLayout(search_row)

        self._model = ReunionTableModel()
        self._proxy = _ReunionFilterProxy()
        self._proxy.setSourceModel(self._model)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.sortByColumn(_COL_DATE, Qt.SortOrder.DescendingOrder)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setWordWrap(True)

        header = self._table.horizontalHeader()
        # Date, Type, Participants, Patients : juste la place nécessaire à leur
        # contenu. Seule Note s'étire pour occuper tout le reste de la largeur
        # (et donc tout l'espace gagné quand on agrandit la fenêtre).
        header.setSectionResizeMode(_COL_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_PARTICIPANTS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_PATIENTS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_NOTE, QHeaderView.ResizeMode.Stretch)
        # Le retour à la ligne dépend de la largeur des colonnes : recalculer
        # la hauteur des lignes à chaque redimensionnement d'une colonne (donc
        # aussi à chaque redimensionnement de la fenêtre, via Stretch).
        header.sectionResized.connect(lambda *_: self._table.resizeRowsToContents())

        self._table.doubleClicked.connect(lambda _: self._on_edit())
        layout.addWidget(self._table)

        buttons_row = QHBoxLayout()
        btn_add = QPushButton("Ajouter une réunion")
        btn_add.clicked.connect(self._on_add)
        theme.tag_button(btn_add, "add")
        btn_edit = QPushButton("Modifier")
        btn_edit.clicked.connect(self._on_edit)
        theme.tag_button(btn_edit, "edit")
        btn_delete = QPushButton("Supprimer")
        btn_delete.clicked.connect(self._on_delete)
        theme.tag_button(btn_delete, "delete")
        btn_new_intervenant = QPushButton("Nouvel intervenant")
        btn_new_intervenant.clicked.connect(self._on_new_intervenant)
        theme.tag_button(btn_new_intervenant, "add")
        buttons_row.addWidget(btn_add)
        buttons_row.addWidget(btn_edit)
        buttons_row.addWidget(btn_delete)
        buttons_row.addWidget(btn_new_intervenant)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        self.refresh()

    def _on_search_changed(self, text: str) -> None:
        self._proxy.set_search_text(text)

    def refresh(self) -> None:
        self._model.set_reunions(reunion_service.list_all())
        # Différé : juste après le peuplement, les largeurs de colonnes issues
        # de ResizeToContents/Stretch ne sont pas encore définitives tant que
        # la fenêtre n'a pas terminé sa mise en page.
        QTimer.singleShot(0, self._table.resizeRowsToContents)

    def _selected_reunion(self) -> ReunionDTO | None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return None
        source_index = self._proxy.mapToSource(indexes[0])
        return self._model.reunion_at(source_index.row())

    def _on_add(self) -> None:
        dialog = ReunionFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reunion_service.create(**dialog.values())
            self.refresh()

    def _on_edit(self) -> None:
        reunion = self._selected_reunion()
        if reunion is None:
            return
        dialog = ReunionFormDialog(reunion=reunion, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reunion_service.update(reunion.id, **dialog.values())
            self.refresh()

    def _on_delete(self) -> None:
        reunion = self._selected_reunion()
        if reunion is None:
            return
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer la réunion du {reunion.date.strftime('%d/%m/%Y')} ({reunion.type_reunion}) ?",
        )
        if reponse == QMessageBox.StandardButton.Yes:
            reunion_service.delete(reunion.id)
            self.refresh()

    def _on_new_intervenant(self) -> None:
        dialog = IntervenantCreateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_intervenant is not None:
            QMessageBox.information(
                self, "Intervenant ajouté",
                f"{dialog.result_intervenant.libelle} a été ajouté à l'annuaire.",
            )
