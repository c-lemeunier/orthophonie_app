# resources/

- `icon.ico` — icône Windows (7 résolutions, 16 à 256px), utilisée par PyInstaller (`build.spec`) et Inno Setup (`installer.iss`).
- `app_icon.png` — même visuel en PNG (bulle de dialogue terracotta), utilisable dans l'UI si besoin.

Une icône par défaut (bulle de dialogue terracotta, cohérente avec le thème de l'app) est déjà fournie. Remplacez ces deux fichiers par vos propres visuels quand vous le souhaitez — gardez juste les mêmes noms et gardez `icon.ico` multi-résolutions (16/24/32/48/64/128/256) pour un rendu net à toutes les tailles (barre des tâches, raccourci bureau, etc.).
