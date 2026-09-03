# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — build en mode onedir (démarrage rapide, moins de faux
positifs antivirus qu'en --onefile). À lancer depuis le dossier app/ :
    pyinstaller build.spec
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = [("resources", "resources")]
binaries = []
hiddenimports = [
    "sqlcipher3.dbapi2",
    "argon2.low_level",
    "sqlalchemy.dialects.sqlite",
]

for pkg in ("sqlcipher3", "argon2"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OrthophonieApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="resources/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OrthophonieApp",
)
