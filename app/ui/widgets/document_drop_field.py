"""Champ « document joint » : glisser-déposer un fichier ou le choisir via
Parcourir, affichage en lien cliquable qui l'ouvre avec l'application par
défaut du système (Sumatra pour un PDF, etc. — géré par l'OS, pas par nous).

On ne stocke qu'un CHEMIN vers le fichier (pas de copie, pas de chiffrement
du contenu) : si le fichier est déplacé ou supprimé, le lien ne s'ouvre plus.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from ui import theme


def document_link_html(document_path: str | None) -> str:
    """HTML pour un lien cliquable vers `document_path` (utilisé aussi par la
    carte de résumé d'un bilan). Retourne une chaîne vide si pas de document."""
    if not document_path:
        return ""
    name = Path(document_path).name
    if Path(document_path).exists():
        return f'<a href="open" style="color:{theme.SELECTION};">📎 {name}</a>'
    return f'📎 {name} <span style="color:{theme.TEXT_DARK};">(fichier introuvable)</span>'


def open_document(document_path: str | None, parent: QWidget | None = None) -> None:
    if document_path and Path(document_path).exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(document_path))


class DocumentDropField(QWidget):
    """Glisser-déposer + Parcourir + lien cliquable + Retirer."""

    path_changed = Signal()

    def __init__(self, path: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._path = path

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._link_label = QLabel()
        self._link_label.setTextFormat(Qt.TextFormat.RichText)
        self._link_label.linkActivated.connect(self._on_link_clicked)
        layout.addWidget(self._link_label, stretch=1)

        self._browse_btn = QPushButton("Parcourir…")
        self._browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self._browse_btn)

        self._remove_btn = QPushButton("Retirer")
        self._remove_btn.clicked.connect(self._on_remove)
        theme.tag_button(self._remove_btn, "delete")
        layout.addWidget(self._remove_btn)

        self._refresh_display()

    def path(self) -> str | None:
        return self._path

    def set_path(self, path: str | None) -> None:
        self._path = path
        self._refresh_display()

    def _refresh_display(self) -> None:
        if self._path:
            self._link_label.setText(document_link_html(self._path))
        else:
            self._link_label.setText(
                "<i>Aucun document — glissez un fichier ici ou cliquez sur Parcourir</i>"
            )
        self._remove_btn.setEnabled(self._path is not None)

    def _on_link_clicked(self, _href: str) -> None:
        open_document(self._path, self)

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choisir un document")
        if path:
            self.set_path(path)
            self.path_changed.emit()

    def _on_remove(self) -> None:
        self.set_path(None)
        self.path_changed.emit()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            self.set_path(urls[0].toLocalFile())
            self.path_changed.emit()
