"""CRUD réunions équipe/synthèses, avec participants et patients concernés."""
from __future__ import annotations

from datetime import date as date_type

from db.database import session_scope
from db.model import Reunion, ReunionIntervenant, ReunionPatient
from services.dto import ReunionDTO
from services.intervenant_service import to_dto as intervenant_to_dto
from services.patient_service import to_dto as patient_to_dto


def _to_dto(reunion: Reunion) -> ReunionDTO:
    return ReunionDTO(
        id=reunion.id,
        date=reunion.date,
        type_reunion=reunion.type_reunion,
        note=reunion.note,
        participants=[intervenant_to_dto(l.intervenant) for l in reunion.intervenants_links],
        patients=[patient_to_dto(l.patient) for l in reunion.patients_links],
    )


def list_all() -> list[ReunionDTO]:
    with session_scope() as session:
        reunions = session.query(Reunion).order_by(Reunion.date.desc()).all()
        return [_to_dto(r) for r in reunions]


def get(reunion_id: int) -> ReunionDTO | None:
    with session_scope() as session:
        reunion = session.get(Reunion, reunion_id)
        return _to_dto(reunion) if reunion else None


def create(
    *,
    date: date_type,
    type_reunion: str,
    note: str | None,
    intervenant_ids: list[int],
    patient_ids: list[int],
) -> ReunionDTO:
    with session_scope() as session:
        reunion = Reunion(date=date, type_reunion=type_reunion.strip(), note=note)
        session.add(reunion)
        session.flush()
        _sync_links(session, reunion, intervenant_ids, patient_ids)
        session.flush()
        return _to_dto(reunion)


def update(
    reunion_id: int,
    *,
    date: date_type,
    type_reunion: str,
    note: str | None,
    intervenant_ids: list[int],
    patient_ids: list[int],
) -> ReunionDTO:
    with session_scope() as session:
        reunion = session.get(Reunion, reunion_id)
        if reunion is None:
            raise ValueError(f"Réunion {reunion_id} introuvable")
        reunion.date = date
        reunion.type_reunion = type_reunion.strip()
        reunion.note = note
        for lien in list(reunion.intervenants_links):
            session.delete(lien)
        for lien in list(reunion.patients_links):
            session.delete(lien)
        session.flush()
        _sync_links(session, reunion, intervenant_ids, patient_ids)
        session.flush()
        return _to_dto(reunion)


def _sync_links(session, reunion: Reunion, intervenant_ids: list[int], patient_ids: list[int]) -> None:
    for intervenant_id in intervenant_ids:
        session.add(ReunionIntervenant(reunion_id=reunion.id, intervenant_id=intervenant_id))
    for patient_id in patient_ids:
        session.add(ReunionPatient(reunion_id=reunion.id, patient_id=patient_id))


def delete(reunion_id: int) -> None:
    with session_scope() as session:
        reunion = session.get(Reunion, reunion_id)
        if reunion is not None:
            session.delete(reunion)
