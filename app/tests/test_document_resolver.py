"""Reproduction du « (fichier introuvable) » sur les documents de bilans et
vérification de la résolution robuste des chemins."""
import os
import shutil
from pathlib import Path

import pytest

from services import document_resolver


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    home = tmp_path / "Users" / "myuser"
    home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        monkeypatch.delenv(var, raising=False)
    return home


def _make_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4")
    return path


REST = ("PRO", "Lib", "Dos pat", "name name", "file name.pdf")


def test_path_with_spaces_exists(fake_home):
    doc = _make_file(fake_home.joinpath("Desktop", *REST))
    assert document_resolver.resolve(str(doc)) == doc


def test_reproduce_onedrive_redirect(fake_home, monkeypatch):
    stored = str(fake_home.joinpath("Desktop", *REST))
    _make_file(Path(stored))

    # OneDrive « Sauvegarde des dossiers PC » déplace le Bureau.
    onedrive = fake_home / "OneDrive"
    target = onedrive.joinpath("Bureau", *REST)
    target.parent.mkdir(parents=True)
    shutil.move(stored, target)
    monkeypatch.setenv("OneDrive", str(onedrive))

    # Comportement d'origine : le chemin stocké ne résout plus -> le bug.
    assert not Path(stored).exists()
    # Nouveau comportement : retrouvé.
    assert document_resolver.resolve(stored) == target


def test_onedrive_back_to_local(fake_home):
    stored = str(fake_home.joinpath("OneDrive", "Documents", *REST))
    target = _make_file(fake_home.joinpath("Documents", *REST))
    assert document_resolver.resolve(stored) == target


def test_reproduce_username_change(fake_home):
    target = _make_file(fake_home.joinpath("Desktop", *REST))
    stored = "C:\\Users\\olduser\\Desktop\\" + "\\".join(REST)
    assert document_resolver.resolve(stored) == target


def test_unresolvable_returns_none(fake_home):
    assert document_resolver.resolve(str(fake_home / "Desktop" / "absent.pdf")) is None
    assert document_resolver.resolve("D:\\Partage\\absent.pdf") is None
    assert document_resolver.resolve(None) is None
    assert document_resolver.resolve("   ") is None


def test_normalize():
    expected = os.path.normpath("/a/b c/d.pdf")
    assert document_resolver.normalize('  "/a/b c//d.pdf"  ') == expected
    assert document_resolver.normalize("file:///a/b%20c/d.pdf") == expected
    assert document_resolver.normalize("file:///C:/x/y.pdf") == os.path.normpath("C:/x/y.pdf")
    assert document_resolver.normalize("") is None


def test_closest_existing_dir(fake_home):
    (fake_home / "Desktop").mkdir()
    stored = str(fake_home.joinpath("Desktop", *REST))
    assert document_resolver.closest_existing_dir(stored) == str(fake_home / "Desktop")
