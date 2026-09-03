"""Primitives cryptographiques pures pour l'écran de verrouillage.

Schéma DEK/KEK :
- une DEK (Data Encryption Key) aléatoire de 256 bits est la vraie clé
  SQLCipher de la base ;
- elle est enveloppée (chiffrée) une fois avec une clé dérivée du mot de
  passe, et une seconde fois avec une clé dérivée d'un code de récupération ;
- changer de mot de passe ne nécessite donc pas de re-chiffrer toute la base
  (juste ré-envelopper la DEK).
"""
from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret_raw
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

_password_hasher = PasswordHasher()

# Paramètres Argon2id pour la dérivation de clé (KDF), distincts du hachage
# de vérification (qui utilise les paramètres par défaut d'argon2-cffi).
_KDF_TIME_COST = 3
_KDF_MEMORY_COST_KIB = 64 * 1024
_KDF_PARALLELISM = 4
_KDF_HASH_LEN = 32
_SALT_LEN = 16

RECOVERY_CODE_GROUPS = 6
RECOVERY_CODE_GROUP_LEN = 4


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_recovery_code() -> str:
    """Code lisible du type XXXX-XXXX-XXXX-XXXX-XXXX-XXXX (base32, sans 0/O/1/I)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    groups = [
        "".join(secrets.choice(alphabet) for _ in range(RECOVERY_CODE_GROUP_LEN))
        for _ in range(RECOVERY_CODE_GROUPS)
    ]
    return "-".join(groups)


def normalize_recovery_code(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def _derive_kek(secret: str, salt: bytes) -> bytes:
    raw = hash_secret_raw(
        secret=secret.encode("utf-8"),
        salt=salt,
        time_cost=_KDF_TIME_COST,
        memory_cost=_KDF_MEMORY_COST_KIB,
        parallelism=_KDF_PARALLELISM,
        hash_len=_KDF_HASH_LEN,
        type=Type.ID,
    )
    return base64.urlsafe_b64encode(raw)


def generate_dek() -> bytes:
    return os.urandom(32)


def dek_to_hex(dek: bytes) -> str:
    return dek.hex()


@dataclass
class WrappedSecret:
    salt_b64: str
    token: str


def wrap_dek(dek: bytes, secret: str) -> WrappedSecret:
    salt = os.urandom(_SALT_LEN)
    kek = _derive_kek(secret, salt)
    token = Fernet(kek).encrypt(dek).decode("utf-8")
    return WrappedSecret(salt_b64=base64.b64encode(salt).decode("utf-8"), token=token)


def unwrap_dek(wrapped: WrappedSecret, secret: str) -> bytes | None:
    salt = base64.b64decode(wrapped.salt_b64)
    kek = _derive_kek(secret, salt)
    try:
        return Fernet(kek).decrypt(wrapped.token.encode("utf-8"))
    except InvalidToken:
        return None
