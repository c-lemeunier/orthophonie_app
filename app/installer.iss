; Installeur Windows (Inno Setup) pour OrthophonieApp.
; À compiler après `pyinstaller build.spec` (le dossier dist\OrthophonieApp
; doit exister), avec ISCC installer.iss (depuis le dossier app\).

#define MyAppName "OrthophonieApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Cabinet d'orthophonie"
#define MyAppExeName "OrthophonieApp.exe"

[Setup]
AppId={{8F2B6B0E-6C1A-4B7E-9C1E-4E7B8B5D9A21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
OutputDir=installer_output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

; Les données patients vivent dans %APPDATA%\OrthophonieApp\, créées par
; l'application elle-même au premier lancement — jamais dans {app}
; (non writable pour un utilisateur standard sans droits admin).

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent

; Ne supprime jamais les données patients à la désinstallation : le dossier
; %APPDATA%\OrthophonieApp\ (base chiffrée + auth.json) n'est volontairement
; pas listé ici, pour préserver le dossier patient en cas de réinstallation.
