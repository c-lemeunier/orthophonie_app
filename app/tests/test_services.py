from datetime import date

from db.model import StatutObjectif
from services import (
    bilan_service,
    intervenant_service,
    journal_service,
    objectifs_service,
    patient_service,
    reunion_service,
    type_bilan_service,
    type_reunion_service,
)


def test_patient_crud():
    patient = patient_service.create("Dupont", "Alice")
    assert patient.id is not None

    patient_service.update_infos(
        patient.id, nom="Dupont", prenom="Alicia",
        date_naissance=date(2010, 5, 1), date_debut=date(2023, 9, 1),
        diagnostic="Trouble du langage", frequence="1x/semaine",
        classe="CE2", email_parent1="parent1@example.com", email_parent2="parent2@example.com",
    )
    reloaded = patient_service.get(patient.id)
    assert reloaded.prenom == "Alicia"
    assert reloaded.frequence == "1x/semaine"
    assert reloaded.classe == "CE2"
    assert reloaded.email_parent1 == "parent1@example.com"
    assert reloaded.email_parent2 == "parent2@example.com"

    patient_service.delete(patient.id)
    assert patient_service.get(patient.id) is None


def test_patient_age():
    from services.dto import compute_age

    assert compute_age(date(2015, 6, 15), today=date(2024, 6, 14)) == 8
    assert compute_age(date(2015, 6, 15), today=date(2024, 6, 15)) == 9
    assert compute_age(date(2015, 6, 15), today=date(2024, 6, 16)) == 9


def test_equipe_pluri_annuaire_partage():
    patient1 = patient_service.create("A", "A")
    patient2 = patient_service.create("B", "B")
    intervenant = intervenant_service.create_intervenant("Dr Martin", "Médecin")

    intervenant_service.ajouter_a_equipe(patient1.id, intervenant.id)
    intervenant_service.ajouter_a_equipe(patient2.id, intervenant.id)

    equipe1 = intervenant_service.list_equipe_patient(patient1.id)
    equipe2 = intervenant_service.list_equipe_patient(patient2.id)
    assert equipe1[0].intervenant.id == intervenant.id
    assert equipe2[0].intervenant.id == intervenant.id

    intervenant_service.retirer_de_equipe(equipe1[0].lien_id)
    assert intervenant_service.list_equipe_patient(patient1.id) == []
    # L'intervenant reste dans l'annuaire et lié au patient 2
    assert len(intervenant_service.list_annuaire()) == 1
    assert len(intervenant_service.list_equipe_patient(patient2.id)) == 1


def test_objectifs_statuts_grand_et_petit():
    patient = patient_service.create("C", "C")
    grand = objectifs_service.add_grand_objectif(patient.id, "Articulation")
    petit = objectifs_service.add_petit_objectif(grand.id, "Son [s]")

    objectifs_service.update_grand_objectif(grand.id, statut=StatutObjectif.EN_COURS)
    objectifs_service.update_petit_objectif(petit.id, statut=StatutObjectif.ATTEINT)

    grands = objectifs_service.list_for_patient(patient.id)
    assert grands[0].statut == StatutObjectif.EN_COURS
    assert grands[0].petits_objectifs[0].statut == StatutObjectif.ATTEINT


def test_journal_coordinations_et_notes_isoles():
    patient = patient_service.create("D", "D")
    journal_service.add_entry("coordinations", patient.id, date(2024, 1, 1), "Coordination 1")
    journal_service.add_entry("notes", patient.id, date(2024, 3, 1), "Note 1")

    assert len(journal_service.list_for_patient("coordinations", patient.id)) == 1
    assert len(journal_service.list_for_patient("notes", patient.id)) == 1


def test_type_bilan_crud_et_bilan_avec_type_et_document():
    patient = patient_service.create("F", "F")
    type_initial = type_bilan_service.create("Bilan initial")
    type_bilan_service.create("Bilan de renouvellement")
    assert len(type_bilan_service.list_all()) == 2

    bilan = bilan_service.add_entry(
        patient.id, date(2024, 6, 15),
        type_bilan_id=type_initial.id, document_path="/tmp/compte-rendu.pdf",
        note="Retard modéré, bonne coopération.",
    )
    assert bilan.type_bilan.libelle == "Bilan initial"
    assert bilan.document_path == "/tmp/compte-rendu.pdf"

    # Renommer le type se répercute sur le bilan
    type_bilan_service.update(type_initial.id, "Bilan initial (renommé)")
    reloaded = bilan_service.list_for_patient(patient.id)[0]
    assert reloaded.type_bilan.libelle == "Bilan initial (renommé)"

    # Supprimer le type ne supprime pas le bilan, il perd juste son type
    type_bilan_service.delete(type_initial.id)
    reloaded = bilan_service.list_for_patient(patient.id)[0]
    assert reloaded.type_bilan is None
    assert reloaded.note == "Retard modéré, bonne coopération."


def test_reunion_participants_et_patients_concernes():
    patient = patient_service.create("E", "E")
    intervenant = intervenant_service.create_intervenant("Mme Petit", "Psychomotricienne")
    type_synthese = type_reunion_service.create("Synthèse")
    type_point_equipe = type_reunion_service.create("Point d'équipe")

    reunion = reunion_service.create(
        date=date(2024, 6, 1), type_reunion_id=type_synthese.id, note="RAS",
        intervenant_ids=[intervenant.id], patient_ids=[patient.id],
    )
    assert reunion.participants[0].id == intervenant.id
    assert reunion.patients[0].id == patient.id
    assert reunion.type_reunion.libelle == "Synthèse"

    all_reunions = reunion_service.list_all()
    assert len(all_reunions) == 1

    reunion_service.update(
        reunion.id, date=date(2024, 6, 2), type_reunion_id=type_point_equipe.id, note=None,
        intervenant_ids=[], patient_ids=[patient.id],
    )
    updated = reunion_service.get(reunion.id)
    assert updated.type_reunion.libelle == "Point d'équipe"
    assert updated.participants == []
    assert len(updated.patients) == 1


def test_type_reunion_crud_et_suppression_conserve_reunion():
    patient = patient_service.create("G", "G")
    type_reunion = type_reunion_service.create("Réunion de rentrée")
    assert len(type_reunion_service.list_all()) == 1

    reunion = reunion_service.create(
        date=date(2024, 9, 1), type_reunion_id=type_reunion.id, note=None,
        intervenant_ids=[], patient_ids=[patient.id],
    )

    type_reunion_service.update(type_reunion.id, "Réunion de rentrée (renommée)")
    reloaded = reunion_service.get(reunion.id)
    assert reloaded.type_reunion.libelle == "Réunion de rentrée (renommée)"

    type_reunion_service.delete(type_reunion.id)
    reloaded = reunion_service.get(reunion.id)
    assert reloaded.type_reunion is None  # la réunion existe toujours, juste sans type
