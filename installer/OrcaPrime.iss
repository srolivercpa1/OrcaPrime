#define MyAppName "OrçaPrime"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "OLIVERTECH SOLUÇÕES"
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
SetupIconFile=..\assets\orcaprime-premium-r2.ico
UninstallDisplayIcon={app}\assets\orcaprime-premium-r2.ico
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
[Files]
Source: "..\dist\OrcaPrime\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\orcaprime-premium-r2.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
[Icons]
Name: "{group}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"; IconFilename: "{app}\assets\orcaprime-premium-r2.ico"; AppUserModelID: "OliverTech.OrcaPrime.Premium"
Name: "{autodesktop}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"; IconFilename: "{app}\assets\orcaprime-premium-r2.ico"; AppUserModelID: "OliverTech.OrcaPrime.Premium"; Tasks: desktopicon
[Run]
Filename: "{app}\OrcaPrime.exe"; Description: "Abrir OrçaPrime"; Flags: nowait postinstall skipifsilent
