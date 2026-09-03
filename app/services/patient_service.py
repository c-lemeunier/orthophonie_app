"""CRUD patients — seule couche du domaine qui parle à SQLAlchemy pour ce sujet."""
from __future__ import annotations

from datetime import date

from db.database import session_scope
from db.model import Patient
from services.dto import PatientDTO


def to_dto(patient: Patient) -> PatientDTO:
    return PatientDTO(
        id=patient.id,
        nom=patient.nom,
        prenom=patient.prenom,
        date_naissance=patient.date_naissance,
        date_debut=patient.date_debut,
        diagnostic=patient.diagnostic,
        frequence=patient.frequence,
    )


def list_all() -> list[PatientDTO]:
    with session_scope() as session:
        patients = session.query(Patient).order_by(Patient.nom, Patient.prenom).all()
        return [to_dto(p) for p in patients]


def get(patient_id: int) -> PatientDTO | None:
    with session_scope() as session:
        patient = session.get(Patient, patient_id)
        return to_dto(patient) if patient else None


def create(nom: str, prenom: str) -> PatientDTO:
    with session_scope() as session:
        patient = Patient(nom=nom.strip(), prenom=prenom.strip())
        session.add(patient)
        session.flush()
        return to_dto(patient)


def update_infos(
    patient_id: int,
    *,
    nom: str,
    prenom: str,
    date_naissance: date | None,
    date_debut: date | None,
    diagnostic: str | None,
    frequence: str | None,
) -> PatientDTO:
    with session_scope() as session:
        patient = session.get(Patient, patient_id)
        if patient is None:
            raise ValueError(f"Patient {patient_id} introuvable")
        patient.nom = nom.strip()
        patient.prenom = prenom.strip()
        patient.date_naissance = date_naissance
        patient.date_debut = date_debut
        patient.diagnostic = diagnostic
        patient.frequence = frequence
        session.flush()
        return to_dto(patient)


def delete(patient_id: int) -> None:
    with session_scope() as session:
        patient = session.get(Patient, patient_id)
        if patient is not None:
            session.delete(patient)
