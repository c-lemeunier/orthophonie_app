"""Modèles SQLAlchemy de l'application."""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StatutObjectif(str, enum.Enum):
    A_TRAVAILLER = "a_travailler"
    EN_COURS = "en_cours"
    ATTEINT = "atteint"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    date_naissance: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_debut: Mapped[date | None] = mapped_column(Date, nullable=True)
    diagnostic: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequence: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email_parent1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_parent2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    intervenants_links: Mapped[list["PatientIntervenant"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    grands_objectifs: Mapped[list["GrandObjectif"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan",
        order_by="GrandObjectif.ordre",
    )
    coordinations: Mapped[list["Coordination"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    bilans: Mapped[list["Bilan"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    reunions_links: Mapped[list["ReunionPatient"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )

    @property
    def nom_complet(self) -> str:
        return f"{self.nom} {self.prenom}"


class Intervenant(Base):
    """Annuaire global partagé (équipe pluri + participants réunions)."""

    __tablename__ = "intervenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    fonction: Mapped[str] = mapped_column(String(150), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    patients_links: Mapped[list["PatientIntervenant"]] = relationship(
        back_populates="intervenant"
    )
    reunions_links: Mapped[list["ReunionIntervenant"]] = relationship(
        back_populates="intervenant"
    )

    @property
    def libelle(self) -> str:
        return f"{self.nom} ({self.fonction})"


class PatientIntervenant(Base):
    """Lien équipe pluridisciplinaire d'un patient vers l'annuaire."""

    __tablename__ = "patient_intervenants"
    __table_args__ = (UniqueConstraint("patient_id", "intervenant_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    intervenant_id: Mapped[int] = mapped_column(
        ForeignKey("intervenants.id", ondelete="RESTRICT"), nullable=False
    )
    role_specifique: Mapped[str | None] = mapped_column(String(150), nullable=True)
    date_ajout: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="intervenants_links")
    intervenant: Mapped["Intervenant"] = relationship(back_populates="patients_links")


class GrandObjectif(Base):
    __tablename__ = "grands_objectifs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    statut: Mapped[StatutObjectif] = mapped_column(
        Enum(StatutObjectif, native_enum=False),
        default=StatutObjectif.A_TRAVAILLER,
        nullable=False,
    )
    ordre: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="grands_objectifs")
    petits_objectifs: Mapped[list["PetitObjectif"]] = relationship(
        back_populates="grand_objectif", cascade="all, delete-orphan",
        order_by="PetitObjectif.ordre",
    )


class PetitObjectif(Base):
    __tablename__ = "petits_objectifs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grand_objectif_id: Mapped[int] = mapped_column(
        ForeignKey("grands_objectifs.id", ondelete="CASCADE"), nullable=False
    )
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    statut: Mapped[StatutObjectif] = mapped_column(
        Enum(StatutObjectif, native_enum=False),
        default=StatutObjectif.A_TRAVAILLER,
        nullable=False,
    )
    ordre: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    grand_objectif: Mapped["GrandObjectif"] = relationship(
        back_populates="petits_objectifs"
    )


class _DatedNoteMixin:
    """Colonnes communes à coordinations/bilans/notes (date + note)."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Coordination(_DatedNoteMixin, Base):
    __tablename__ = "coordinations"

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    patient: Mapped["Patient"] = relationship(back_populates="coordinations")


class TypeBilan(Base):
    """Annuaire des types de bilan, géré par l'utilisateur (ajout, renommage,
    suppression) — propre aux bilans, pas partagé ailleurs."""

    __tablename__ = "type_bilans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bilans: Mapped[list["Bilan"]] = relationship(back_populates="type_bilan")


class Bilan(_DatedNoteMixin, Base):
    __tablename__ = "bilans"

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    type_bilan_id: Mapped[int | None] = mapped_column(
        ForeignKey("type_bilans.id", ondelete="SET NULL"), nullable=True
    )
    # Chemin vers un document joint (référence, pas une copie) — le nom de
    # colonne est resté `document` pour éviter une migration, mais il
    # contient un chemin de fichier, pas du texte libre (voir bilan_service).
    document: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="bilans")
    type_bilan: Mapped["TypeBilan | None"] = relationship(back_populates="bilans")


class Note(_DatedNoteMixin, Base):
    __tablename__ = "notes"

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    patient: Mapped["Patient"] = relationship(back_populates="notes")


class TypeReunion(Base):
    """Annuaire des types de réunion, géré par l'utilisateur (recherche,
    ajout, modification, suppression) — propre aux réunions."""

    __tablename__ = "type_reunions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    reunions: Mapped[list["Reunion"]] = relationship(back_populates="type_reunion")


class Reunion(Base):
    __tablename__ = "reunions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    # Ancienne colonne texte libre, conservée (non utilisée par l'ORM) pour la
    # migration des données existantes vers `type_reunion_id` — voir
    # db/database.py::_migrate_reunion_types.
    type_reunion_id: Mapped[int | None] = mapped_column(
        ForeignKey("type_reunions.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    type_reunion: Mapped["TypeReunion | None"] = relationship(back_populates="reunions")
    intervenants_links: Mapped[list["ReunionIntervenant"]] = relationship(
        back_populates="reunion", cascade="all, delete-orphan"
    )
    patients_links: Mapped[list["ReunionPatient"]] = relationship(
        back_populates="reunion", cascade="all, delete-orphan"
    )


class ReunionIntervenant(Base):
    __tablename__ = "reunion_intervenants"
    __table_args__ = (UniqueConstraint("reunion_id", "intervenant_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reunion_id: Mapped[int] = mapped_column(
        ForeignKey("reunions.id", ondelete="CASCADE"), nullable=False
    )
    intervenant_id: Mapped[int] = mapped_column(
        ForeignKey("intervenants.id", ondelete="RESTRICT"), nullable=False
    )

    reunion: Mapped["Reunion"] = relationship(back_populates="intervenants_links")
    intervenant: Mapped["Intervenant"] = relationship(back_populates="reunions_links")


class ReunionPatient(Base):
    __tablename__ = "reunion_patients"
    __table_args__ = (UniqueConstraint("reunion_id", "patient_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reunion_id: Mapped[int] = mapped_column(
        ForeignKey("reunions.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )

    reunion: Mapped["Reunion"] = relationship(back_populates="patients_links")
    patient: Mapped["Patient"] = relationship(back_populates="reunions_links")
