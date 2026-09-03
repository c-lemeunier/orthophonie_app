"""Lecture/écriture de auth.json et orchestration login/setup/changement de mdp."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from auth import crypto
from auth.crypto import WrappedSecret

APP_DIR_NAME = "OrthophonieApp"
AUTH_FILE_NAME = "auth.json"
DB_FILE_NAME = "data.db"

MAX_LOGIN_ATTEMPTS = 5


def get_app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
    # Fallback dev (WSL/Linux/macOS)
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def get_auth_path() -> Path:
    return get_app_data_dir() / AUTH_FILE_NAME


def get_db_path() -> Path:
    return get_app_data_dir() / DB_FILE_NAME


@dataclass
class AuthRecord:
    password_hash: str
    wrapped_dek_password: WrappedSecret
    wrapped_dek_recovery: WrappedSecret

    def to_json(self) -> dict:
        return {
            "version": 1,
            "password_hash": self.password_hash,
            "wrapped_dek_password": asdict(self.wrapped_dek_password),
            "wrapped_dek_recovery": asdict(self.wrapped_dek_recovery),
        }

    @staticmethod
    def from_json(data: dict) -> "AuthRecord":
        return AuthRecord(
            password_hash=data["password_hash"],
            wrapped_dek_password=WrappedSecret(**data["wrapped_dek_password"]),
            wrapped_dek_recovery=WrappedSecret(**data["wrapped_dek_recovery"]),
        )


def is_first_launch() -> bool:
    return not get_auth_path().exists()


def load_auth_record() -> AuthRecord:
    with open(get_auth_path(), "r", encoding="utf-8") as f:
        return AuthRecord.from_json(json.load(f))


def _save_auth_record(record: AuthRecord) -> None:
    path = get_auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(record.to_json(), f, indent=2)
    tmp_path.replace(path)


def create_password(password: str) -> tuple[bytes, str]:
    """Premier lancement : crée la DEK, l'enveloppe avec le mdp et un code de
    récupération. Retourne (dek, recovery_code) — le code doit être affiché
    une seule fois à l'utilisateur puis jeté."""
    dek = crypto.generate_dek()
    recovery_code = crypto.generate_recovery_code()

    record = AuthRecord(
        password_hash=crypto.hash_password(password),
        wrapped_dek_password=crypto.wrap_dek(dek, password),
        wrapped_dek_recovery=crypto.wrap_dek(dek, crypto.normalize_recovery_code(recovery_code)),
    )
    _save_auth_record(record)
    return dek, recovery_code


def unlock_with_password(password: str) -> bytes | None:
    """Vérifie le mot de passe puis déverrouille la DEK. Retourne None si le
    mot de passe est incorrect."""
    record = load_auth_record()
    if not crypto.verify_password(password, record.password_hash):
        return None
    return crypto.unwrap_dek(record.wrapped_dek_password, password)


def unlock_with_recovery_code(recovery_code: str) -> bytes | None:
    record = load_auth_record()
    normalized = crypto.normalize_recovery_code(recovery_code)
    return crypto.unwrap_dek(record.wrapped_dek_recovery, normalized)


def change_password(dek: bytes, new_password: str) -> None:
    """Ré-enveloppe la DEK avec un nouveau mot de passe (pas de re-chiffrement
    de la base : la DEK ne change pas)."""
    record = load_auth_record()
    record.password_hash = crypto.hash_password(new_password)
    record.wrapped_dek_password = crypto.wrap_dek(dek, new_password)
    _save_auth_record(record)
