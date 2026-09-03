# Orthophonie App

Application desktop locale (Windows) pour la gestion de dossiers patients
orthophoniques : infos personnelles, équipe pluridisciplinaire, objectifs
orthophoniques, coordinations, bilans, notes, et réunions d'équipe/synthèses.

Mono-poste, mono-utilisateur. Les données sont stockées dans une base SQLite
**chiffrée** (SQLCipher) sur le poste de l'utilisateur, protégée par un mot
de passe local.

## Stack technique

- **UI** : [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python)
- **ORM / base de données** : SQLAlchemy 2.x + [sqlcipher3](https://pypi.org/project/sqlcipher3/) (SQLite chiffré AES-256, wheels précompilées Linux/Windows/macOS)
- **Authentification locale** : Argon2id (`argon2-cffi`) + enveloppe de clé Fernet (`cryptography`)
- **Packaging** : PyInstaller (mode onedir) + Inno Setup, buildés automatiquement via GitHub Actions (`windows-latest`)
- **Dépendances** : déclarées dans `pyproject.toml` (PEP 621) — pas de `requirements.txt`

## Développement

Avec conda (recommandé) :

```bash
conda create -n orthophonie-app python=3.11
conda activate orthophonie-app
pip install -e ".[dev]"
python main.py
```

Ou avec un venv standard :

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -e ".[dev]"
python main.py
```

Sous WSL, un serveur d'affichage est requis pour PySide6 (WSLg sur Windows 11,
ou un serveur X sous Windows 10).

En développement (hors Windows), les données sont stockées dans
`~/.orthophonieapp/` plutôt que `%APPDATA%\OrthophonieApp\`.

## Tests

```bash
pytest
```

Les tests utilisent une base SQLite en mémoire non chiffrée (rapide, pas de
dépendance à SQLCipher pour la logique métier).

## Sécurité & récupération de mot de passe

Le mot de passe protège l'accès à la base via une clé de chiffrement (DEK)
générée aléatoirement au premier lancement. **Un code de récupération est
affiché une seule fois** lors de la création du mot de passe : notez-le et
conservez-le en lieu sûr (hors de cet ordinateur). Sans le mot de passe *ni*
le code de récupération, les données de la base sont **définitivement
irrécupérables** — il n'existe aucune porte dérobée.

## Build de l'exécutable Windows

PyInstaller ne peut pas cross-compiler : le `.exe` doit être produit sur
Windows. Deux options :

1. **CI (recommandé)** : `.github/workflows/build-windows.yml` build
   automatiquement sur `windows-latest` à chaque tag `vX.Y.Z` (ou déclenchement
   manuel), et publie l'exécutable + l'installeur en artifacts/release.
2. **Local sur Windows** :
   ```powershell
   pip install -e ".[dev]"
   pyinstaller build.spec
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

Avant de builder, ajoutez `resources/icon.ico` (voir `resources/README.md`).

## Structure

```
app/
  main.py              point d'entrée
  auth/                écran de verrouillage, chiffrement, gestion auth.json
  db/                   modèles SQLAlchemy, moteur SQLCipher, seed
  services/             couche métier (CRUD) — seule couche qui parle à SQLAlchemy
  ui/                    fenêtres et onglets Qt (n'appellent que les services)
  tests/                 tests pytest
```
