"""CRUD des bilans (date, type, document joint, note).

Le document joint n'est qu'une RÉFÉRENCE de chemin (colonne `document` en
base, réutilisée telle quelle — pas de migration nécessaire), pas une copie :
si le fichier est déplacé ou supprimé, le lien ne s'ouvre plus."""
from __future__ import annotations

from datetime import date as date_type

from db.database import session_scope
from db.model import Bilan
from services.dto import BilanDTO
from services.type_bilan_service import to_dto as type_bilan_to_dto


def to_dto(bilan: Bilan) -> BilanDTO:
    return BilanDTO(
        id=bilan.id,
        patient_id=bilan.patient_id,
        date=bilan.date,
        type_bilan=type_bilan_to_dto(bilan.type_bilan) if bilan.type_bilan_id else None,
        document_path=bilan.document,
        note=bilan.note,
    )


def list_for_patient(patient_id: int) -> list[BilanDTO]:
    with session_scope() as session:
        bilans = (
            session.query(Bilan)
            .filter(Bilan.patient_id == patient_id)
            .order_by(Bilan.date.desc(), Bilan.id.desc())
            .all()
        )
        return [to_dto(b) for b in bilans]


def add_entry(
    patient_id: int,
    entry_date: date_type,
    *,
    type_bilan_id: int | None,
    document_path: str | None,
    note: str,
) -> BilanDTO:
    with session_scope() as session:
        bilan = Bilan(
            patient_id=patient_id,
            date=entry_date,
            type_bilan_id=type_bilan_id,
            document=document_path,
            note=note.strip(),
        )
        session.add(bilan)
        session.flush()
        return to_dto(bilan)


def update_entry(
    bilan_id: int,
    *,
    entry_date: date_type,
    type_bilan_id: int | None,
    document_path: str | None,
    note: str,
) -> None:
    with session_scope() as session:
        bilan = session.get(Bilan, bilan_id)
        if bilan is None:
            raise ValueError(f"Bilan {bilan_id} introuvable")
        bilan.date = entry_date
        bilan.type_bilan_id = type_bilan_id
        bilan.document = document_path
        bilan.note = note.strip()


def delete_entry(bilan_id: int) -> None:
    with session_scope() as session:
        bilan = session.get(Bilan, bilan_id)
        if bilan is not None:
            session.delete(bilan)
