"""Données par défaut, insérées de façon idempotente au premier lancement.

Le schéma est déjà créé par `database.init_engine()`. Cette fonction ne fait
rien de destructif : elle peut être rappelée à chaque démarrage sans effet
de bord si les données par défaut sont déjà présentes.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

DEFAULT_TYPES_REUNION = [
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
    """Types de réunion par défaut, uniquement si l'annuaire est encore vide
    (ni déjà peuplé par l'utilisateur, ni par la migration des anciennes
    valeurs texte libre — voir db/database.py::_migrate_reunion_types)."""
    from db.model import TypeReunion

    if session.query(TypeReunion).count() == 0:
        for libelle in DEFAULT_TYPES_REUNION:
            session.add(TypeReunion(libelle=libelle))
