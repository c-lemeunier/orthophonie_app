from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ui.tabs.journal_tab_base import JournalTabBase


class TabNotes(JournalTabBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("notes", "une note", parent)
