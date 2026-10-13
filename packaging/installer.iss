; Windows setup program for PyDataQuality. Built with Inno Setup 6:
;
;     python packaging/build.py
;     iscc /DAppVersion=0.3.0 packaging\installer.iss
;
; Writes dist\PyDataQuality-Setup.exe. It installs for the current user only,
; so it never asks for an administrator password.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F3B2C1E-8A4D-4E57-9B0A-2D7C5E1F4A90}
AppName=PyDataQuality
AppVersion={#AppVersion}
AppPublisher=Dominion Akinrotimi
AppPublisherURL=https://github.com/DominionAkinrotimi/PyDataQuality
AppSupportURL=https://github.com/DominionAkinrotimi/PyDataQuality/issues
DefaultDirName={autopf}\PyDataQuality
DefaultGroupName=PyDataQuality
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=PyDataQuality-Setup
SetupIconFile=..\pydataquality\static\icon.ico
UninstallDisplayIcon={app}\PyDataQuality.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Put a shortcut on the desktop"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\PyDataQuality\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\PyDataQuality"; Filename: "{app}\PyDataQuality.exe"
Name: "{autodesktop}\PyDataQuality"; Filename: "{app}\PyDataQuality.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PyDataQuality.exe"; Description: "Open PyDataQuality now"; Flags: nowait postinstall skipifsilent
