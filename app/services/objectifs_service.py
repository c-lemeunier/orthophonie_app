"""CRUD grands objectifs / petits objectifs, statut sur les deux niveaux."""
from __future__ import annotations

from db.database import session_scope
from db.model import GrandObjectif, PetitObjectif, StatutObjectif
from services.dto import GrandObjectifDTO, PetitObjectifDTO


def _petit_to_dto(petit: PetitObjectif) -> PetitObjectifDTO:
    return PetitObjectifDTO(
        id=petit.id,
        grand_objectif_id=petit.grand_objectif_id,
        libelle=petit.libelle,
        statut=petit.statut,
        ordre=petit.ordre,
    )


def _grand_to_dto(grand: GrandObjectif) -> GrandObjectifDTO:
    return GrandObjectifDTO(
        id=grand.id,
        patient_id=grand.patient_id,
        libelle=grand.libelle,
        statut=grand.statut,
        ordre=grand.ordre,
        petits_objectifs=[_petit_to_dto(p) for p in grand.petits_objectifs],
    )


def list_for_patient(patient_id: int) -> list[GrandObjectifDTO]:
    with session_scope() as session:
        grands = (
            session.query(GrandObjectif)
            .filter(GrandObjectif.patient_id == patient_id)
            .order_by(GrandObjectif.ordre, GrandObjectif.id)
            .all()
        )
        return [_grand_to_dto(g) for g in grands]


def add_grand_objectif(
    patient_id: int, libelle: str, statut: StatutObjectif = StatutObjectif.A_TRAVAILLER
) -> GrandObjectifDTO:
    with session_scope() as session:
        ordre_max = (
            session.query(GrandObjectif)
            .filter(GrandObjectif.patient_id == patient_id)
            .count()
        )
        grand = GrandObjectif(
            patient_id=patient_id, libelle=libelle.strip(), statut=statut, ordre=ordre_max
        )
        session.add(grand)
        session.flush()
        return _grand_to_dto(grand)


def add_petit_objectif(
    grand_objectif_id: int, libelle: str, statut: StatutObjectif = StatutObjectif.A_TRAVAILLER
) -> PetitObjectifDTO:
    with session_scope() as session:
        ordre_max = (
            session.query(PetitObjectif)
            .filter(PetitObjectif.grand_objectif_id == grand_objectif_id)
            .count()
        )
        petit = PetitObjectif(
            grand_objectif_id=grand_objectif_id, libelle=libelle.strip(), statut=statut, ordre=ordre_max
        )
        session.add(petit)
        session.flush()
        return _petit_to_dto(petit)


def update_grand_objectif(
    grand_objectif_id: int, *, libelle: str | None = None, statut: StatutObjectif | None = None
) -> None:
    with session_scope() as session:
        grand = session.get(GrandObjectif, grand_objectif_id)
        if grand is None:
            raise ValueError(f"Grand objectif {grand_objectif_id} introuvable")
        if libelle is not None:
            grand.libelle = libelle.strip()
        if statut is not None:
            grand.statut = statut


def update_petit_objectif(
    petit_objectif_id: int, *, libelle: str | None = None, statut: StatutObjectif | None = None
) -> None:
    with session_scope() as session:
        petit = session.get(PetitObjectif, petit_objectif_id)
        if petit is None:
            raise ValueError(f"Petit objectif {petit_objectif_id} introuvable")
        if libelle is not None:
            petit.libelle = libelle.strip()
        if statut is not None:
            petit.statut = statut


def delete_grand_objectif(grand_objectif_id: int) -> None:
    with session_scope() as session:
        grand = session.get(GrandObjectif, grand_objectif_id)
        if grand is not None:
            session.delete(grand)


def delete_petit_objectif(petit_objectif_id: int) -> None:
    with session_scope() as session:
        petit = session.get(PetitObjectif, petit_objectif_id)
        if petit is not None:
            session.delete(petit)
