[Setup]
AppName=Gadget System Framework
AppVersion=1.0
DefaultDirName={autopf}\Gadget System Framework
DefaultGroupName=Gadget System Framework
OutputBaseFilename=GSF-Setup-1.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=dist\GSF_Distribution\gsf\assets\icon-install.ico
UninstallDisplayIcon={app}/gsf\assets\icon.ico

[Files]
Source: "dist\GSF_Distribution\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GSF Control Center"; Filename: "{app}\GSFControlCenter.exe"
Name: "{group}\Uninstall GSF"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\GSFService.exe"; Parameters: "install"; Flags: runhidden
Filename: "net"; Parameters: "start GSF-Service"; Flags: runhidden

[UninstallRun]
Filename: "net"; Parameters: "stop GSF-Service"; Flags: runhidden
Filename: "{app}\GSFService.exe"; Parameters: "remove"; Flags: runhidden