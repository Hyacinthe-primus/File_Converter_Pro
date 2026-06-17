; Setup.iss (FCP)
; Inno Setup Script for File Converter Pro
; Multi-language support
; Complete uninstallation support

#define MyAppName "File Converter Pro"
#define MyAppVersion "1.0.6"
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
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "LICENSE\LICENSE.txt"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"; LicenseFile: "LICENSE\LICENSE.txt"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"; LicenseFile: "LICENSE\LICENSE.txt"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"; LicenseFile: "LICENSE\LICENSE.txt"

[CustomMessages]
french.AddAntivirusExclusion=Ajouter une exclusion Windows Defender (recommandé pour les performances)
english.AddAntivirusExclusion=Add Windows Defender exclusion (recommended for performance)
italian.AddAntivirusExclusion=Aggiungi un'esclusione a Windows Defender (consigliato per le prestazioni)
russian.AddAntivirusExclusion=Добавить исключение в Windows Defender (рекомендуется для производительности)

french.AppDescription=File Converter Pro - Le convertisseur de fichiers professionnel et rapide, entièrement gratuit
english.AppDescription=File Converter Pro - Fast professional file converter, made for free
italian.AppDescription=File Converter Pro - Il convertitore di file professionale e veloce, completamente gratuito
russian.AppDescription=File Converter Pro - быстрый профессиональный конвертер файлов, совершенно бесплатный

french.AssocFileType=Associer les fichiers .fcproj avec File Converter Pro
english.AssocFileType=Associate .fcproj files with File Converter Pro
italian.AssocFileType=Associa i file .fcproj a File Converter Pro
russian.AssocFileType=Связать файлы .fcproj с File Converter Pro

french.AddContextMenu=Ajouter "Convertir avec FCP" au menu contextuel Windows
english.AddContextMenu=Add "Convert with FCP" to Windows right-click menu
italian.AddContextMenu=Aggiungi "Convertire con FCP" al menu contestuale di Windows
russian.AddContextMenu=Добавить "Конвертировать с FCP" в контекстное меню Windows

french.ConvertWithFCP=Convertir avec FCP
english.ConvertWithFCP=Convert with FCP
italian.ConvertWithFCP=Convertire con FCP
russian.ConvertWithFCP=Конвертировать с FCP

[Tasks]
Name: "desktopicon";   Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "assocfileext";  Description: "{cm:AssocFileType}";         GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "contextmenu";   Description: "{cm:AddContextMenu}";        GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Uninstallation icon
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

Source: "{#MyDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "{#MyAppExeName}"

; License
Source: "LICENSE\LICENSE.txt";    DestDir: "{app}"; Flags: ignoreversion; Check: IsEnglish()
Source: "LICENSE\LICENSE_FR.txt"; DestDir: "{app}"; Flags: ignoreversion; Check: IsFrench()

[Icons]
Name: "{group}\{#MyAppName}";                          Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Comment: "{cm:AppDescription}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}";    Filename: "{uninstallexe}";        IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}";                    Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Comment: "{cm:AppDescription}"; Tasks: desktopicon

[Registry]
; Association extension .fcproj
Root: HKCU; Subkey: "Software\Classes\.fcproj";                                          ValueType: string; ValueName: ""; ValueData: "FileConverterPro.Project";     Flags: uninsdeletevalue;  Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project";                         ValueType: string; ValueName: ""; ValueData: "File Converter Pro Project";   Flags: uninsdeletekey;    Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\DefaultIcon";             ValueType: string; ValueName: ""; ValueData: "{app}\icon.ico,0";             Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\shell\open\command";      ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assocfileext
Root: HKCU; Subkey: "Software\Classes\FileConverterPro.Project\shell\open";              ValueType: string; ValueName: "WorkingDirectory"; ValueData: "{app}";        Tasks: assocfileext

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
  else if ActiveLanguage() = 'italian' then
    Result := 'it'
  else if ActiveLanguage() = 'russian' then
    Result := 'ru'
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

function IsPreservedFile(const FileName: String): Boolean;
var
  Lower: String;
begin
  Lower := LowerCase(FileName);
  Result := (Lower = 'achievements.db') or
            (Lower = 'file_converter_advanced.db') or
            (Lower = 'file_converter_config.dat') or
            (Lower = 'file_converter_key.key') or
            (Lower = 'file_converter_stats.db') or
            (Lower = 'special_events.db');
end;

procedure CleanInstallDir();
var
  FindRec: TFindRec;
  DirPath, FilePath: String;
begin
  DirPath := ExpandConstant('{app}');
  if not DirExists(DirPath) then Exit;

  if FindFirst(DirPath + '\*', FindRec) then
  begin
    repeat
      if (FindRec.Name = '.') or (FindRec.Name = '..') then Continue;
      FilePath := DirPath + '\' + FindRec.Name;

      if (FindRec.Attributes and $10) <> 0 then
      begin
        if LowerCase(FindRec.Name) <> 'automation' then
          DelTree(FilePath, True, True, True);
      end
      else
      begin
        if not IsPreservedFile(FindRec.Name) then
          DeleteFile(FilePath);
      end;
    until not FindNext(FindRec);
    FindClose(FindRec);
  end;
end;

procedure DeleteContextMenuForExtension(const Ext: String);
begin
  RegDeleteKeyIncludingSubkeys(HKCU,
    'Software\Classes\SystemFileAssociations\.' + Ext + '\shell\ConvertWithFCP');
end;

procedure CleanOldRegistry();
begin
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\.fcproj');
  RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Classes\FileConverterPro.Project');

  DeleteContextMenuForExtension('aac');
  DeleteContextMenuForExtension('apng');
  DeleteContextMenuForExtension('arw');
  DeleteContextMenuForExtension('avi');
  DeleteContextMenuForExtension('avif');
  DeleteContextMenuForExtension('bmp');
  DeleteContextMenuForExtension('cr2');
  DeleteContextMenuForExtension('cr3');
  DeleteContextMenuForExtension('csv');
  DeleteContextMenuForExtension('dng');
  DeleteContextMenuForExtension('doc');
  DeleteContextMenuForExtension('docx');
  DeleteContextMenuForExtension('epub');
  DeleteContextMenuForExtension('flac');
  DeleteContextMenuForExtension('gif');
  DeleteContextMenuForExtension('heic');
  DeleteContextMenuForExtension('heif');
  DeleteContextMenuForExtension('html');
  DeleteContextMenuForExtension('j2k');
  DeleteContextMenuForExtension('jfif');
  DeleteContextMenuForExtension('jp2');
  DeleteContextMenuForExtension('jpeg');
  DeleteContextMenuForExtension('jpg');
  DeleteContextMenuForExtension('jpx');
  DeleteContextMenuForExtension('json');
  DeleteContextMenuForExtension('m4a');
  DeleteContextMenuForExtension('mkv');
  DeleteContextMenuForExtension('mov');
  DeleteContextMenuForExtension('mp3');
  DeleteContextMenuForExtension('mp4');
  DeleteContextMenuForExtension('nef');
  DeleteContextMenuForExtension('ogg');
  DeleteContextMenuForExtension('orf');
  DeleteContextMenuForExtension('pdf');
  DeleteContextMenuForExtension('png');
  DeleteContextMenuForExtension('pptx');
  DeleteContextMenuForExtension('psd');
  DeleteContextMenuForExtension('raf');
  DeleteContextMenuForExtension('raw');
  DeleteContextMenuForExtension('rw2');
  DeleteContextMenuForExtension('rtf');
  DeleteContextMenuForExtension('svg');
  DeleteContextMenuForExtension('tif');
  DeleteContextMenuForExtension('tiff');
  DeleteContextMenuForExtension('txt');
  DeleteContextMenuForExtension('wav');
  DeleteContextMenuForExtension('webm');
  DeleteContextMenuForExtension('webp');
  DeleteContextMenuForExtension('xlsx');
end;

procedure AddConversion(SubKey, Num, MenuLabel, ConvType: String);
var
  ShellKey, ExePath: String;
begin
  ShellKey := SubKey + '\shell\' + Num;
  ExePath := ExpandConstant('{app}\{#MyAppExeName}');
  RegWriteStringValue(HKCU, ShellKey, 'MUIVerb', MenuLabel);
  RegWriteStringValue(HKCU, ShellKey, 'Icon', ExpandConstant('{app}\icon.ico,0'));
  RegWriteStringValue(HKCU, ShellKey + '\command', '', '"' + ExePath + '" --context-menu --files "%1" --conversion-type ' + ConvType);
end;

procedure RegisterContextMenuForExt(Ext: String);
var
  CM, SubKey: String;
begin
  CM := 'Software\Classes\SystemFileAssociations';
  SubKey := CM + '\.' + Ext + '\shell\ConvertWithFCP';
  RegWriteStringValue(HKCU, SubKey, 'MUIVerb', ExpandConstant('{cm:ConvertWithFCP}'));
  RegWriteStringValue(HKCU, SubKey, 'Icon', ExpandConstant('{app}\icon.ico,0'));
  RegWriteStringValue(HKCU, SubKey, 'SubCommands', '');

  if Ext = 'aac' then begin
    AddConversion(SubKey, '01_to_mp3', 'Audio → MP3', 'audio_to_mp3');
    AddConversion(SubKey, '02_to_wav', 'Audio → WAV', 'audio_to_wav');
    AddConversion(SubKey, '03_to_flac', 'Audio → FLAC', 'audio_to_flac');
    AddConversion(SubKey, '04_to_m4a', 'Audio → M4A', 'audio_to_m4a');
  end else if Ext = 'apng' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'arw' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'avi' then begin
    AddConversion(SubKey, '01_to_mp4', 'Video → MP4', 'video_to_mp4');
    AddConversion(SubKey, '02_to_mkv', 'Video → MKV', 'video_to_mkv');
    AddConversion(SubKey, '03_to_webm', 'Video → WEBM', 'video_to_webm');
    AddConversion(SubKey, '04_to_mov', 'Video → MOV', 'video_to_mov');
    AddConversion(SubKey, '05_to_mp3', 'Video → MP3', 'video_to_mp3');
    AddConversion(SubKey, '06_to_wav', 'Video → WAV', 'video_to_wav');
    AddConversion(SubKey, '07_to_aac', 'Video → AAC', 'video_to_aac');
    AddConversion(SubKey, '08_to_flac', 'Video → FLAC', 'video_to_flac');
  end else if Ext = 'avif' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'bmp' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'cr2' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'cr3' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'csv' then begin
    AddConversion(SubKey, '01_to_json', 'CSV → JSON', 'csv_to_json');
  end else if Ext = 'dng' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'doc' then begin
    AddConversion(SubKey, '01_to_pdf', 'Word → PDF', 'docx_to_pdf');
    AddConversion(SubKey, '02_merge_none', 'Merge (order)', 'merge_docx_none');
    AddConversion(SubKey, '03_merge_alpha_asc', 'Merge A→Z', 'merge_docx_alpha_asc');
    AddConversion(SubKey, '04_merge_alpha_desc', 'Merge Z→A', 'merge_docx_alpha_desc');
    AddConversion(SubKey, '05_merge_num_asc', 'Merge 1→9', 'merge_docx_num_asc');
    AddConversion(SubKey, '06_merge_num_desc', 'Merge 9→1', 'merge_docx_num_desc');
    AddConversion(SubKey, '07_merge_date_asc', 'Merge oldest', 'merge_docx_date_asc');
    AddConversion(SubKey, '08_merge_date_desc', 'Merge newest', 'merge_docx_date_desc');
  end else if Ext = 'docx' then begin
    AddConversion(SubKey, '01_to_pdf', 'Word → PDF', 'docx_to_pdf');
    AddConversion(SubKey, '02_merge_none', 'Merge (order)', 'merge_docx_none');
    AddConversion(SubKey, '03_merge_alpha_asc', 'Merge A→Z', 'merge_docx_alpha_asc');
    AddConversion(SubKey, '04_merge_alpha_desc', 'Merge Z→A', 'merge_docx_alpha_desc');
    AddConversion(SubKey, '05_merge_num_asc', 'Merge 1→9', 'merge_docx_num_asc');
    AddConversion(SubKey, '06_merge_num_desc', 'Merge 9→1', 'merge_docx_num_desc');
    AddConversion(SubKey, '07_merge_date_asc', 'Merge oldest', 'merge_docx_date_asc');
    AddConversion(SubKey, '08_merge_date_desc', 'Merge newest', 'merge_docx_date_desc');
  end else if Ext = 'epub' then begin
    AddConversion(SubKey, '01_to_pdf', 'ePub → PDF', 'epub_to_pdf');
  end else if Ext = 'flac' then begin
    AddConversion(SubKey, '01_to_mp3', 'Audio → MP3', 'audio_to_mp3');
    AddConversion(SubKey, '02_to_wav', 'Audio → WAV', 'audio_to_wav');
    AddConversion(SubKey, '03_to_aac', 'Audio → AAC', 'audio_to_aac');
    AddConversion(SubKey, '04_to_ogg', 'Audio → OGG', 'audio_to_ogg');
  end else if Ext = 'gif' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'heic' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'heif' then begin
    AddConversion(SubKey, '01_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '02_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '03_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '06_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '07_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '08_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'html' then begin
    AddConversion(SubKey, '01_to_pdf', 'HTML → PDF', 'html_to_pdf');
  end else if Ext = 'j2k' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'jfif' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'jp2' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'jpeg' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'jpg' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'jpx' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'json' then begin
    AddConversion(SubKey, '01_to_csv', 'JSON → CSV', 'json_to_csv');
  end else if Ext = 'm4a' then begin
    AddConversion(SubKey, '01_to_mp3', 'Audio → MP3', 'audio_to_mp3');
    AddConversion(SubKey, '02_to_wav', 'Audio → WAV', 'audio_to_wav');
    AddConversion(SubKey, '03_to_aac', 'Audio → AAC', 'audio_to_aac');
    AddConversion(SubKey, '04_to_flac', 'Audio → FLAC', 'audio_to_flac');
  end else if Ext = 'mkv' then begin
    AddConversion(SubKey, '01_to_mp4', 'Video → MP4', 'video_to_mp4');
    AddConversion(SubKey, '02_to_avi', 'Video → AVI', 'video_to_avi');
    AddConversion(SubKey, '03_to_webm', 'Video → WEBM', 'video_to_webm');
    AddConversion(SubKey, '04_to_mov', 'Video → MOV', 'video_to_mov');
    AddConversion(SubKey, '05_to_mp3', 'Video → MP3', 'video_to_mp3');
    AddConversion(SubKey, '06_to_wav', 'Video → WAV', 'video_to_wav');
    AddConversion(SubKey, '07_to_aac', 'Video → AAC', 'video_to_aac');
    AddConversion(SubKey, '08_to_flac', 'Video → FLAC', 'video_to_flac');
  end else if Ext = 'mov' then begin
    AddConversion(SubKey, '01_to_mp4', 'Video → MP4', 'video_to_mp4');
    AddConversion(SubKey, '02_to_mkv', 'Video → MKV', 'video_to_mkv');
    AddConversion(SubKey, '03_to_avi', 'Video → AVI', 'video_to_avi');
    AddConversion(SubKey, '04_to_webm', 'Video → WEBM', 'video_to_webm');
    AddConversion(SubKey, '05_to_mp3', 'Video → MP3', 'video_to_mp3');
    AddConversion(SubKey, '06_to_wav', 'Video → WAV', 'video_to_wav');
    AddConversion(SubKey, '07_to_aac', 'Video → AAC', 'video_to_aac');
    AddConversion(SubKey, '08_to_flac', 'Video → FLAC', 'video_to_flac');
  end else if Ext = 'mp3' then begin
    AddConversion(SubKey, '01_to_wav', 'Audio → WAV', 'audio_to_wav');
    AddConversion(SubKey, '02_to_aac', 'Audio → AAC', 'audio_to_aac');
    AddConversion(SubKey, '03_to_flac', 'Audio → FLAC', 'audio_to_flac');
    AddConversion(SubKey, '04_to_ogg', 'Audio → OGG', 'audio_to_ogg');
    AddConversion(SubKey, '05_to_m4a', 'Audio → M4A', 'audio_to_m4a');
  end else if Ext = 'mp4' then begin
    AddConversion(SubKey, '01_to_mkv', 'Video → MKV', 'video_to_mkv');
    AddConversion(SubKey, '02_to_avi', 'Video → AVI', 'video_to_avi');
    AddConversion(SubKey, '03_to_webm', 'Video → WEBM', 'video_to_webm');
    AddConversion(SubKey, '04_to_mov', 'Video → MOV', 'video_to_mov');
    AddConversion(SubKey, '05_to_mp3', 'Video → MP3', 'video_to_mp3');
    AddConversion(SubKey, '06_to_wav', 'Video → WAV', 'video_to_wav');
    AddConversion(SubKey, '07_to_aac', 'Video → AAC', 'video_to_aac');
    AddConversion(SubKey, '08_to_flac', 'Video → FLAC', 'video_to_flac');
  end else if Ext = 'nef' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'ogg' then begin
    AddConversion(SubKey, '01_to_mp3', 'Audio → MP3', 'audio_to_mp3');
    AddConversion(SubKey, '02_to_wav', 'Audio → WAV', 'audio_to_wav');
    AddConversion(SubKey, '03_to_aac', 'Audio → AAC', 'audio_to_aac');
    AddConversion(SubKey, '04_to_flac', 'Audio → FLAC', 'audio_to_flac');
  end else if Ext = 'orf' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'pdf' then begin
    AddConversion(SubKey, '01_to_docx', 'PDF → Word', 'pdf_to_docx');
    AddConversion(SubKey, '02_to_html', 'PDF → HTML', 'pdf_to_html');
    AddConversion(SubKey, '03_merge_none', 'Merge (order)', 'merge_pdf_none');
    AddConversion(SubKey, '04_merge_alpha_asc', 'Merge A→Z', 'merge_pdf_alpha_asc');
    AddConversion(SubKey, '05_merge_alpha_desc', 'Merge Z→A', 'merge_pdf_alpha_desc');
    AddConversion(SubKey, '06_merge_num_asc', 'Merge 1→9', 'merge_pdf_num_asc');
    AddConversion(SubKey, '07_merge_num_desc', 'Merge 9→1', 'merge_pdf_num_desc');
    AddConversion(SubKey, '08_merge_date_asc', 'Merge oldest', 'merge_pdf_date_asc');
    AddConversion(SubKey, '09_merge_date_desc', 'Merge newest', 'merge_pdf_date_desc');
  end else if Ext = 'png' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'pptx' then begin
    AddConversion(SubKey, '01_to_pdf', 'PPTX → PDF', 'pptx_to_pdf');
  end else if Ext = 'psd' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'raf' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'raw' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'rtf' then begin
    AddConversion(SubKey, '01_to_pdf', 'RTF → PDF', 'rtf_to_pdf');
    AddConversion(SubKey, '02_to_docx', 'RTF → Word', 'rtf_to_docx');
  end else if Ext = 'rw2' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'svg' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'tif' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'tiff' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'txt' then begin
    AddConversion(SubKey, '01_to_pdf', 'TXT → PDF', 'txt_to_pdf');
    AddConversion(SubKey, '02_to_docx', 'TXT → Word', 'txt_to_docx');
  end else if Ext = 'wav' then begin
    AddConversion(SubKey, '01_to_mp3', 'Audio → MP3', 'audio_to_mp3');
    AddConversion(SubKey, '02_to_aac', 'Audio → AAC', 'audio_to_aac');
    AddConversion(SubKey, '03_to_flac', 'Audio → FLAC', 'audio_to_flac');
    AddConversion(SubKey, '04_to_ogg', 'Audio → OGG', 'audio_to_ogg');
    AddConversion(SubKey, '05_to_m4a', 'Audio → M4A', 'audio_to_m4a');
  end else if Ext = 'webm' then begin
    AddConversion(SubKey, '01_to_mp4', 'Video → MP4', 'video_to_mp4');
    AddConversion(SubKey, '02_to_mkv', 'Video → MKV', 'video_to_mkv');
    AddConversion(SubKey, '03_to_avi', 'Video → AVI', 'video_to_avi');
    AddConversion(SubKey, '04_to_mov', 'Video → MOV', 'video_to_mov');
    AddConversion(SubKey, '05_to_mp3', 'Video → MP3', 'video_to_mp3');
    AddConversion(SubKey, '06_to_wav', 'Video → WAV', 'video_to_wav');
    AddConversion(SubKey, '07_to_aac', 'Video → AAC', 'video_to_aac');
    AddConversion(SubKey, '08_to_flac', 'Video → FLAC', 'video_to_flac');
  end else if Ext = 'webp' then begin
    AddConversion(SubKey, '01_to_jpg', 'Image → JPG', 'image_to_jpg');
    AddConversion(SubKey, '02_to_jpeg', 'Image → JPEG', 'image_to_jpeg');
    AddConversion(SubKey, '03_to_bmp', 'Image → BMP', 'image_to_bmp');
    AddConversion(SubKey, '04_to_webp', 'Image → WEBP', 'image_to_webp');
    AddConversion(SubKey, '05_to_tiff', 'Image → TIFF', 'image_to_tiff');
    AddConversion(SubKey, '06_to_avif', 'Image → AVIF', 'image_to_avif');
    AddConversion(SubKey, '07_to_svg', 'Image → SVG', 'image_to_svg');
    AddConversion(SubKey, '08_to_ico', 'Image → ICO', 'image_to_ico');
    AddConversion(SubKey, '09_to_pdf', 'Image → PDF', 'image_to_pdf');
    AddConversion(SubKey, '10_to_heic', 'Image → HEIC', 'image_to_heic');
    AddConversion(SubKey, '11_to_psd', 'Image → PSD', 'image_to_psd');
    AddConversion(SubKey, '12_to_dng', 'Image → DNG', 'image_to_dng');
    AddConversion(SubKey, '13_to_j2k', 'Image → J2K', 'image_to_j2k');
    AddConversion(SubKey, '14_to_png', 'Image → PNG', 'image_to_png');
    AddConversion(SubKey, '15_to_pdf_merged', 'Images → PDF (merged)', 'images_to_pdf_merged');
  end else if Ext = 'xlsx' then begin
    AddConversion(SubKey, '01_to_pdf', 'Excel → PDF', 'xlsx_to_pdf');
    AddConversion(SubKey, '02_to_csv', 'Excel → CSV', 'xlsx_to_csv');
    AddConversion(SubKey, '03_to_json', 'Excel → JSON', 'xlsx_to_json');
  end;
end;

procedure RegisterAllContextMenus();
var
  Exts: array of String;
  I: Integer;
begin
  Exts := ['aac','apng','arw','avi','avif','bmp','cr2','cr3','csv','dng',
           'doc','docx','epub','flac','gif','heic','heif','html','j2k','jfif',
           'jp2','jpeg','jpg','jpx','json','m4a','mkv','mov','mp3','mp4',
           'nef','ogg','orf','pdf','png','pptx','psd','raf','raw','rw2','rtf',
           'svg','tif','tiff','txt','wav','webm','webp','xlsx'];
  for I := 0 to GetArrayLength(Exts) - 1 do
    RegisterContextMenuForExt(Exts[I]);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  Exec('taskkill.exe', '/f /im "File Converter Pro.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(500);

  if DirExists(ExpandConstant('{app}')) then
  begin
    CleanInstallDir();
    CleanOldRegistry();
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
  AntivirusExclusionCheckbox.Parent  := WizardForm.ReadyMemo.Parent;
  AntivirusExclusionCheckbox.Top     := WizardForm.ReadyMemo.Top + WizardForm.ReadyMemo.Height + ScaleY(8);
  AntivirusExclusionCheckbox.Left    := WizardForm.ReadyMemo.Left;
  AntivirusExclusionCheckbox.Width   := WizardForm.ReadyMemo.Width;
  AntivirusExclusionCheckbox.Height  := ScaleY(17);
  AntivirusExclusionCheckbox.Caption := CustomMessage('AddAntivirusExclusion');
  AntivirusExclusionCheckbox.Checked := True;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  I: Integer;
begin
  if CurPageID = wpSelectTasks then
    for I := 0 to WizardForm.TasksList.Items.Count - 1 do
      WizardForm.TasksList.Checked[I] := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    CleanOldRegistry();
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  AppPath: String;
begin
  if CurStep = ssPostInstall then begin
    ForceDirectories(ExpandConstant('{localappdata}\{#MyAppName}'));

    if WizardIsTaskSelected('contextmenu') then
      RegisterAllContextMenus();

    WriteLanguageConfig();

    if AntivirusExclusionCheckbox.Checked then begin
      AppPath := ExpandConstant('{app}');
      Exec('powershell.exe',
            '-NoProfile -ExecutionPolicy Bypass -Command "try { Add-MpPreference -ExclusionPath ''' + AppPath + ''' -ErrorAction Stop } catch { }"',
            '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
