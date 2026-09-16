# Orthophonie App

Application desktop locale (Windows) pour la gestion de dossiers patients
orthophoniques : infos personnelles, équipe pluridisciplinaire, objectifs
orthophoniques, coordinations, bilans, notes, et réunions d'équipe/synthèses.

Mono-poste, mono-utilisateur. Les données sont stockées dans une base SQLite
**chiffrée** (SQLCipher) sur le poste de l'utilisateur, protégée par un mot
de passe local.

## Fonctionnalités

### Patients

- Menu déroulant en haut de la fenêtre principale, avec recherche en direct
  (on tape le début du nom et la liste se filtre toute seule).
- Au démarrage (ou en revenant sur l'étiquette "Cliquez sur un patient"),
  aucun dossier n'est affiché : il faut choisir un patient explicitement.
- Boutons "Ajouter patient" et "Supprimer patient" (avec confirmation avant
  suppression, qui efface aussi toutes les données liées au patient).
- Chaque patient a 6 onglets :

**Infos personnelles** : nom, prénom, date de naissance (format jour/mois/
année), âge calculé automatiquement à partir de la date de naissance, date de
début de prise en charge, classe, diagnostic, fréquence des séances, e-mail
parent 1 et e-mail parent 2.

**Équipe pluri** : liste des intervenants (fonction et nom) rattachés au
patient. Les intervenants viennent d'un annuaire global partagé entre tous
les patients et les réunions (pas de saisie en double), avec possibilité de
créer un nouvel intervenant directement depuis cet onglet.

**Objectifs orthophoniques** : arbre à deux niveaux (grands objectifs
contenant des petits objectifs), chacun avec son propre statut (à
travailler, en cours, atteint) affiché par une pastille de couleur.

**Coordinations** et **Notes** : liste d'entrées datées, affichées en entier
sur des cartes avec retour à la ligne automatique (pas de troncature) et
défilement vertical.

**Derniers bilans** : comme les coordinations et les notes, avec en plus :
  - un type de bilan, choisi dans un annuaire géré par l'utilisateur
    (recherche, ajout, renommage, suppression depuis le formulaire) ;
  - un document joint : on glisse un fichier sur la zone de dépôt (ou on le
    choisit via "Parcourir"), il apparaît ensuite en lien cliquable qui
    l'ouvre avec l'application par défaut du système (Sumatra PDF, Word,
    etc.). Seul le chemin du fichier est mémorisé, pas de copie ni de
    chiffrement du contenu : si le fichier est déplacé, le lien ne s'ouvre
    plus ;
  - la note est facultative sur un bilan ;
  - un encart "prochain bilan" calculé automatiquement (dernier bilan plus un
    an).

### Réunions équipe et synthèses

Fenêtre séparée, accessible depuis la fenêtre principale, listant toutes les
réunions dans un tableau triable (clic sur un en-tête de colonne) et
filtrable par une recherche libre portant sur toutes les colonnes.

Chaque réunion comprend une date (colonne étroite, juste la place
nécessaire), un type (annuaire géré par l'utilisateur, recherche, ajout,
renommage, suppression), des participants et des patients concernés (chacun
affiché en bloc, un par ligne), et une note. Seule la colonne Note s'étire
pour occuper l'espace disponible quand on agrandit la fenêtre.

Le formulaire d'ajout ou de modification permet de créer un nouvel
intervenant directement depuis la liste des participants, sans quitter le
formulaire.

### Thème et couleurs

Fond terracotta pour toute l'application, panneaux clairs (crème) pour le
contenu afin de garder une bonne lisibilité. Chaque onglet patient a sa
propre couleur d'accent. Les boutons suivent un code couleur constant dans
toute l'application : vert pour ajouter, bleu pour modifier ou enregistrer,
rouge pour supprimer. La fenêtre de mot de passe reste sur un fond clair,
distincte du reste de l'application.

## Sécurité et authentification

Écran de verrouillage au premier lancement (création du mot de passe) puis à
chaque démarrage (saisie du mot de passe). La base de données est chiffrée
(SQLCipher, AES-256) avec une clé générée aléatoirement, elle-même protégée
par le mot de passe (schéma DEK/KEK) : changer de mot de passe ne nécessite
pas de rechiffrer toute la base.

Un code de récupération est affiché une seule fois lors de la création du
mot de passe. À noter et conserver en lieu sûr, hors de cet ordinateur : sans
le mot de passe ni le code de récupération, les données sont définitivement
irrécupérables, il n'existe aucune porte dérobée.

Après plusieurs tentatives de connexion échouées, l'application se ferme
(délai croissant entre les tentatives).

## Stack technique

- **UI** : [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python)
- **ORM et base de données** : SQLAlchemy 2.x et
  [sqlcipher3](https://pypi.org/project/sqlcipher3/) (SQLite chiffré,
  wheels précompilées Linux, Windows et macOS)
- **Authentification locale** : Argon2id (`argon2-cffi`) et enveloppe de clé
  Fernet (`cryptography`)
- **Packaging** : PyInstaller (mode onedir) et Inno Setup, buildés
  automatiquement via GitHub Actions (`windows-latest`)
- **Dépendances** : déclarées dans `pyproject.toml` (PEP 621), pas de
  `requirements.txt`

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

## Build de l'exécutable Windows

PyInstaller ne peut pas cross-compiler : le `.exe` doit être produit sur
Windows. Deux options :

1. **CI (recommandé)** : `.github/workflows/build-windows.yml` build
   automatiquement sur `windows-latest` à chaque tag `prod-vX.Y.Z` poussé sur
   le dépôt (ou via déclenchement manuel), et publie l'exécutable et
   l'installeur en artifacts et en release GitHub. Le numéro de version de
   l'installeur est extrait directement du nom du tag.
2. **Local sur Windows** :
   ```powershell
   pip install -e ".[dev]"
   pyinstaller build.spec
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

Une icône par défaut est fournie dans `resources/`. Remplacez-la par votre
propre visuel quand vous voulez (voir `resources/README.md`).

## Structure

```
app/
  main.py              point d'entrée
  auth/                écran de verrouillage, chiffrement, gestion auth.json
  db/                  modèles SQLAlchemy, moteur SQLCipher, seed et migrations
  services/            couche métier (CRUD), seule couche qui parle à SQLAlchemy
  ui/                  fenêtres et onglets Qt (n'appellent que les services)
  tests/               tests pytest
```
