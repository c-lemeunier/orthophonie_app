from datetime import date

from db.database import session_scope
from db.model import GrandObjectif, Patient, PetitObjectif, StatutObjectif


def test_create_patient_and_query():
    with session_scope() as session:
        session.add(Patient(nom="Dupont", prenom="Alice"))

    with session_scope() as session:
        patient = session.query(Patient).one()
        assert patient.nom_complet == "Dupont Alice"


def test_grand_objectif_cascade_delete_removes_petits():
    with session_scope() as session:
        patient = Patient(nom="Martin", prenom="Bob")
        session.add(patient)
        session.flush()
        grand = GrandObjectif(patient_id=patient.id, libelle="Articulation", statut=StatutObjectif.EN_COURS)
        session.add(grand)
        session.flush()
        session.add(PetitObjectif(grand_objectif_id=grand.id, libelle="Son [s]"))
        grand_id = grand.id

    with session_scope() as session:
        session.delete(session.get(GrandObjectif, grand_id))

    with session_scope() as session:
        assert session.query(PetitObjectif).count() == 0


def test_patient_delete_cascades_to_objectifs():
    with session_scope() as session:
        patient = Patient(nom="Petit", prenom="Chloé", date_naissance=date(2015, 1, 1))
        session.add(patient)
        session.flush()
        session.add(GrandObjectif(patient_id=patient.id, libelle="Langage oral"))
        patient_id = patient.id

    with session_scope() as session:
        session.delete(session.get(Patient, patient_id))

    with session_scope() as session:
        assert session.query(GrandObjectif).count() == 0
