#define MyAppName "OrçaPrime"
#define MyAppVersion "2.1.1"
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
SetupIconFile=..\assets\orcaprime.ico
UninstallDisplayIcon={app}\OrcaPrime.exe
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
[Icons]
Name: "{group}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"
Name: "{autodesktop}\OrçaPrime"; Filename: "{app}\OrcaPrime.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\OrcaPrime.exe"; Description: "Abrir OrçaPrime"; Flags: nowait postinstall skipifsilent
