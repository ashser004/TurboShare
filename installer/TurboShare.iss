#define AppName "TurboShare"
#define AppExeName "TurboShare.exe"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "Ashmith Babu P S"
#define AppURL "https://github.com/ashser004"

[Setup]
AppId=TurboShareUI
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={localappdata}\Programs\TurboShare
DefaultGroupName=TurboShare
DisableProgramGroupPage=yes
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#AppExeName}
OutputDir=..\build\installer
OutputBaseFilename=TurboShare_Setup
SetupIconFile=..\build\installer\TurboShare.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64
VersionInfoVersion={#AppVersion}.0
VersionInfoTextVersion={#AppVersion}
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\TurboShare\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TurboShare"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall TurboShare"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TurboShare"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""TurboShare"" dir=in action=allow program=""{app}\{#AppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "{app}\{#AppExeName}"; Description: "Launch TurboShare"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""TurboShare"" program=""{app}\{#AppExeName}"""; Flags: runhidden
