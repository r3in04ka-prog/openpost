[Setup]
AppId={{92DC757B-A0C8-4821-B24D-1AC1F574BD5E}
AppName=OpenPost
AppVersion=0.2.0
AppPublisher=OpenPost contributors
AppPublisherURL=https://github.com/r3in04ka-prog/openpost
DefaultDirName={localappdata}\Programs\OpenPost
DefaultGroupName=OpenPost
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=OpenPost-Setup-0.2.0-windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\OpenPost.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\OpenPost\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OpenPost"; Filename: "{app}\OpenPost.exe"
Name: "{autodesktop}\OpenPost"; Filename: "{app}\OpenPost.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OpenPost.exe"; Description: "Launch OpenPost"; Flags: nowait postinstall skipifsilent
