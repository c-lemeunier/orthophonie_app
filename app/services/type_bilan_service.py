"""CRUD de l'annuaire des types de bilan (géré par l'utilisateur)."""
from __future__ import annotations

from db.database import session_scope
from db.model import TypeBilan
from services.dto import TypeBilanDTO


def to_dto(type_bilan: TypeBilan) -> TypeBilanDTO:
    return TypeBilanDTO(id=type_bilan.id, libelle=type_bilan.libelle)


def list_all() -> list[TypeBilanDTO]:
    with session_scope() as session:
        types = session.query(TypeBilan).order_by(TypeBilan.libelle).all()
        return [to_dto(t) for t in types]


def create(libelle: str) -> TypeBilanDTO:
    with session_scope() as session:
        type_bilan = TypeBilan(libelle=libelle.strip())
        session.add(type_bilan)
        session.flush()
        return to_dto(type_bilan)


def update(type_bilan_id: int, libelle: str) -> None:
    with session_scope() as session:
        type_bilan = session.get(TypeBilan, type_bilan_id)
        if type_bilan is None:
            raise ValueError(f"Type de bilan {type_bilan_id} introuvable")
        type_bilan.libelle = libelle.strip()


def delete(type_bilan_id: int) -> None:
    with session_scope() as session:
        type_bilan = session.get(TypeBilan, type_bilan_id)
        if type_bilan is not None:
            session.delete(type_bilan)
