"""Constantes visuelles partagées (couleurs de statut, etc.)."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

from db.model import StatutObjectif

STATUT_COLORS: dict[StatutObjectif, QColor] = {
    StatutObjectif.A_TRAVAILLER: QColor("#e74c3c"),
    StatutObjectif.EN_COURS: QColor("#f39c12"),
    StatutObjectif.ATTEINT: QColor("#27ae60"),
}

STATUT_LABELS: dict[StatutObjectif, str] = {
    StatutObjectif.A_TRAVAILLER: "À travailler",
    StatutObjectif.EN_COURS: "En cours",
    StatutObjectif.ATTEINT: "Atteint",
}

_ICON_CACHE: dict[StatutObjectif, QIcon] = {}


def statut_icon(statut: StatutObjectif, size: int = 12) -> QIcon:
    if statut not in _ICON_CACHE:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(STATUT_COLORS[statut])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.end()
        _ICON_CACHE[statut] = QIcon(pixmap)
    return _ICON_CACHE[statut]


def statut_icon_size() -> QSize:
    return QSize(12, 12)
