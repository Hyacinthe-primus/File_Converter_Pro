# Automated Build Script - File Converter Pro

param(
    [string]$IssFile   = "setup.iss",
    [string]$OutputDir = "Output",
    [string]$DistDir   = "dist\File Converter Pro"
)

# Paths
$IsccPath        = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
$JsonHistoryPath = Join-Path $OutputDir "build_stats.json"

$ColorTitle     = "Cyan"
$ColorSuccess   = "Green"
$ColorWarning   = "Yellow"
$ColorError     = "Red"
$ColorInfo      = "White"
$ColorHighlight = "Magenta"
$ColorDim       = "Gray"

$script:Checks = [System.Collections.Generic.List[hashtable]]::new()

function Add-CheckResult {
    param([string]$Label, [bool]$Passed, [string]$Detail = "")
    $script:Checks.Add(@{ Label = $Label; Passed = $Passed; Detail = $Detail })
}

function Write-Title {
    param([string]$Text)
    Write-Host "`n$("=" * 80)" -ForegroundColor $ColorTitle
    Write-Host "  $Text" -ForegroundColor $ColorTitle
    Write-Host "$("=" * 80)`n" -ForegroundColor $ColorTitle
}

function Write-Step     { param([string]$T) Write-Host "[*] $T" -ForegroundColor $ColorInfo }
function Write-Success  { param([string]$T) Write-Host "[✓] $T" -ForegroundColor $ColorSuccess }
function Write-Warning  { param([string]$T) Write-Host "[!] $T" -ForegroundColor $ColorWarning }
function Write-ErrorMsg { param([string]$T) Write-Host "[✗] $T" -ForegroundColor $ColorError }

function Format-FileSize {
    param([long]$Bytes)
    if ($Bytes -ge 1GB)     { return "{0:N2} GB"    -f ($Bytes / 1GB) }
    elseif ($Bytes -ge 1MB) { return "{0:N2} MB"    -f ($Bytes / 1MB) }
    elseif ($Bytes -ge 1KB) { return "{0:N2} KB"    -f ($Bytes / 1KB) }
    else                    { return "{0:N0} bytes"  -f $Bytes }
}

function Format-Row {
    param([string]$Label, [string]$Value)
    $inner = "  $($Label.PadRight(20)): $Value"
    $width = 73
    if ($inner.Length -gt $width) { $inner = $inner.Substring(0, $width - 3) + "..." }
    return "│$($inner.PadRight($width))│"
}

function Format-Sep   { return "│  $("─" * 68)   │" }
function Format-Head  { param([string]$T) "│  $($T.PadRight(71))│" }
function Format-Blank { return "│$(" " * 73)│" }

function Get-CompressionRatio {
    param([long]$OriginalSize, [long]$CompressedSize)
    if ($OriginalSize -eq 0) { return "N/A" }
    $ratio = (($OriginalSize - $CompressedSize) / $OriginalSize) * 100
    $sign = if ($ratio -gt 0) { "" } else { "+" }
    return "{0}{1:N2}%" -f $sign, [Math]::Abs($ratio)
}

function Get-FileSHA256 {
    param([string]$Path)
    try   { return (Get-FileHash -Path $Path -Algorithm SHA256 -ErrorAction Stop).Hash }
    catch { return "N/A" }
}

function Get-FileSHA256Short {
    param([string]$Path)
    $full = Get-FileSHA256 $Path
    if ($full -eq "N/A") { return "N/A" }
    return $full.Substring(0, 16) + "..."
}

function Invoke-WithSpinner {
    param(
        [string]$Message,
        [string]$IsccPath,
        [string]$IssFile,
        [string]$OutputDir
    )

    $frames   = @("⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏")
    $exitFile = [System.IO.Path]::GetTempFileName()

    $job = Start-Job -ScriptBlock {
        param($iscc, $iss, $outDir, $exitFile)
        try {
            $p = Start-Process -FilePath $iscc `
                -ArgumentList "`"$iss`"" `
                -Wait -NoNewWindow -PassThru `
                -RedirectStandardOutput "$outDir\iscc_output.log" `
                -RedirectStandardError  "$outDir\iscc_error.log"
            Set-Content -Path $exitFile -Value $p.ExitCode
        } catch {
            Set-Content -Path $exitFile -Value "99"
        }
    } -ArgumentList $IsccPath, $IssFile, $OutputDir, $exitFile

    $i = 0
    Write-Host ""
    while ($job.State -eq "Running") {
        $frame = $frames[$i % $frames.Length]
        Write-Host "`r  $frame  $Message..." -NoNewline -ForegroundColor $ColorHighlight
        Start-Sleep -Milliseconds 80
        $i++
    }

    Receive-Job $job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job  $job -ErrorAction SilentlyContinue

    Write-Host "`r  [✓]  $Message -- done!          " -ForegroundColor $ColorSuccess
    Write-Host ""

    $code = if (Test-Path $exitFile) { [int](Get-Content $exitFile) } else { 99 }
    Remove-Item $exitFile -ErrorAction SilentlyContinue
    return $code
}


function Get-SystemInfo {
    $os  = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $cpu = Get-CimInstance Win32_Processor       -ErrorAction SilentlyContinue | Select-Object -First 1
    $mem = Get-CimInstance Win32_ComputerSystem  -ErrorAction SilentlyContinue
    return @{
        OS          = if ($os)  { $os.Caption }                                    else { "N/A" }
        OSBuild     = if ($os)  { $os.BuildNumber }                                else { "N/A" }
        CPU         = if ($cpu) { $cpu.Name.Trim() }                               else { "N/A" }
        CPUCores    = if ($cpu) { $cpu.NumberOfLogicalProcessors }                 else { "N/A" }
        TotalRAM_GB = if ($mem) { [math]::Round($mem.TotalPhysicalMemory/1GB, 2) } else { "N/A" }
        FreeRAM_GB  = if ($os)  { [math]::Round($os.FreePhysicalMemory/1MB,  2) } else { "N/A" }
        PSVersion   = $PSVersionTable.PSVersion.ToString()
        Machine     = $env:COMPUTERNAME
        User        = $env:USERNAME
    }
}


function Get-DistInventory {
    param([string]$Dir)
    if (-not (Test-Path $Dir)) {
        return @{ Files = @(); TotalSize = 0; FileCount = 0; DirCount = 0 }
    }

    $allFiles = Get-ChildItem -Path $Dir -Recurse -File      -ErrorAction SilentlyContinue
    $allDirs  = Get-ChildItem -Path $Dir -Recurse -Directory -ErrorAction SilentlyContinue
    $rootPath = (Resolve-Path $Dir).Path + "\"

    $inventory = foreach ($f in $allFiles) {
        [PSCustomObject]@{
            RelativePath  = $f.FullName.Replace($rootPath, "")
            SizeBytes     = $f.Length
            SizeFormatted = Format-FileSize $f.Length
            SHA256        = Get-FileSHA256 $f.FullName
            Extension     = $f.Extension.ToLower()
            LastModified  = $f.LastWriteTime.ToString("o")
        }
    }

    $totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
    if (-not $totalSize) { $totalSize = 0 }

    return @{
        Files     = @($inventory)
        TotalSize = $totalSize
        FileCount = $allFiles.Count
        DirCount  = $allDirs.Count
    }
}


function Get-BuildHistory {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    try {
        $obj = Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($obj -is [System.Array]) { return $obj }
        elseif ($obj.PSObject.Properties["History"]) { return @($obj.History) }
        else { return @($obj) }
    } catch { return @() }
}

function Write-BuildSummary {
    Write-Title "BUILD SUMMARY"

    $passed = ($script:Checks | Where-Object {  $_.Passed }).Count
    $failed = ($script:Checks | Where-Object { -not $_.Passed }).Count
    $total  = $script:Checks.Count

    foreach ($c in $script:Checks) {
        $icon   = if ($c.Passed) { "[✓]" } else { "[✗]" }
        $color  = if ($c.Passed) { $ColorSuccess } else { $ColorError }
        $label  = $c.Label.PadRight(40)
        $detail = if ($c.Detail) { "  ->  $($c.Detail)" } else { "" }
        Write-Host "  $icon  $label$detail" -ForegroundColor $color
    }

    Write-Host ""
    Write-Host "  $("─" * 60)" -ForegroundColor $ColorDim

    if ($failed -eq 0) {
        Write-Host "  All $total checks passed." -ForegroundColor $ColorSuccess
    } else {
        Write-Host "  $passed / $total checks passed   |   $failed failed." -ForegroundColor $ColorWarning
    }
    Write-Host ""
}

$BuildStart = Get-Date
$SysInfo    = Get-SystemInfo

if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }

Write-Title "FILE CONVERTER PRO — INSTALLER BUILD"
Write-Host "  Started  : $($BuildStart.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor $ColorDim
Write-Host "  Machine  : $($SysInfo.Machine)  ($($SysInfo.User))"        -ForegroundColor $ColorDim
Write-Host "  OS       : $($SysInfo.OS)  (Build $($SysInfo.OSBuild))"    -ForegroundColor $ColorDim
Write-Host "  CPU      : $($SysInfo.CPU)  [$($SysInfo.CPUCores) logical cores]" -ForegroundColor $ColorDim
Write-Host "  RAM      : $($SysInfo.TotalRAM_GB) GB total  /  $($SysInfo.FreeRAM_GB) GB free" -ForegroundColor $ColorDim
Write-Host "  PS       : $($SysInfo.PSVersion)"                           -ForegroundColor $ColorDim
Write-Host ""

Write-Title "PREREQUISITES CHECK"

Write-Step "Checking Inno Setup..."
$isccOk = Test-Path $IsccPath
if ($isccOk) { Write-Success "Inno Setup found: $IsccPath" }
else {
    Write-ErrorMsg "ISCC.exe not found at: $IsccPath"
    Write-Warning  "Install Inno Setup from: https://jrsoftware.org/isinfo.php"
}
Add-CheckResult "Inno Setup (ISCC.exe)" $isccOk $IsccPath

Write-Step "Checking Inno Setup script..."
$issOk = Test-Path $IssFile
if ($issOk) { Write-Success "Script found: $IssFile" }
else        { Write-ErrorMsg ".iss file not found: $IssFile" }
Add-CheckResult ".iss script" $issOk $IssFile

Write-Step "Checking onedir folder..."
$onedirOk = Test-Path $DistDir
if ($onedirOk) {
    Write-Success "Onedir folder found: $DistDir"
    Add-CheckResult "Onedir folder" $true $DistDir
} else {
    Write-Warning "Onedir folder not found: $DistDir"
    Write-Warning "Run build.ps1 first to generate the onedir build."
    Add-CheckResult "Onedir folder" $false "not found — run build.ps1 first"
}

if (-not $isccOk -or -not $issOk) {
    Write-BuildSummary
    Write-ErrorMsg "Critical prerequisites missing. Aborting."
    exit 1
}

Write-Title "ISS SCRIPT ANALYSIS"
Write-Step "Parsing script metadata..."

$issContent     = Get-Content $IssFile -Raw
$appName        = if ($issContent -match '#define MyAppName "([^"]+)"')                { $matches[1] } else { "N/A" }
$appVersion     = if ($issContent -match '#define MyAppVersion "([^"]+)"')             { $matches[1] } else { "N/A" }
$appPublisher   = if ($issContent -match '#define MyAppPublisher "([^"]+)"')           { $matches[1] } else { "N/A" }
$compression    = if ($issContent -match 'Compression=([^\r\n]+)')                     { $matches[1] } else { "N/A" }
$solidComp      = if ($issContent -match 'SolidCompression=([^\r\n]+)')                { $matches[1] } else { "N/A" }
$outputBaseFile = if ($issContent -match 'OutputBaseFilename=([^\r\n]+)')              { $matches[1] } else { "N/A" }
$minVersion     = if ($issContent -match 'MinVersion=([^\r\n]+)')                      { $matches[1] } else { "N/A" }
$archMode       = if ($issContent -match 'ArchitecturesInstallIn64BitMode=([^\r\n]+)') { $matches[1] } else { "N/A" }

Write-Host "  Application      : $appName"        -ForegroundColor $ColorInfo
Write-Host "  Version          : $appVersion"     -ForegroundColor $ColorInfo
Write-Host "  Publisher        : $appPublisher"   -ForegroundColor $ColorInfo
Write-Host "  Output filename  : $outputBaseFile" -ForegroundColor $ColorDim
Write-Host "  Min Windows ver  : $minVersion"     -ForegroundColor $ColorDim
Write-Host "  Architecture     : $archMode"       -ForegroundColor $ColorDim
Write-Host "  Compression      : $compression"    -ForegroundColor $ColorWarning
Write-Host "  Solid Compress   : $solidComp"      -ForegroundColor $ColorWarning

Write-Title "DIST FOLDER ANALYSIS"
Write-Step "Scanning $DistDir\ ..."

$DistInventory = Get-DistInventory $DistDir

Write-Host "  Files found    : $($DistInventory.FileCount)" -ForegroundColor $ColorInfo
Write-Host "  Directories    : $($DistInventory.DirCount)"  -ForegroundColor $ColorInfo
Write-Host "  Total size     : $(Format-FileSize $DistInventory.TotalSize)" -ForegroundColor $ColorHighlight
Write-Host ""

$top10 = $DistInventory.Files | Sort-Object SizeBytes -Descending | Select-Object -First 10
if ($top10) {
    Write-Host "  Top 10 largest files:" -ForegroundColor $ColorHighlight
    foreach ($f in $top10) {
        $rel = if ($f.RelativePath.Length -gt 55) { $f.RelativePath.Substring(0,52)+"..." } else { $f.RelativePath }
        Write-Host "    $($rel.PadRight(56))  $($f.SizeFormatted)" -ForegroundColor $ColorDim
    }
    Write-Host ""
}

$byExt = $DistInventory.Files |
         Group-Object Extension |
         Sort-Object { ($_.Group | Measure-Object SizeBytes -Sum).Sum } -Descending |
         Select-Object -First 8

if ($byExt) {
    Write-Host "  By extension (top 8 by size):" -ForegroundColor $ColorHighlight
    foreach ($g in $byExt) {
        $extSum   = ($g.Group | Measure-Object SizeBytes -Sum).Sum
        $extLabel = $(if ($g.Name) { $g.Name } else { "(none)" }).PadRight(10)
        Write-Host "    $extLabel  $($g.Count.ToString().PadLeft(5)) file(s)   $(Format-FileSize $extSum)" -ForegroundColor $ColorDim
    }
    Write-Host ""
}

Add-CheckResult "Dist folder exists" ($DistInventory.FileCount -gt 0) `
    "$($DistInventory.FileCount) files / $(Format-FileSize $DistInventory.TotalSize)"

$DistFolderSize = $DistInventory.TotalSize

Write-Title "INSTALLER COMPILATION"
Write-Step "Cleaning output folder..."

if (Test-Path $OutputDir) {
    $oldFiles = Get-ChildItem "$OutputDir\*.exe" -ErrorAction SilentlyContinue
    if ($oldFiles) {
        Remove-Item "$OutputDir\*.exe" -ErrorAction SilentlyContinue
        Write-Host "  Removed $($oldFiles.Count) old installer(s)." -ForegroundColor $ColorDim
    } else {
        Write-Host "  Output folder already clean." -ForegroundColor $ColorDim
    }
}

Write-Host "  Script      : $IssFile"     -ForegroundColor $ColorDim
Write-Host "  Compression : $compression" -ForegroundColor $ColorWarning

$CompileStart = Get-Date

$exitCode = Invoke-WithSpinner `
    -Message   "Compiling installer with Inno Setup" `
    -IsccPath  $IsccPath `
    -IssFile   $IssFile `
    -OutputDir $OutputDir

$CompileEnd      = Get-Date
$CompileDuration = ($CompileEnd - $CompileStart).TotalSeconds

$isccErr = ""
if (Test-Path "$OutputDir\iscc_output.log") { Remove-Item "$OutputDir\iscc_output.log" -ErrorAction SilentlyContinue }
if (Test-Path "$OutputDir\iscc_error.log")  {
    $isccErr = Get-Content "$OutputDir\iscc_error.log" -Raw -ErrorAction SilentlyContinue
    Remove-Item "$OutputDir\iscc_error.log" -ErrorAction SilentlyContinue
}

$compileOk = ($exitCode -eq 0)
if ($compileOk) {
    Write-Success "Compilation finished in $("{0:N2}" -f $CompileDuration) seconds"
    Add-CheckResult "Inno Setup compilation" $true "$("{0:N2}" -f $CompileDuration)s  (exit $exitCode)"
} else {
    Write-ErrorMsg "Compilation failed with exit code: $exitCode"
    if ($isccErr) { Write-Host $isccErr -ForegroundColor Red }
    Add-CheckResult "Inno Setup compilation" $false "exit code $exitCode"
    Write-BuildSummary
    exit 1
}

Write-Title "INSTALLER ANALYSIS"

$InstallerFile = Get-ChildItem -Path $OutputDir -Filter "*.exe" |
                 Sort-Object LastWriteTime -Descending |
                 Select-Object -First 1

if (-not $InstallerFile) {
    Write-ErrorMsg "No installer found in $OutputDir after compilation."
    Add-CheckResult "Installer produced" $false "file not found in $OutputDir"
    Write-BuildSummary
    exit 1
}

$InstallerPath      = $InstallerFile.FullName
$InstallerSize      = $InstallerFile.Length
$InstallerHashShort = Get-FileSHA256Short $InstallerPath
$InstallerHashFull  = Get-FileSHA256      $InstallerPath

Write-Step "Collecting file information..."
Write-Success "Installer: $($InstallerFile.Name)"
Write-Host "  Path        : $InstallerPath"                    -ForegroundColor $ColorDim
Write-Host "  Size        : $(Format-FileSize $InstallerSize)" -ForegroundColor $ColorHighlight
Write-Host "  SHA256      : $InstallerHashFull"                -ForegroundColor $ColorDim
Write-Host "  Created     : $($InstallerFile.LastWriteTime)"   -ForegroundColor $ColorDim

if ($DistFolderSize -gt 0) {
    $overhead    = $InstallerSize - $DistFolderSize
    $diffSign    = if ($overhead -gt 0) { "+" } else { "" }
    $overheadPct = [math]::Round([Math]::Abs($overhead) / $DistFolderSize * 100, 2)
    Write-Host ""
    Write-Host "  vs. dist folder ($DistDir\) :" -ForegroundColor $ColorWarning
    Write-Host "    Dist folder : $(Format-FileSize $DistFolderSize)  ($($DistInventory.FileCount) files)"  -ForegroundColor $ColorDim
    Write-Host "    Installer   : $(Format-FileSize $InstallerSize)"                                         -ForegroundColor $ColorDim
    Write-Host "    Difference  : $diffSign$(Format-FileSize ([Math]::Abs($overhead)))  ($overheadPct%)"    -ForegroundColor $ColorDim
}

Add-CheckResult "Installer produced" $true "$(Format-FileSize $InstallerSize)"

Write-Title "FULL BUILD REPORT"

$border = "┌$("─" * 73)┐"
$tsep   = "├$("─" * 73)┤"
$bottom = "└$("─" * 73)┘"
$title  = "│$("BUILD COMPILATION RESULTS".PadLeft(49).PadRight(73))│"

$lines = @(
    "", $border, $title, $tsep,
    (Format-Blank),
    (Format-Head "APPLICATION"),
    (Format-Sep),
    (Format-Row "Name            " $appName),
    (Format-Row "Version         " $appVersion),
    (Format-Row "Publisher       " $appPublisher),
    (Format-Row "Min Windows ver " $minVersion),
    (Format-Row "Architecture    " $archMode),
    (Format-Blank),
    (Format-Head "GENERATED INSTALLER"),
    (Format-Sep),
    (Format-Row "File            " $InstallerFile.Name),
    (Format-Row "Output path     " $OutputDir),
    (Format-Row "Size            " (Format-FileSize $InstallerSize)),
    (Format-Row "SHA256          " $InstallerHashShort),
    (Format-Row "Creation date   " $InstallerFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")),
    (Format-Blank),
    (Format-Head "INNO SETUP CONFIGURATION"),
    (Format-Sep),
    (Format-Row "Algorithm       " $compression),
    (Format-Row "Solid Compress  " $solidComp),
    (Format-Row "Script used     " $IssFile),
    (Format-Blank),
    (Format-Head "DIST FOLDER STATS  (onedir)"),
    (Format-Sep),
    (Format-Row "Contents        " "$($DistInventory.FileCount) files in $DistDir\"),
    (Format-Row "Total size      " (Format-FileSize $DistInventory.TotalSize)),
    (Format-Blank)
)

if ($DistFolderSize -gt 0) {
    $overhead    = $InstallerSize - $DistFolderSize
    $diffSign    = if ($overhead -gt 0) { "+" } else { "" }
    $overheadPct = Get-CompressionRatio -OriginalSize $DistFolderSize -CompressedSize $InstallerSize
    $lines += @(
        (Format-Head "COMPARISON: INSTALLER vs. DIST FOLDER"),
        (Format-Sep),
        (Format-Row "Dist folder     " (Format-FileSize $DistFolderSize)),
        (Format-Row "Dist file count " "$($DistInventory.FileCount) files"),
        (Format-Row "Installer       " (Format-FileSize $InstallerSize)),
        (Format-Row "Difference      " "$diffSign$(Format-FileSize ([Math]::Abs($overhead)))"),
        (Format-Row "Compression ratio" $overheadPct),
        (Format-Blank)
    )
}

$lines += @(
    (Format-Head "BUILD TIMING"),
    (Format-Sep),
    (Format-Row "Duration        " ("{0:N2} seconds" -f $CompileDuration)),
    (Format-Row "Duration (min)  " ("{0:N2} minutes" -f ($CompileDuration / 60))),
    (Format-Row "Start timestamp " $CompileStart.ToString("HH:mm:ss")),
    (Format-Row "End timestamp   " $CompileEnd.ToString("HH:mm:ss")),
    (Format-Blank),
    (Format-Head "BUILD ENVIRONMENT"),
    (Format-Sep),
    (Format-Row "Machine         " $SysInfo.Machine),
    (Format-Row "OS              " "$($SysInfo.OS)  (Build $($SysInfo.OSBuild))"),
    (Format-Row "CPU             " $SysInfo.CPU),
    (Format-Row "RAM             " "$($SysInfo.TotalRAM_GB) GB total  /  $($SysInfo.FreeRAM_GB) GB free"),
    (Format-Row "PowerShell      " $SysInfo.PSVersion),
    (Format-Blank),
    $bottom, ""
)

$report = $lines -join "`n"

foreach ($line in $lines) {
    if ($line -match "^[┌├└]") {
        Write-Host $line -ForegroundColor DarkGray
    } elseif ($line -match "BUILD COMPILATION RESULTS") {
        Write-Host "│" -NoNewline -ForegroundColor DarkGray
        Write-Host $line.Substring(1, $line.Length - 2) -NoNewline -ForegroundColor Cyan
        Write-Host "│" -ForegroundColor DarkGray
    } elseif ($line -match "^│\s+(APPLICATION|GENERATED INSTALLER|INNO SETUP CONFIGURATION|DIST FOLDER STATS|COMPARISON:|BUILD TIMING|BUILD ENVIRONMENT)") {
        Write-Host "│" -NoNewline -ForegroundColor DarkGray
        Write-Host $line.Substring(1, $line.Length - 2) -NoNewline -ForegroundColor Cyan
        Write-Host "│" -ForegroundColor DarkGray
    } elseif ($line -match "^│  ─") {
        Write-Host $line -ForegroundColor DarkGray
    } elseif ($line -match "^│\s*│$" -or $line -eq "│$(" " * 73)│") {
        Write-Host $line -ForegroundColor DarkGray
    } elseif ($line -match "^│(.+):(.+)│$") {
        $inner = $line.Substring(1, $line.Length - 2)
        $colon = $inner.IndexOf(":")
        $label = $inner.Substring(0, $colon + 1)
        $value = $inner.Substring($colon + 1)
        Write-Host "│" -NoNewline -ForegroundColor DarkGray
        Write-Host $label -NoNewline -ForegroundColor Gray
        Write-Host $value -NoNewline -ForegroundColor White
        Write-Host "│" -ForegroundColor DarkGray
    } else {
        Write-Host $line -ForegroundColor DarkGray
    }
}

Write-BuildSummary

Write-Step "Saving build statistics..."

$previousSizes = [System.Collections.ArrayList]::new()
$runNumber = 1

if (Test-Path $JsonHistoryPath) {
    try {
        $existing = Get-Content $JsonHistoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $runNumber = $existing.TotalRuns + 1

        if ($existing.PSObject.Properties["SizeHistory"]) {
            foreach ($entry in $existing.SizeHistory) {
                [void]$previousSizes.Add($entry)
            }
        }

        if ($existing.PSObject.Properties["CurrentBuild"]) {
            [void]$previousSizes.Add([ordered]@{
                Run           = $existing.CurrentBuild.Run
                Timestamp     = $existing.CurrentBuild.Timestamp
                Version       = $existing.CurrentBuild.Version
                InstallerSize = $existing.CurrentBuild.InstallerSize
                DistSize      = $existing.CurrentBuild.DistSize
            })
        }
    } catch {
        Write-Warning "Could not read existing stats — starting fresh."
    }
}

$currentBuild = [ordered]@{
    Run           = $runNumber
    Timestamp     = $BuildStart.ToString("o")
    Duration_s    = [math]::Round($CompileDuration, 3)
    Version       = $appVersion

    Installer = [ordered]@{
        FileName      = $InstallerFile.Name
        Path          = $InstallerPath
        SizeBytes     = $InstallerSize
        SizeFormatted = Format-FileSize $InstallerSize
        SHA256_Full   = $InstallerHashFull
        CreationTime  = $InstallerFile.LastWriteTime.ToString("o")
    }

    DistFolder = [ordered]@{
        Path               = $DistDir
        FileCount          = $DistInventory.FileCount
        TotalSizeBytes     = $DistInventory.TotalSize
        TotalSizeFormatted = Format-FileSize $DistInventory.TotalSize
        OverheadBytes      = $InstallerSize - $DistFolderSize
        OverheadPct        = Get-CompressionRatio -OriginalSize $DistFolderSize -CompressedSize $InstallerSize
    }

    Environment = [ordered]@{
        Machine   = $SysInfo.Machine
        OS        = $SysInfo.OS
        CPU       = $SysInfo.CPU
        RAM_GB    = $SysInfo.TotalRAM_GB
        PSVersion = $SysInfo.PSVersion
    }

    InstallerSize = Format-FileSize $InstallerSize
    DistSize      = Format-FileSize $DistInventory.TotalSize
}

if ($previousSizes.Count -gt 0) {
    $lastBuild = $previousSizes[$previousSizes.Count - 1]
    $currentBuild["PreviousBuild"] = [ordered]@{
        Run           = $lastBuild.Run
        Timestamp     = $lastBuild.Timestamp
        InstallerSize = $lastBuild.InstallerSize
        DistSize      = $lastBuild.DistSize
    }
}

$jsonOutput = [ordered]@{
    LastUpdated  = (Get-Date).ToString("o")
    TotalRuns    = $runNumber
    CurrentBuild = $currentBuild
    SizeHistory  = $previousSizes.ToArray()
}

$jsonOutput | ConvertTo-Json -Depth 10 | Set-Content $JsonHistoryPath -Encoding UTF8
Write-Success "Statistics saved  ->  $JsonHistoryPath  (run #$runNumber)"

if ($previousSizes.Count -gt 0) {
    $lastBuild = $previousSizes[$previousSizes.Count - 1]
    Write-Host ""
    Write-Host "  vs. previous build (run #$($lastBuild.Run)):" -ForegroundColor $ColorHighlight
    Write-Host "     Previous installer : $($lastBuild.InstallerSize)" -ForegroundColor $ColorDim
    Write-Host "     Current  installer : $(Format-FileSize $InstallerSize)" -ForegroundColor $ColorDim
    Write-Host "     Previous dist      : $($lastBuild.DistSize)" -ForegroundColor $ColorDim
    Write-Host "     Current  dist      : $(Format-FileSize $DistInventory.TotalSize)" -ForegroundColor $ColorDim
}

Write-Host ""
Write-Host "  Installer : $InstallerPath" -ForegroundColor $ColorHighlight
Write-Host ""
Write-Host "  Stats     : $JsonHistoryPath" -ForegroundColor $ColorDim
Write-Host ""
Write-Success "BUILD COMPLETED SUCCESSFULLY!"
Write-Host ""

return [ordered]@{
    Success         = $true
    InstallerPath   = $InstallerPath
    InstallerSize   = $InstallerSize
    InstallerHash   = $InstallerHashFull
    DistFolderSize  = $DistFolderSize
    DistFileCount   = $DistInventory.FileCount
    CompileDuration = $CompileDuration
    AppName         = $appName
    AppVersion      = $appVersion
    Compression     = $compression
    DistTotalSize   = $DistInventory.TotalSize
    BuildRun        = $runNumber
}