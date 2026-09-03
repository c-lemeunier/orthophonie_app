"""Données par défaut, insérées de façon idempotente au premier lancement.

Le schéma est déjà créé par `database.init_engine()`. Cette fonction ne fait
rien de destructif : elle peut être rappelée à chaque démarrage sans effet
de bord si les données par défaut sont déjà présentes.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

SUGGESTIONS_TYPE_REUNION = [
    "Synthèse",
    "Réunion de coordination",
    "Réunion de rentrée",
    "Point d'équipe",
]

SUGGESTIONS_FREQUENCE = [
    "1x/semaine",
    "2x/semaine",
    "1x/15 jours",
    "1x/mois",
]


def seed_default_data(session: Session) -> None:
    """Point d'extension pour des données par défaut futures (aucune table de
    référence à peupler en v1 : les intervenants et types de réunion sont
    propres à chaque praticien et saisis librement)."""
    return None
