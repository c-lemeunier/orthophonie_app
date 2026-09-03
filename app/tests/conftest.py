import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import database


@pytest.fixture(autouse=True)
def fresh_db():
    """Base SQLite en mémoire, non chiffrée, réinitialisée à chaque test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.reset_engine_for_tests(engine)
    yield
    engine.dispose()
