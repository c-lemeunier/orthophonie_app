# resources/

Placez ici avant le build :

- `icon.ico` — icône Windows (multi-résolutions 16/32/48/256) utilisée par PyInstaller (`build.spec`) et Inno Setup (`installer.iss`).
- `app_icon.png` — variante PNG, utilisable dans l'UI (à propos, etc.) si besoin.

Ces fichiers ne sont pas générables automatiquement : fournissez vos propres visuels (ou générez un `.ico` à partir d'un PNG via un outil comme https://icoconvert.com ou `Pillow`/`img2ico`). Sans `icon.ico`, `pyinstaller build.spec` échoue.
