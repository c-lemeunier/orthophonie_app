"""Résolution robuste du chemin d'un document joint (sans Qt, testable).

On ne stocke qu'une référence vers le fichier d'origine. Ce chemin absolu peut
cesser d'être valide alors que le fichier n'a pas bougé du point de vue de
l'utilisateur, typiquement :
- OneDrive « Sauvegarde des dossiers PC » a redirigé le Bureau / les Documents
  (C:\\Users\\x\\Desktop\\... -> C:\\Users\\x\\OneDrive\\Bureau\\...) alors que
  l'Explorateur affiche toujours « Bureau » ;
- autre PC / autre session / nom d'utilisateur changé (C:\\Users\\<ancien>\\...).

`resolve()` essaie quelques variantes ciblées (jamais de recherche récursive :
appelée à chaque affichage de carte, elle doit rester instantanée).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

# Préfixe « profil utilisateur » d'un chemin Windows ou Unix, quel que soit
# l'OS courant : C:\Users\<nom>\reste, /Users/<nom>/reste, /home/<nom>/reste.
_PROFILE_RE = re.compile(r"^(?:[A-Za-z]:)?[\\/]+(?:Users|home)[\\/]+[^\\/]+[\\/]+(?P<rest>.+)$", re.IGNORECASE)

# Dossiers connus dont le nom varie selon la langue / la redirection OneDrive.
_KNOWN_FOLDER_GROUPS = (
    ("Desktop", "Bureau"),
    ("Documents", "Mes documents"),
)

_ONEDRIVE_ENV_VARS = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")


def normalize(path: str | None) -> str | None:
    """Nettoie un chemin saisi / collé / déposé : espaces, guillemets (« Copier
    en tant que chemin d'accès » de Windows), préfixe file://, séparateurs."""
    if path is None:
        return None
    cleaned = path.strip().strip('"').strip("'").strip()
    if not cleaned:
        return None
    if cleaned.lower().startswith("file:"):
        cleaned = unquote(urlparse(cleaned).path)
        if re.match(r"^/[A-Za-z]:", cleaned):  # file:///C:/x -> /C:/x -> C:/x
            cleaned = cleaned[1:]
    return os.path.normpath(cleaned)


def _split_parts(rest: str) -> list[str]:
    return [p for p in re.split(r"[\\/]+", rest) if p]


def _relative_to_profile(path: str) -> list[str] | None:
    """Partie du chemin située sous le dossier du profil utilisateur (le profil
    courant ou n'importe quel C:\\Users\\<nom>), ou None."""
    try:
        return list(Path(path).relative_to(Path.home()).parts) or None
    except ValueError:
        pass
    match = _PROFILE_RE.match(path)
    if match:
        return _split_parts(match.group("rest")) or None
    return None


def _onedrive_roots(home: Path) -> list[Path]:
    roots: list[Path] = []
    for var in _ONEDRIVE_ENV_VARS:
        value = os.environ.get(var)
        if value:
            roots.append(Path(value))
    try:
        roots.extend(p for p in home.glob("OneDrive*") if p.is_dir())
    except OSError:
        pass
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def _first_segment_variants(segment: str) -> list[str]:
    for group in _KNOWN_FOLDER_GROUPS:
        if segment.lower() in (name.lower() for name in group):
            return [segment] + [name for name in group if name.lower() != segment.lower()]
    return [segment]


def _candidates(parts: list[str]) -> list[Path]:
    home = Path.home()
    # Si le chemin stocké passait déjà par OneDrive, essayer aussi sans.
    rests = [parts]
    if parts[0].lower().startswith("onedrive") and len(parts) > 1:
        rests.append(parts[1:])

    roots = [home] + _onedrive_roots(home)
    candidates: list[Path] = []
    for rest in rests:
        for root in roots:
            for first in _first_segment_variants(rest[0]):
                candidate = root.joinpath(first, *rest[1:])
                if candidate not in candidates:
                    candidates.append(candidate)
    return candidates


def resolve(stored: str | None) -> Path | None:
    """Chemin existant correspondant à `stored`, ou None s'il est introuvable."""
    normalized = normalize(stored)
    if normalized is None:
        return None
    direct = Path(normalized)
    if direct.exists():
        return direct

    parts = _relative_to_profile(normalized)
    if not parts:
        return None
    for candidate in _candidates(parts):
        if candidate.exists():
            return candidate
    return None


def closest_existing_dir(stored: str | None) -> str:
    """Dossier existant le plus proche du chemin stocké (pour ouvrir le
    sélecteur de fichier au bon endroit), sinon chaîne vide."""
    normalized = normalize(stored)
    if not normalized:
        return ""
    current = Path(normalized).parent
    while True:
        if current.is_dir():
            return str(current)
        if current.parent == current:
            return ""
        current = current.parent
