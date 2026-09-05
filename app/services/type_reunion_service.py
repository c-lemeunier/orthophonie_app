"""CRUD de l'annuaire des types de réunion (géré par l'utilisateur)."""
from __future__ import annotations

from db.database import session_scope
from db.model import TypeReunion
from services.dto import TypeReunionDTO


def to_dto(type_reunion: TypeReunion) -> TypeReunionDTO:
    return TypeReunionDTO(id=type_reunion.id, libelle=type_reunion.libelle)


def list_all() -> list[TypeReunionDTO]:
    with session_scope() as session:
        types = session.query(TypeReunion).order_by(TypeReunion.libelle).all()
        return [to_dto(t) for t in types]


def create(libelle: str) -> TypeReunionDTO:
    with session_scope() as session:
        type_reunion = TypeReunion(libelle=libelle.strip())
        session.add(type_reunion)
        session.flush()
        return to_dto(type_reunion)


def update(type_reunion_id: int, libelle: str) -> None:
    with session_scope() as session:
        type_reunion = session.get(TypeReunion, type_reunion_id)
        if type_reunion is None:
            raise ValueError(f"Type de réunion {type_reunion_id} introuvable")
        type_reunion.libelle = libelle.strip()


def delete(type_reunion_id: int) -> None:
    with session_scope() as session:
        type_reunion = session.get(TypeReunion, type_reunion_id)
        if type_reunion is not None:
            session.delete(type_reunion)
