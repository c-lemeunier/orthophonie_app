"""Initialisation du moteur SQLAlchemy sur une base SQLite chiffrée (SQLCipher).

Le moteur n'est créé qu'après authentification réussie (voir app/main.py) :
il n'existe aucun moteur/session global au niveau module.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from db.model import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_engine(db_path: Path, key_hex: str, *, echo: bool = False) -> Engine:
    """Crée le moteur SQLAlchemy pointant sur une base SQLCipher déverrouillée
    avec `key_hex` (clé DEK en hexadécimal), et crée le schéma s'il est absent.
    """
    global _engine, _SessionLocal

    import sqlcipher3.dbapi2 as sqlcipher

    db_path.parent.mkdir(parents=True, exist_ok=True)

    def _creator():
        return sqlcipher.connect(str(db_path))

    engine = create_engine_from_creator(_creator, echo=echo)

    @event.listens_for(engine, "connect")
    def _set_key(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        # PRAGMA key ne supporte pas les paramètres liés : la clé est un hex
        # généré côté serveur (crypto.py), jamais une entrée utilisateur brute.
        cursor.execute(f"PRAGMA key = \"x'{key_hex}'\"")
        cursor.execute("PRAGMA cipher_page_size = 4096")
        cursor.execute("PRAGMA kdf_iter = 256000")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    Base.metadata.create_all(engine)
    _auto_migrate(engine)
    _migrate_reunion_types(engine)

    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return engine


def _auto_migrate(engine: Engine) -> None:
    """Ajoute les colonnes manquantes (ALTER TABLE ... ADD COLUMN) sur les
    tables déjà existantes. Pas de framework de migration (Alembic) pour une
    appli mono-poste — suffisant tant qu'on ne fait qu'ajouter des colonnes
    nullable, ce qui couvre les évolutions de schéma jusqu'ici."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                col_type = column.type.compile(engine.dialect)
                conn.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}')
                )


def _migrate_reunion_types(engine: Engine) -> None:
    """Convertit les anciennes valeurs `reunions.type_reunion` (texte libre)
    en entrées de l'annuaire `type_reunions`, pour les bases créées avant
    l'introduction de cet annuaire géré. Idempotent : ne touche que les
    réunions dont `type_reunion_id` est encore NULL."""
    inspector = inspect(engine)
    if "reunions" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("reunions")}
    if "type_reunion" not in columns or "type_reunion_id" not in columns:
        return

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, type_reunion FROM reunions "
                "WHERE type_reunion_id IS NULL AND type_reunion IS NOT NULL AND type_reunion != ''"
            )
        ).all()
        if not rows:
            return

        cache: dict[str, int] = {}
        for row in rows:
            libelle = row.type_reunion.strip()
            if not libelle:
                continue
            if libelle not in cache:
                existing = conn.execute(
                    text("SELECT id FROM type_reunions WHERE libelle = :libelle"),
                    {"libelle": libelle},
                ).first()
                if existing:
                    cache[libelle] = existing.id
                else:
                    result = conn.execute(
                        text(
                            "INSERT INTO type_reunions (libelle, created_at) "
                            "VALUES (:libelle, CURRENT_TIMESTAMP)"
                        ),
                        {"libelle": libelle},
                    )
                    cache[libelle] = result.lastrowid
            conn.execute(
                text("UPDATE reunions SET type_reunion_id = :tid WHERE id = :rid"),
                {"tid": cache[libelle], "rid": row.id},
            )


def create_engine_from_creator(creator, *, echo: bool = False) -> Engine:
    from sqlalchemy import create_engine

    return create_engine("sqlite://", creator=creator, echo=echo)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Le moteur n'est pas initialisé : appeler init_engine() après login.")
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    """Fournit une session avec commit/rollback automatique."""
    if _SessionLocal is None:
        raise RuntimeError("Le moteur n'est pas initialisé : appeler init_engine() après login.")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests(engine: Engine) -> None:
    """Permet aux tests d'injecter un moteur en mémoire non chiffré."""
    global _engine, _SessionLocal
    Base.metadata.create_all(engine)
    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
