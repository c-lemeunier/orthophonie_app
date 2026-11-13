"""Champ « document joint » : glisser-déposer un fichier ou le choisir via
Parcourir, affichage en lien cliquable qui l'ouvre avec l'application par
défaut du système (Sumatra pour un PDF, etc. — géré par l'OS, pas par nous).

On ne stocke qu'un CHEMIN vers le fichier (pas de copie, pas de chiffrement
du contenu). Le chemin est résolu via `services.document_resolver` (redirection
OneDrive du Bureau/Documents, changement de profil…) ; s'il reste introuvable,
un lien « Relocaliser… » permet de re-sélectionner le fichier.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services import document_resolver
from ui import theme

HREF_OPEN = "open"
HREF_RELINK = "relink"

_STYLE_EMPTY = f"""
    QLabel {{
        border: 2px dashed {theme.BORDER};
        border-radius: 6px;
        background-color: {theme.CREAM_ALT};
        color: {theme.TEXT_DARK};
        padding: 14px;
    }}
"""
_STYLE_EMPTY_HOVER = f"""
    QLabel {{
        border: 2px dashed {theme.SELECTION};
        border-radius: 6px;
        background-color: {theme.CREAM_ALT};
        color: {theme.TEXT_DARK};
        padding: 14px;
    }}
"""
_STYLE_FILLED = f"""
    QLabel {{
        border: 1px solid {theme.BORDER};
        border-radius: 6px;
        background-color: {theme.CREAM};
        padding: 10px 14px;
    }}
"""


def document_link_html(document_path: str | None) -> str:
    """HTML pour un lien cliquable vers `document_path` (utilisé aussi par la
    carte de résumé d'un bilan). Retourne une chaîne vide si pas de document.
    Si le fichier est introuvable, propose un lien « Relocaliser… »."""
    if not document_path:
        return ""
    resolved = document_resolver.resolve(document_path)
    if resolved is not None:
        return f'📎 <a href="{HREF_OPEN}" style="color:{theme.SELECTION};">{escape(resolved.name)}</a>'
    name = escape(Path(document_resolver.normalize(document_path) or document_path).name)
    return (
        f'📎 {name} <span style="color:{theme.TEXT_DARK};">(fichier introuvable)</span> '
        f'<a href="{HREF_RELINK}" style="color:{theme.SELECTION};">Relocaliser…</a>'
    )


def document_tooltip(document_path: str | None) -> str:
    """Chemin complet enregistré (diagnostic) et, si différent, celui utilisé."""
    if not document_path:
        return ""
    resolved = document_resolver.resolve(document_path)
    tooltip = f"Chemin enregistré : {document_path}"
    if resolved is None:
        tooltip += "\nFichier introuvable à cet emplacement."
    elif str(resolved) != document_resolver.normalize(document_path):
        tooltip += f"\nRetrouvé ici : {resolved}"
    return tooltip


def open_document(document_path: str | None, parent: QWidget | None = None) -> None:
    if not document_path:
        return
    resolved = document_resolver.resolve(document_path)
    if resolved is None:
        QMessageBox.warning(parent, "Document introuvable", f"Fichier introuvable :\n{document_path}")
        return
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved))):
        QMessageBox.warning(
            parent,
            "Ouverture impossible",
            f"Impossible d'ouvrir le document avec l'application par défaut :\n{resolved}",
        )


def choose_document(parent: QWidget | None, current_path: str | None = None) -> str | None:
    """Sélecteur de fichier ouvert au dossier existant le plus proche du
    chemin actuel. Retourne le chemin choisi ou None."""
    start_dir = document_resolver.closest_existing_dir(current_path)
    path, _ = QFileDialog.getOpenFileName(parent, "Choisir un document", start_dir)
    return path or None


class _DropLabel(QLabel):
    """Le glisser-déposer doit être accepté par le widget précisément situé
    sous le curseur — un `QWidget` parent avec `setAcceptDrops(True)` ne
    reçoit RIEN si l'enfant qui couvre la zone (ce label) ne l'accepte pas
    aussi lui-même. C'est ce qui rendait le dépôt inopérant auparavant."""

    file_dropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(56)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            if not self.property("hasDocument"):
                self.setStyleSheet(_STYLE_EMPTY_HOVER)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        if not self.property("hasDocument"):
            self.setStyleSheet(_STYLE_EMPTY)

    def dropEvent(self, event) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())


class DocumentDropField(QWidget):
    """Zone de dépôt bien visible (bordure en pointillés tant que vide) +
    Parcourir + lien cliquable + Retirer."""

    path_changed = Signal()

    def __init__(self, path: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._drop_label = _DropLabel()
        self._drop_label.setTextFormat(Qt.TextFormat.RichText)
        self._drop_label.linkActivated.connect(self._on_link_clicked)
        self._drop_label.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self._drop_label)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self._browse_btn = QPushButton("Parcourir…")
        self._browse_btn.clicked.connect(self._on_browse)
        buttons_row.addWidget(self._browse_btn)

        self._remove_btn = QPushButton("Retirer")
        self._remove_btn.clicked.connect(self._on_remove)
        theme.tag_button(self._remove_btn, "delete")
        buttons_row.addWidget(self._remove_btn)
        layout.addLayout(buttons_row)

        self._refresh_display()

    def path(self) -> str | None:
        return self._path

    def set_path(self, path: str | None) -> None:
        self._path = path
        self._refresh_display()

    def _refresh_display(self) -> None:
        if self._path:
            self._drop_label.setText(document_link_html(self._path))
            self._drop_label.setToolTip(document_tooltip(self._path))
            self._drop_label.setProperty("hasDocument", True)
            self._drop_label.setStyleSheet(_STYLE_FILLED)
        else:
            self._drop_label.setToolTip("")
            self._drop_label.setText("📄  Glissez un fichier ici, ou cliquez sur « Parcourir »")
            self._drop_label.setProperty("hasDocument", False)
            self._drop_label.setStyleSheet(_STYLE_EMPTY)
        self._remove_btn.setEnabled(self._path is not None)

    def _on_link_clicked(self, href: str) -> None:
        if href == HREF_RELINK:
            self._on_browse()
        else:
            open_document(self._path, self)

    def _on_file_dropped(self, path: str) -> None:
        self.set_path(path)
        self.path_changed.emit()

    def _on_browse(self) -> None:
        path = choose_document(self, self._path)
        if path:
            self.set_path(path)
            self.path_changed.emit()

    def _on_remove(self) -> None:
        self.set_path(None)
        self.path_changed.emit()
