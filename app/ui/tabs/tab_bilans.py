from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QLabel, QWidget

from ui.tabs.journal_tab_base import JournalTabBase


def _add_one_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # 29 février sur une année non bissextile
        return d.replace(month=2, day=28, year=d.year + 1)


class TabBilans(JournalTabBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("bilans", "un bilan", "bilans", parent)

    def _create_header_widget(self) -> QWidget:
        self._prochain_bilan_label = QLabel()
        self._prochain_bilan_label.setStyleSheet(f"font-weight: bold; color: {self._accent_color};")
        return self._prochain_bilan_label

    def _after_refresh(self, entries: list) -> None:
        if not entries:
            self._prochain_bilan_label.setText("Prochain bilan : aucun bilan enregistré pour l'instant.")
            return
        dernier = entries[0].date  # la liste est triée par date décroissante
        prochain = _add_one_year(dernier)
        self._prochain_bilan_label.setText(
            f"Dernier bilan : {dernier.strftime('%d/%m/%Y')}    —    "
            f"Prochain bilan prévu : {prochain.strftime('%d/%m/%Y')}"
        )
