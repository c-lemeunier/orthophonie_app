"""Vérifie que l'auto-migration ajoute les colonnes manquantes sans perte de
données sur une base déjà existante (cas réel : ajout de classe/e-mails
parents sur une base créée avant ces champs)."""
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, text

from db.database import _auto_migrate


def test_auto_migrate_adds_missing_columns_without_losing_data():
    engine = create_engine("sqlite:///:memory:")

    old_metadata = MetaData()
    Table(
        "patients", old_metadata,
        Column("id", Integer, primary_key=True),
        Column("nom", String(100), nullable=False),
        Column("prenom", String(100), nullable=False),
    )
    old_metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO patients (nom, prenom) VALUES ('Dupont', 'Alice')"))

    _auto_migrate(engine)

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT nom, prenom, classe, email_parent1, email_parent2 FROM patients")
        ).one()
        assert row.nom == "Dupont"
        assert row.prenom == "Alice"
        assert row.classe is None
        assert row.email_parent1 is None
        assert row.email_parent2 is None
