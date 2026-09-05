"""Thème visuel de l'application.

- Le fond (fenêtres, dialogs) est terracotta ; le contenu (champs, tableaux,
  cartes) reste sur des panneaux clairs pour la lisibilité.
- Les boutons d'action suivent un code couleur constant dans toute l'app,
  quel que soit l'onglet : vert = ajouter, bleu = modifier/enregistrer,
  rouge = supprimer. Voir `tag_button()`.
- Chaque onglet patient a une couleur d'accent qui lui est propre (roue
  chromatique répartie autour du terracotta), utilisée pour son en-tête de
  tableau/arbre et le liseré en haut de l'onglet. Voir `apply_tab_accent()`.
- La fenêtre de mot de passe (LoginDialog) reste claire plutôt que terracotta
  (voir `LOGIN_DIALOG_OBJECT_NAME`).
"""
from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget

# ---- Palette de base ----
TERRACOTTA = "#C1623F"        # fond principal (fenêtres, barres d'onglets)
TERRACOTTA_DARK = "#A84F30"   # boutons neutres, en-têtes par défaut
TERRACOTTA_DARKER = "#8F3F26"
TERRACOTTA_DARKEST = "#7A3520"
TERRACOTTA_LIGHT = "#DDA47F"  # onglets inactifs
CREAM = "#FBF3EC"             # panneaux de contenu (champs, tableaux, cartes)
CREAM_ALT = "#F2E4D8"         # lignes alternées
BORDER = "#D9B49A"
TEXT_DARK = "#3A2A22"
TEXT_ON_DARK = "#FBF3EC"      # texte clair sur fond foncé (boutons, en-têtes)
SELECTION = "#4F7C74"
DISABLED_BG = "#C9A088"
DISABLED_TEXT = "#EEDFD3"

# ---- Couleurs sémantiques des actions (constantes partout dans l'app) ----
ACTION_COLORS = {
    "add": ("#4F8B5B", "#3E6F48", "#335A3B"),      # Ajouter / Nouveau : vert
    "edit": ("#4A5FA5", "#3C4E88", "#303F70"),     # Modifier / Enregistrer : bleu
    "delete": ("#C0392B", "#A5301F", "#8A2818"),   # Supprimer / Retirer : rouge
}

# ---- Couleurs d'accent par onglet (réparties sur la roue chromatique) ----
TAB_ACCENTS = {
    "infos": "#B8863B",           # Infos personnelles : ambre
    "equipe": "#3D8B82",          # Équipe pluri : sarcelle
    "objectifs": "#4A5FA5",       # Objectifs orthophoniques : bleu-violet
    "coordinations": "#7A4F8B",   # Coordinations : prune
    "bilans": "#A34B6E",          # Derniers bilans : rose foncé
    "notes": "#6B8F4E",           # Notes : vert olive
}

LOGIN_DIALOG_OBJECT_NAME = "loginDialog"


def tag_button(button: QPushButton, role: str) -> None:
    """Applique le code couleur sémantique constant (add/edit/delete) à un bouton."""
    button.setProperty("btnRole", role)


def apply_tab_accent(widget: QWidget, accent_key: str) -> None:
    """Ajoute un liseré de couleur en haut de l'onglet, propre à ce widget."""
    color = TAB_ACCENTS[accent_key]
    object_name = f"tabAccent_{accent_key}"
    widget.setObjectName(object_name)
    widget.setStyleSheet(f"QWidget#{object_name} {{ border-top: 4px solid {color}; }}")


def header_style(accent_key: str) -> str:
    """Style QSS pour l'en-tête (QHeaderView) d'un tableau/arbre, dans la
    couleur d'accent de l'onglet plutôt que le terracotta par défaut."""
    color = TAB_ACCENTS[accent_key]
    return f"""
        QHeaderView::section {{
            background-color: {color};
            color: {TEXT_ON_DARK};
            padding: 5px;
            border: none;
        }}
    """


def _action_qss() -> str:
    rules = []
    for role, (base, hover, pressed) in ACTION_COLORS.items():
        rules.append(f"""
            QPushButton[btnRole="{role}"] {{
                background-color: {base};
                color: {TEXT_ON_DARK};
            }}
            QPushButton[btnRole="{role}"]:hover {{
                background-color: {hover};
            }}
            QPushButton[btnRole="{role}"]:pressed {{
                background-color: {pressed};
            }}
        """)
    return "\n".join(rules)


STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {TERRACOTTA};
}}

QDialog#{LOGIN_DIALOG_OBJECT_NAME} {{
    background-color: {CREAM};
}}

QWidget {{
    color: {TEXT_DARK};
    font-size: 10pt;
}}

QLabel {{
    background: transparent;
}}

QTabWidget::pane {{
    background: {CREAM};
    border: 1px solid {BORDER};
    border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{
    background: {TERRACOTTA_LIGHT};
    /* pas de `color` ici : laisse `setTabTextColor()` donner sa couleur
       d'accent au libellé de chaque onglet (voir MainWindow). */
    padding: 6px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {CREAM};
    font-weight: bold;
}}

QLineEdit, QTextEdit, QDateEdit, QComboBox, QAbstractSpinBox {{
    background-color: {CREAM};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 3px 5px;
    color: {TEXT_DARK};
    selection-background-color: {SELECTION};
    selection-color: {CREAM};
}}

QLineEdit:disabled, QTextEdit:disabled, QDateEdit:disabled, QComboBox:disabled {{
    background-color: {DISABLED_BG};
    color: {DISABLED_TEXT};
}}

QTableView, QTreeWidget, QListWidget {{
    background-color: {CREAM};
    alternate-background-color: {CREAM_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
    color: {TEXT_DARK};
    selection-background-color: {SELECTION};
    selection-color: {CREAM};
}}

QHeaderView::section {{
    background-color: {TERRACOTTA_DARK};
    color: {TEXT_ON_DARK};
    padding: 5px;
    border: none;
    border-right: 1px solid {TERRACOTTA_DARKER};
}}

QPushButton {{
    background-color: {TERRACOTTA_DARK};
    color: {TEXT_ON_DARK};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
}}

QPushButton:hover {{
    background-color: {TERRACOTTA_DARKER};
}}

QPushButton:pressed {{
    background-color: {TERRACOTTA_DARKEST};
}}

QPushButton:disabled {{
    background-color: {DISABLED_BG};
    color: {DISABLED_TEXT};
}}

{_action_qss()}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: {TERRACOTTA_LIGHT};
    width: 12px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: {TERRACOTTA_DARK};
    border-radius: 6px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

_EntryCard {{
    background-color: {CREAM};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

QCheckBox, QRadioButton {{
    background: transparent;
}}
"""
