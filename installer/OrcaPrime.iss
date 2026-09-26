#define MyAppName "OrçaPrime"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "Sketch Inc"
[Setup]
AppId={{0478A6B2-BC65-4C86-A371-4FC7EC577067}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Copyright (C) 2026 Mateus Oliveira
DefaultDirName={localappdata}\Programs\OrcaPrime
DefaultGroupName=OrçaPrime
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=OrcaPrime-Setup
SetupIconFile=..\assets\orcaprime-commercial.ico
UninstallDisplayIcon={app}\assets\orcaprime-commercial.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
[Dirs]
Name: "{app}\backup"; Flags: uninsneveruninstall
[Files]
Source: "register-backup-task.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\OrcaPrime\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\orcaprime-commercial.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
[Icons]
Name: "{group}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"; IconFilename: "{app}\assets\orcaprime-commercial.ico"; AppUserModelID: "OliverTech.OrcaPrime.Premium"
Name: "{autodesktop}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"; IconFilename: "{app}\assets\orcaprime-commercial.ico"; AppUserModelID: "OliverTech.OrcaPrime.Premium"; Tasks: desktopicon
[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\register-backup-task.ps1"" -Action unregister"; Flags: runhidden waituntilterminated
[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\register-backup-task.ps1"" -Action register -ExePath ""{app}\OrcaPrime.exe"""; Flags: runhidden waituntilterminated
Filename: "{app}\OrcaPrime.exe"; Description: "Abrir OrçaPrime"; Flags: nowait postinstall skipifsilent
