; Setup.iss (FCP)
; Inno Setup Script for File Converter Pro
; Dual language support: French / English
; Complete uninstallation support

#define MyAppName "File Converter Pro"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "Prime Enterprises"
#define MyAppURL "https://github.com/Hyacinthe-primus/File-Converter-Pro"
#define MyAppExeName "File Converter Pro.exe"
#define MyAppId "{{C1E31023-8141-4243-96B2-D3AAC59CAC6F}}"
#define MyDistDir "dist\File Converter Pro"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCopyright=© 2026 {#MyAppPublisher}. All rights reserved.
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=FileConverterPro_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico
WizardStyle=modern
WizardSmallImageFile=installer_banner.bmp
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "LICENSE\LICENSE.txt"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"; LicenseFile: "LICENSE\LICENSE_FR.txt"

[CustomMessages]
french.AddAntivirusExclusion=Ajouter une exclusion Windows Defender (recommandé pour les performances)
english.AddAntivirusExclusion=Add Windows Defender exclusion (recommended for performance)
french.AppDescription=File Converter Pro - Le convertisseur de fichiers professionnel et rapide, entièrement gratuit
english.AppDescription=File Converter Pro - Fast professional file converter, made for free
french.AssocFileType=Associer les fichiers .fcproj avec File Converter Pro
english.AssocFileType=Associate .fcproj files with File Converter Pro

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "assocfileext"; Description: "{cm:AssocFileType}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Uninstallation icon
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

Source: "{#MyDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "{#MyAppExeName}"

; Quick Check utility
Source: "{#MyDistDir}\Quick Check.exe"; DestDir: "{app}"; Flags: ignoreversion

; Language files
Source: "languages\*"; DestDir: "{app}\languages"; Flags: ignoreversion recursesubdirs; Excludes: "blank.lang,en-revisited.lang"

; Configuration and keys
Source: "file_converter_config.dat"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('file_converter_config.dat')
Source: "file_converter_key.key"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('file_converter_key.key')

; Databases
Source: "achievements.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('achievements.db')
Source: "file_converter_stats.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('file_converter_stats.db')
Source: "special_events.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('special_events.db')

; License
Source: "LICENSE\LICENSE.txt";    DestDir: "{app}"; Flags: ignoreversion; Check: IsEnglish()
Source: "LICENSE\LICENSE_FR.txt"; DestDir: "{app}"; Flags: ignoreversion; Check: IsFrench()

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Comment: "{cm:AppDescription}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Comment: "{cm:AppDescription}"; Tasks: desktopicon

[Registry]
; Association extension .fcproj
Root: HKCU; Subkey: "Software\Classes\.fcproj"; ValueType: string; ValueName: ""; ValueData: "FileConverterPro.Project"; Flags: uninsdeletevalue; Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project"; ValueType: string; ValueName: ""; ValueData: "File Converter Pro Project"; Flags: uninsdeletekey; Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icon.ico,0"; Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\shell\open"; ValueType: string; ValueName: "WorkingDirectory"; ValueData: "{app}"; Tasks: assocfileext

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--lang {code:GetLangCode}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{localappdata}\{#MyAppName}"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
var
  AntivirusExclusionCheckbox: TNewCheckBox;

function IsEnglish(): Boolean;
begin
  Result := ActiveLanguage() = 'english';
end;

function IsFrench(): Boolean;
begin
  Result := ActiveLanguage() = 'french';
end;

function GetLangCode(Param: String): String;
begin
  if ActiveLanguage() = 'french' then
    Result := 'fr'
  else
    Result := 'en';
end;

procedure WriteLanguageConfig();
var
  ConfigPath: String;
  JsonContent: String;
begin
  ConfigPath := ExpandConstant('{app}\file_converter_config.dat');

  if not FileExists(ConfigPath) then
  begin
    JsonContent := '{"language": "' + GetLangCode('') + '"}';
    SaveStringToFile(ConfigPath, JsonContent, False);
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('This application requires Windows 64-bit.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure InitializeWizard;
begin
  AntivirusExclusionCheckbox := TNewCheckBox.Create(WizardForm);
  AntivirusExclusionCheckbox.Parent := WizardForm.ReadyMemo.Parent;
  AntivirusExclusionCheckbox.Top := WizardForm.ReadyMemo.Top + WizardForm.ReadyMemo.Height + ScaleY(8);
  AntivirusExclusionCheckbox.Left := WizardForm.ReadyMemo.Left;
  AntivirusExclusionCheckbox.Width := WizardForm.ReadyMemo.Width;
  AntivirusExclusionCheckbox.Height := ScaleY(17);
  AntivirusExclusionCheckbox.Caption := CustomMessage('AddAntivirusExclusion');
  AntivirusExclusionCheckbox.Checked := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  AppPath: String;
begin
  if CurStep = ssPostInstall then begin
    ForceDirectories(ExpandConstant('{localappdata}\{#MyAppName}'));

    WriteLanguageConfig();

    if AntivirusExclusionCheckbox.Checked then begin
      AppPath := ExpandConstant('{app}');
      Exec('powershell.exe',
            '-NoProfile -ExecutionPolicy Bypass -Command "try { Add-MpPreference -ExclusionPath ''' + AppPath + ''' -ErrorAction Stop } catch { }"',
            '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
