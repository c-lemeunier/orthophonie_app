"""QTextEdit qui colle toujours en texte brut.

Par défaut, QTextEdit conserve la mise en forme (police, taille, couleur...)
du texte copié depuis un autre document (Word, PDF, navigateur...). On ne
veut pas de cet héritage de police dans nos champs de note : tout texte
collé doit reprendre la police du champ.
"""
from __future__ import annotations

from PySide6.QtGui import QTextDocumentFragment
from PySide6.QtWidgets import QTextEdit


class PlainTextEdit(QTextEdit):
    def insertFromMimeData(self, source) -> None:  # noqa: N802
        if source.hasText():
            fragment = QTextDocumentFragment.fromPlainText(source.text())
            self.textCursor().insertFragment(fragment)
        else:
            super().insertFromMimeData(source)
