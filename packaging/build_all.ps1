# Run build steps, stop on failure.

[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '')]
param()

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$OutputDir = Join-Path $ProjectRoot "Output"
$DistDir = Join-Path $ProjectRoot "packaging\dist\FCP"

# Optional explicit fallback if 7-Zip is not available on PATH.
$SevenZipFallbackPath = ""

function Write-Banner {
    param(
        [string]$Text,
        [ConsoleColor]$Color = 'Cyan'
    )
    $line = ([string][char]0x2550) * 42
    Write-Host ""
    Write-Host $line -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host $line -ForegroundColor $Color
}

function Run-Step {
    param(
        [string]$Label,
        [string]$Script
    )
    $path = Join-Path $ScriptDir $Script
    Write-Banner $Label

    if (-not (Test-Path $path)) {
        Write-Host "  [ERROR] File not found: $path" -ForegroundColor Red
        exit 1
    }

    & $path
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  [FAILED] $Script returned exit code $LASTEXITCODE" -ForegroundColor Red
        Write-Host "  Pipeline stopped." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host "  [OK] $Label completed." -ForegroundColor Green
}

function Resolve-SevenZipPath {
    foreach ($name in @("7z", "7zz", "7za")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) {
            return $command.Source
        }
    }

    if ($SevenZipFallbackPath -and (Test-Path -LiteralPath $SevenZipFallbackPath -PathType Leaf)) {
        return $SevenZipFallbackPath
    }

    foreach ($candidate in @(
        (Join-Path $env:ProgramFiles "7-Zip\7z.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "7-Zip\7z.exe")
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    return $null
}

$Start = Get-Date

Run-Step "1/3  Main Build" "build.ps1"
Run-Step "2/3  Installer" "build_installer.ps1"

Write-Banner "3/3  Portable ZIP and checksums"

$IssFile = Join-Path $ScriptDir "setup.iss"
if (-not (Test-Path -LiteralPath $IssFile)) {
    Write-Host "  [ERROR] File not found: $IssFile" -ForegroundColor Red
    exit 1
}

$issContent = Get-Content -LiteralPath $IssFile -Raw
if ($issContent -notmatch '#define MyAppVersion "([^"]+)"') {
    Write-Host "  [ERROR] Could not read MyAppVersion from $IssFile" -ForegroundColor Red
    exit 1
}
$AppVersion = $matches[1]

$InstallerPath = Join-Path $OutputDir "FileConverterPro_Setup_v$AppVersion.exe"
$ZipPath = Join-Path $OutputDir "File_Converter_Pro_v$AppVersion.zip"
$ChecksumsPath = Join-Path $OutputDir "checksums.txt"

if (-not (Test-Path -LiteralPath $InstallerPath -PathType Leaf)) {
    Write-Host "  [ERROR] Installer not found: $InstallerPath" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $DistDir -PathType Container)) {
    Write-Host "  [ERROR] Onedir build not found: $DistDir" -ForegroundColor Red
    exit 1
}

$SevenZipPath = Resolve-SevenZipPath
if (-not $SevenZipPath) {
    Write-Host "  [ERROR] 7-Zip not found on PATH. Add it to PATH or set `$SevenZipFallbackPath in this script." -ForegroundColor Red
    exit 1
}

if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

Push-Location (Split-Path -Parent $DistDir)
try {
    & $SevenZipPath a -tzip $ZipPath (Split-Path -Leaf $DistDir)
    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

$checksumLines = foreach ($file in @($InstallerPath, $ZipPath)) {
    $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
    "SHA256          $hash         $([System.IO.Path]::GetFileName($file))"
}
$checksumLines | Set-Content -LiteralPath $ChecksumsPath -Encoding ascii

Write-Host "  [OK] Portable ZIP: $ZipPath" -ForegroundColor Green
Write-Host "  [OK] Checksums:    $ChecksumsPath" -ForegroundColor Green

$Duration = (Get-Date) - $Start
Write-Banner "Full build completed in $([math]::Round($Duration.TotalSeconds))s" -Color Green