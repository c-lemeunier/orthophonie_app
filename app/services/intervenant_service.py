"""Annuaire global d'intervenants + liens équipe pluri par patient."""
from __future__ import annotations

from db.database import session_scope
from db.model import Intervenant, PatientIntervenant
from services.dto import IntervenantDTO, PatientIntervenantDTO


def to_dto(intervenant: Intervenant) -> IntervenantDTO:
    return IntervenantDTO(
        id=intervenant.id,
        nom=intervenant.nom,
        fonction=intervenant.fonction,
        actif=intervenant.actif,
    )


def list_annuaire(*, actifs_seulement: bool = True) -> list[IntervenantDTO]:
    with session_scope() as session:
        query = session.query(Intervenant)
        if actifs_seulement:
            query = query.filter(Intervenant.actif.is_(True))
        intervenants = query.order_by(Intervenant.nom).all()
        return [to_dto(i) for i in intervenants]


def create_intervenant(nom: str, fonction: str) -> IntervenantDTO:
    with session_scope() as session:
        intervenant = Intervenant(nom=nom.strip(), fonction=fonction.strip())
        session.add(intervenant)
        session.flush()
        return to_dto(intervenant)


def list_equipe_patient(patient_id: int) -> list[PatientIntervenantDTO]:
    with session_scope() as session:
        liens = (
            session.query(PatientIntervenant)
            .filter(PatientIntervenant.patient_id == patient_id)
            .join(PatientIntervenant.intervenant)
            .order_by(Intervenant.nom)
            .all()
        )
        return [
            PatientIntervenantDTO(
                lien_id=lien.id,
                intervenant=to_dto(lien.intervenant),
                role_specifique=lien.role_specifique,
            )
            for lien in liens
        ]


def ajouter_a_equipe(
    patient_id: int, intervenant_id: int, role_specifique: str | None = None
) -> None:
    with session_scope() as session:
        existe = (
            session.query(PatientIntervenant)
            .filter_by(patient_id=patient_id, intervenant_id=intervenant_id)
            .first()
        )
        if existe is not None:
            return
        session.add(
            PatientIntervenant(
                patient_id=patient_id,
                intervenant_id=intervenant_id,
                role_specifique=role_specifique,
            )
        )


def retirer_de_equipe(lien_id: int) -> None:
    with session_scope() as session:
        lien = session.get(PatientIntervenant, lien_id)
        if lien is not None:
            session.delete(lien)
