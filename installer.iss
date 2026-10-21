#define MyAppName "ffReal"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "baturdenada"
#define MyAppExeName "ffReal.exe"

[Setup]
AppId={{9C6442A8-96C4-4D95-97BA-4090D15AB610}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=ffReal-Setup
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "ffReal.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\ffReal"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Comment: "FocusForReal task timer"
Name: "{group}\ffReal"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ffReal"; Flags: nowait postinstall skipifsilent
