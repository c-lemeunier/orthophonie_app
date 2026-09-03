"""CRUD générique pour les 3 tables (date, note) : coordinations, bilans, notes."""
from __future__ import annotations

from datetime import date as date_type
from typing import Literal

from db.database import session_scope
from db.model import Bilan, Coordination, Note
from services.dto import JournalEntryDTO

JournalKind = Literal["coordinations", "bilans", "notes"]

_MODELS = {
    "coordinations": Coordination,
    "bilans": Bilan,
    "notes": Note,
}


def _model_for(kind: JournalKind):
    try:
        return _MODELS[kind]
    except KeyError as exc:
        raise ValueError(f"Type de journal inconnu : {kind}") from exc


def _to_dto(entry) -> JournalEntryDTO:
    return JournalEntryDTO(id=entry.id, patient_id=entry.patient_id, date=entry.date, note=entry.note)


def list_for_patient(kind: JournalKind, patient_id: int) -> list[JournalEntryDTO]:
    model = _model_for(kind)
    with session_scope() as session:
        entries = (
            session.query(model)
            .filter(model.patient_id == patient_id)
            .order_by(model.date.desc(), model.id.desc())
            .all()
        )
        return [_to_dto(e) for e in entries]


def add_entry(kind: JournalKind, patient_id: int, entry_date: date_type, note: str) -> JournalEntryDTO:
    model = _model_for(kind)
    with session_scope() as session:
        entry = model(patient_id=patient_id, date=entry_date, note=note.strip())
        session.add(entry)
        session.flush()
        return _to_dto(entry)


def update_entry(kind: JournalKind, entry_id: int, *, entry_date: date_type, note: str) -> None:
    model = _model_for(kind)
    with session_scope() as session:
        entry = session.get(model, entry_id)
        if entry is None:
            raise ValueError(f"Entrée {entry_id} introuvable dans {kind}")
        entry.date = entry_date
        entry.note = note.strip()


def delete_entry(kind: JournalKind, entry_id: int) -> None:
    model = _model_for(kind)
    with session_scope() as session:
        entry = session.get(model, entry_id)
        if entry is not None:
            session.delete(entry)
