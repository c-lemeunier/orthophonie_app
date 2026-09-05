"""DTOs partagés entre services — l'UI ne manipule jamais les objets ORM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from db.model import StatutObjectif


def compute_age(date_naissance: date, today: date | None = None) -> int:
    today = today or date.today()
    annees = today.year - date_naissance.year
    if (today.month, today.day) < (date_naissance.month, date_naissance.day):
        annees -= 1
    return annees


@dataclass
class PatientDTO:
    id: int
    nom: str
    prenom: str
    date_naissance: date | None
    date_debut: date | None
    diagnostic: str | None
    frequence: str | None
    classe: str | None = None
    email_parent1: str | None = None
    email_parent2: str | None = None

    @property
    def nom_complet(self) -> str:
        return f"{self.nom} {self.prenom}"

    @property
    def age_ans(self) -> int | None:
        if self.date_naissance is None:
            return None
        return compute_age(self.date_naissance)


@dataclass
class IntervenantDTO:
    id: int
    nom: str
    fonction: str
    actif: bool = True

    @property
    def libelle(self) -> str:
        return f"{self.nom} ({self.fonction})"


@dataclass
class PatientIntervenantDTO:
    lien_id: int
    intervenant: IntervenantDTO
    role_specifique: str | None


@dataclass
class PetitObjectifDTO:
    id: int
    grand_objectif_id: int
    libelle: str
    statut: StatutObjectif
    ordre: int


@dataclass
class GrandObjectifDTO:
    id: int
    patient_id: int
    libelle: str
    statut: StatutObjectif
    ordre: int
    petits_objectifs: list[PetitObjectifDTO] = field(default_factory=list)


@dataclass
class JournalEntryDTO:
    id: int
    patient_id: int
    date: date
    note: str


@dataclass
class TypeBilanDTO:
    id: int
    libelle: str


@dataclass
class BilanDTO:
    id: int
    patient_id: int
    date: date
    type_bilan: TypeBilanDTO | None
    document: str | None
    note: str


@dataclass
class ReunionDTO:
    id: int
    date: date
    type_reunion: str
    note: str | None
    participants: list[IntervenantDTO] = field(default_factory=list)
    patients: list[PatientDTO] = field(default_factory=list)
