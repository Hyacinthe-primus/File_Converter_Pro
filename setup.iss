; Setup.iss (FCP)
; Inno Setup Script for File Converter Pro
; Dual language support: French / English
; Complete uninstallation support

#define MyAppName "File Converter Pro"
#define MyAppVersion "1.0.4"
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
french.AddContextMenu=Ajouter "Convertir avec FCP" au menu contextuel Windows
english.AddContextMenu=Add "Convert with FCP" to Windows right-click menu
french.ConvertWithFCP=Convertir avec FCP
english.ConvertWithFCP=Convert with FCP

[Tasks]
Name: "desktopicon";   Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "assocfileext";  Description: "{cm:AssocFileType}";         GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "contextmenu";   Description: "{cm:AddContextMenu}";        GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

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
Source: "file_converter_key.key";    DestDir: "{app}"; Flags: ignoreversion; Check: FileExists('file_converter_key.key')

; Databases
Source: "achievements.db";         DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('achievements.db')
Source: "file_converter_stats.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('file_converter_stats.db')
Source: "special_events.db";       DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists('special_events.db')

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

#define CM "Software\Classes\SystemFileAssociations"
#define EXE """{app}\{#MyAppExeName}"""
#define ICON "{app}\icon.ico,0"
#define BASE "--context-menu --files ""%1"""

; IMAGES

; .png
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .jpeg
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .jpg
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .bmp
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .webp
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .tiff
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .tif
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .heic
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .heif
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\01_to_png";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\01_to_png";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\01_to_png\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\02_to_jpg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\02_to_jpg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\02_to_jpg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\03_to_jpeg";         ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\03_to_jpeg";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\03_to_jpeg\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\04_to_webp";         ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\04_to_webp";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\04_to_webp\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\05_to_avif";         ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\05_to_avif";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\05_to_avif\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\06_to_svg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\06_to_svg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\06_to_svg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\07_to_ico";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\07_to_ico";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\07_to_ico\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\08_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\08_to_pdf";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heif\shell\ConvertWithFCP\shell\08_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu

; .jfif
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jfif\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .avif
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avif\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .psd
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.psd\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .svg
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.svg\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .dng
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.dng\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .raw
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raw\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .gif
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .apng
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.apng\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .jp2
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jp2\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .jpx
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpx\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .j2k
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.j2k\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .cr2
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr2\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .cr3
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.cr3\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .nef
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.nef\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .arw
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.arw\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .orf
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.orf\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .rw2
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rw2\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; .raf
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\01_to_jpg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\01_to_jpg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\01_to_jpg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\02_to_jpeg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → JPEG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\02_to_jpeg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\02_to_jpeg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_jpeg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\03_to_bmp";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → BMP";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\03_to_bmp";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\03_to_bmp\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_bmp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\04_to_webp";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → WEBP";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\04_to_webp";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\04_to_webp\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_webp"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\05_to_tiff";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → TIFF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\05_to_tiff";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\05_to_tiff\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_tiff"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\06_to_avif";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → AVIF";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\06_to_avif";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\06_to_avif\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_avif"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\07_to_svg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → SVG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\07_to_svg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\07_to_svg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_svg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\08_to_ico";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\08_to_ico";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\08_to_ico\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\09_to_pdf";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\09_to_pdf";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\09_to_pdf\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\10_to_heic";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → HEIC";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\10_to_heic";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\10_to_heic\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_heic"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\11_to_psd";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PSD";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\11_to_psd";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\11_to_psd\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_psd"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\12_to_dng";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → DNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\12_to_dng";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\12_to_dng\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_dng"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\13_to_j2k";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → J2K";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\13_to_j2k";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\13_to_j2k\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_j2k"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\14_to_png";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PNG";    Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\14_to_png";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.raf\shell\ConvertWithFCP\shell\14_to_png\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_png"; Tasks: contextmenu

; DOCUMENTS

; .docx
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                         ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                         ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP\shell\01_to_pdf";         ValueType: string; ValueName: "MUIVerb"; ValueData: "Word → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP\shell\01_to_pdf";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type docx_to_pdf"; Tasks: contextmenu

; .doc
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Word → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type docx_to_pdf"; Tasks: contextmenu

; .pdf
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\01_to_docx";         ValueType: string; ValueName: "MUIVerb"; ValueData: "PDF → Word";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\01_to_docx";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\01_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pdf_to_docx"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\02_to_html";         ValueType: string; ValueName: "MUIVerb"; ValueData: "PDF → HTML";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\02_to_html";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\02_to_html\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pdf_to_html"; Tasks: contextmenu

; .txt
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "TXT → PDF";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type txt_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\02_to_docx";         ValueType: string; ValueName: "MUIVerb"; ValueData: "TXT → DOCX";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\02_to_docx";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\02_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type txt_to_docx"; Tasks: contextmenu

; .rtf
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "RTF → PDF";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type rtf_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\02_to_docx";         ValueType: string; ValueName: "MUIVerb"; ValueData: "RTF → DOCX";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\02_to_docx";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\02_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type rtf_to_docx"; Tasks: contextmenu

; .xlsx
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\02_to_csv";          ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → CSV";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\02_to_csv";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\02_to_csv\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_csv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\03_to_json";         ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → JSON";           Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\03_to_json";         ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\03_to_json\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_json"; Tasks: contextmenu

; .pptx
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "PPTX → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pptx_to_pdf"; Tasks: contextmenu

; .html
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "HTML → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type html_to_pdf"; Tasks: contextmenu

; .epub
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "MUIVerb"; ValueData: "EPUB → PDF";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP\shell\01_to_pdf";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP\shell\01_to_pdf\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type epub_to_pdf"; Tasks: contextmenu

; .csv
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP\shell\01_to_json";          ValueType: string; ValueName: "MUIVerb"; ValueData: "CSV → JSON";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP\shell\01_to_json";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP\shell\01_to_json\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type csv_to_json"; Tasks: contextmenu

; .json
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                 Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands"; ValueData: "";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP\shell\01_to_csv";          ValueType: string; ValueName: "MUIVerb"; ValueData: "JSON → CSV";            Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP\shell\01_to_csv";          ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";                  Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP\shell\01_to_csv\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type json_to_csv"; Tasks: contextmenu

; AUDIO

; .mp3
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\01_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\01_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\01_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\02_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\02_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\02_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\03_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\03_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\03_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_flac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\04_to_ogg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → OGG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\04_to_ogg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\04_to_ogg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_ogg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\05_to_m4a";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → M4A";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\05_to_m4a";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\05_to_m4a\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_m4a"; Tasks: contextmenu

; .wav
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\01_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\01_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\01_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\02_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\02_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\02_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\03_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\03_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\03_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_flac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\04_to_ogg";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → OGG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\04_to_ogg";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\04_to_ogg\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_ogg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\05_to_m4a";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → M4A";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\05_to_m4a";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\05_to_m4a\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_m4a"; Tasks: contextmenu

; .aac
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\01_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\01_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\01_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\02_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\02_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\02_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\03_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\03_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\03_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_flac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\04_to_m4a";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → M4A";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\04_to_m4a";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\04_to_m4a\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_m4a"; Tasks: contextmenu

; .flac
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\01_to_mp3";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\01_to_mp3";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\01_to_mp3\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\02_to_wav";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\02_to_wav";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\02_to_wav\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\03_to_aac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\03_to_aac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\03_to_aac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\04_to_ogg";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → OGG";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\04_to_ogg";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\04_to_ogg\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_ogg"; Tasks: contextmenu

; .ogg
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\01_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\01_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\01_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\02_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\02_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\02_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\03_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\03_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\03_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\04_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\04_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\04_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_flac"; Tasks: contextmenu

; .m4a
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\01_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\01_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\01_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\02_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\02_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\02_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\03_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\03_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\03_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\04_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Audio → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\04_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.m4a\shell\ConvertWithFCP\shell\04_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type audio_to_flac"; Tasks: contextmenu

; VIDEO

; .mp4
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\01_to_mkv";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MKV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\01_to_mkv";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\01_to_mkv\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mkv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\02_to_avi";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AVI";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\02_to_avi";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\02_to_avi\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_avi"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\03_to_webm";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WEBM";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\03_to_webm";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\03_to_webm\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_webm"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\04_to_mov";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MOV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\04_to_mov";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\04_to_mov\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mov"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\05_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\05_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\05_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\06_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\06_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\06_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\07_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\07_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\07_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\08_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\08_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\08_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_flac"; Tasks: contextmenu

; .webm
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                          ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                          ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                          ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\01_to_mp4";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP4";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\01_to_mp4";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\01_to_mp4\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\02_to_mkv";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MKV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\02_to_mkv";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\02_to_mkv\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mkv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\03_to_avi";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AVI";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\03_to_avi";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\03_to_avi\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_avi"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\04_to_mov";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MOV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\04_to_mov";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\04_to_mov\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mov"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\05_to_mp3";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\05_to_mp3";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\05_to_mp3\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\06_to_wav";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\06_to_wav";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\06_to_wav\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\07_to_aac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\07_to_aac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\07_to_aac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\08_to_flac";         ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\08_to_flac";           ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\08_to_flac\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_flac"; Tasks: contextmenu

; .mkv
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\01_to_mp4";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP4";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\01_to_mp4";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\01_to_mp4\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\02_to_avi";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AVI";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\02_to_avi";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\02_to_avi\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_avi"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\03_to_webm";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WEBM";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\03_to_webm";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\03_to_webm\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_webm"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\04_to_mov";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MOV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\04_to_mov";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\04_to_mov\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mov"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\05_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\05_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\05_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\06_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\06_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\06_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\07_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\07_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\07_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\08_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\08_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\08_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_flac"; Tasks: contextmenu

; .mov
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\01_to_mp4";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP4";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\01_to_mp4";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\01_to_mp4\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\02_to_mkv";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MKV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\02_to_mkv";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\02_to_mkv\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mkv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\03_to_avi";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AVI";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\03_to_avi";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\03_to_avi\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_avi"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\04_to_webm";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WEBM";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\04_to_webm";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\04_to_webm\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_webm"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\05_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\05_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\05_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\06_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\06_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\06_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\07_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\07_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\07_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\08_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\08_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\08_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_flac"; Tasks: contextmenu

; .avi
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                           ValueType: string; ValueName: "MUIVerb";      ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                           ValueType: string; ValueName: "Icon";         ValueData: "{#ICON}";             Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                           ValueType: string; ValueName: "SubCommands";  ValueData: "";                    Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\01_to_mp4";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP4";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\01_to_mp4";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\01_to_mp4\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\02_to_mkv";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MKV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\02_to_mkv";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\02_to_mkv\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mkv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\03_to_webm";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WEBM";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\03_to_webm";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\03_to_webm\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_webm"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\04_to_mov";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MOV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\04_to_mov";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\04_to_mov\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mov"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\05_to_mp3";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → MP3";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\05_to_mp3";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\05_to_mp3\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_mp3"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\06_to_wav";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → WAV";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\06_to_wav";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\06_to_wav\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\07_to_aac";           ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → AAC";   Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\07_to_aac";             ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\07_to_aac\command";   ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_aac"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\08_to_flac";          ValueType: string; ValueName: "MUIVerb"; ValueData: "Video → FLAC";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\08_to_flac";            ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\08_to_flac\command";  ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type video_to_flac"; Tasks: contextmenu

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
