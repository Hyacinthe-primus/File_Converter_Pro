; Setup.iss (FCP)
; Inno Setup Script for File Converter Pro
; Dual language support: French / English
; Complete uninstallation support

#define MyAppName "File Converter Pro"
#define MyAppVersion "1.0.3"
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

;IMAGES

; .jpg / .jpeg
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\02_to_png";      ValueType: string; ValueName: "MUIVerb"; ValueData: "JPG → PNG";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type jpg_to_png"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\03_to_ico";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpg\shell\ConvertWithFCP\shell\03_to_ico\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu

Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\02_to_png";     ValueType: string; ValueName: "MUIVerb"; ValueData: "JPEG → PNG";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type jpeg_to_png"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\03_to_ico";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.jpeg\shell\ConvertWithFCP\shell\03_to_ico\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu

; .png
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\02_to_jpg";      ValueType: string; ValueName: "MUIVerb"; ValueData: "PNG → JPG";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\02_to_jpg\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type png_to_jpg"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\03_to_ico";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → ICO";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.png\shell\ConvertWithFCP\shell\03_to_ico\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_ico"; Tasks: contextmenu

; .webp
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\02_to_png";     ValueType: string; ValueName: "MUIVerb"; ValueData: "WEBP → PNG";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webp\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type webp_to_png"; Tasks: contextmenu

; .bmp
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\02_to_png";      ValueType: string; ValueName: "MUIVerb"; ValueData: "BMP → PNG";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.bmp\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type bmp_to_png"; Tasks: contextmenu

; .gif
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\02_to_png";      ValueType: string; ValueName: "MUIVerb"; ValueData: "GIF → PNG";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.gif\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type gif_to_png"; Tasks: contextmenu

; .tiff / .tif
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\02_to_png";     ValueType: string; ValueName: "MUIVerb"; ValueData: "TIFF → PNG";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tiff\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type tiff_to_png"; Tasks: contextmenu

Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\02_to_png";      ValueType: string; ValueName: "MUIVerb"; ValueData: "TIFF → PNG";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.tif\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type tiff_to_png"; Tasks: contextmenu

; .heic
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Image → PDF";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type image_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\02_to_png";     ValueType: string; ValueName: "MUIVerb"; ValueData: "HEIC → PNG";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.heic\shell\ConvertWithFCP\shell\02_to_png\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type heic_to_png"; Tasks: contextmenu

;DOCUMENTS

; .docx / .doc
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "Word → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.docx\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type docx_to_pdf"; Tasks: contextmenu

Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "Word → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.doc\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type docx_to_pdf"; Tasks: contextmenu

; .pdf
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\01_to_docx";     ValueType: string; ValueName: "MUIVerb"; ValueData: "PDF → Word";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\01_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pdf_to_docx"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\02_to_html";     ValueType: string; ValueName: "MUIVerb"; ValueData: "PDF → HTML";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pdf\shell\ConvertWithFCP\shell\02_to_html\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pdf_to_html"; Tasks: contextmenu

; .txt
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "TXT → PDF";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type txt_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\02_to_docx";     ValueType: string; ValueName: "MUIVerb"; ValueData: "TXT → DOCX";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.txt\shell\ConvertWithFCP\shell\02_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type txt_to_docx"; Tasks: contextmenu

; .rtf
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\01_to_pdf";      ValueType: string; ValueName: "MUIVerb"; ValueData: "RTF → PDF";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type rtf_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\02_to_docx";     ValueType: string; ValueName: "MUIVerb"; ValueData: "RTF → DOCX";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.rtf\shell\ConvertWithFCP\shell\02_to_docx\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type rtf_to_docx"; Tasks: contextmenu

; .xlsx
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_pdf"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\02_to_csv";     ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → CSV";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\02_to_csv\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_csv"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\03_to_json";    ValueType: string; ValueName: "MUIVerb"; ValueData: "XLSX → JSON";       Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.xlsx\shell\ConvertWithFCP\shell\03_to_json\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type xlsx_to_json"; Tasks: contextmenu

; .pptx
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "PPTX → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.pptx\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type pptx_to_pdf"; Tasks: contextmenu

; .html
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "HTML → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.html\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type html_to_pdf"; Tasks: contextmenu

; .epub
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP\shell\01_to_pdf";     ValueType: string; ValueName: "MUIVerb"; ValueData: "EPUB → PDF";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.epub\shell\ConvertWithFCP\shell\01_to_pdf\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type epub_to_pdf"; Tasks: contextmenu

; .csv
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP\shell\01_to_json";     ValueType: string; ValueName: "MUIVerb"; ValueData: "CSV → JSON";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.csv\shell\ConvertWithFCP\shell\01_to_json\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type csv_to_json"; Tasks: contextmenu

; .json
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP\shell\01_to_csv";     ValueType: string; ValueName: "MUIVerb"; ValueData: "JSON → CSV";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.json\shell\ConvertWithFCP\shell\01_to_csv\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type json_to_csv"; Tasks: contextmenu

;AUDIO

; .wav
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\01_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "WAV → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.wav\shell\ConvertWithFCP\shell\01_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type wav_to_mp3"; Tasks: contextmenu

; .mp3
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\01_to_wav";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MP3 → WAV";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\01_to_wav\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mp3_to_wav"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\02_to_aac";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MP3 → AAC";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp3\shell\ConvertWithFCP\shell\02_to_aac\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mp3_to_acc"; Tasks: contextmenu

; .flac
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\01_to_mp3";     ValueType: string; ValueName: "MUIVerb"; ValueData: "FLAC → MP3";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.flac\shell\ConvertWithFCP\shell\01_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type flac_to_mp3"; Tasks: contextmenu

; .ogg
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\01_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "OGG → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.ogg\shell\ConvertWithFCP\shell\01_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type ogg_to_mp3"; Tasks: contextmenu

; .aac
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\01_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "AAC → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.aac\shell\ConvertWithFCP\shell\01_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type acc_to_mp3"; Tasks: contextmenu

;VIDEO

; .mp4
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\01_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MP4 → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mp4\shell\ConvertWithFCP\shell\01_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mp4_to_mp3"; Tasks: contextmenu

; .avi
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\01_to_mp4";      ValueType: string; ValueName: "MUIVerb"; ValueData: "AVI → MP4";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\01_to_mp4\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type avi_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\02_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "AVI → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.avi\shell\ConvertWithFCP\shell\02_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type avi_to_mp3"; Tasks: contextmenu

; .mkv
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\01_to_mp4";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MKV → MP4";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\01_to_mp4\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mkv_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\02_to_mp3";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MKV → MP3";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mkv\shell\ConvertWithFCP\shell\02_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mkv_to_mp3"; Tasks: contextmenu

; .mov
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                      ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                      ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP";                      ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\01_to_mp4";      ValueType: string; ValueName: "MUIVerb"; ValueData: "MOV → MP4";         Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.mov\shell\ConvertWithFCP\shell\01_to_mp4\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type mov_to_mp4"; Tasks: contextmenu

; .webm
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                     ValueType: string; ValueName: "MUIVerb"; ValueData: "{cm:ConvertWithFCP}";  Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                     ValueType: string; ValueName: "Icon"; ValueData: "{#ICON}";       Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP";                     ValueType: string; ValueName: "SubCommands"; ValueData: "";        Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\01_to_mp4";     ValueType: string; ValueName: "MUIVerb"; ValueData: "WEBM → MP4";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\01_to_mp4\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type webm_to_mp4"; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\02_to_mp3";     ValueType: string; ValueName: "MUIVerb"; ValueData: "WEBM → MP3";        Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "{#CM}\.webm\shell\ConvertWithFCP\shell\02_to_mp3\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --context-menu --files ""%1"" --conversion-type webm_to_mp3"; Tasks: contextmenu

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
