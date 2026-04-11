# Build Script - File Converter Pro Quick Check

# UPX configuration
$UPX_PATH = "C:\....\.....\Your_path\....\upx.exe" # <-- SET THIS TO YOUR UPX PATH

# Output destination inside the onedir build
$OnedirFolder = "dist\File Converter Pro"
$SpecFile     = "quick_check.spec"
$OutputExe    = "dist\Quick Check.exe"
$DestExe      = "$OnedirFolder\Quick Check.exe"

# Colors
function Write-Success { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Fail    { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red }
function Write-Info    { param($msg) Write-Host "[ℹ] $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Title   {
    param($msg)
    Write-Host "`n$("=" * 60)" -ForegroundColor Cyan
    Write-Host "  $msg"        -ForegroundColor Cyan
    Write-Host "$("=" * 60)`n" -ForegroundColor Cyan
}

# Prerequisites

Write-Title "QUICK CHECK — BUILD"

Write-Info "Checking environment..."

# UPX
if (-not (Test-Path $UPX_PATH)) {
    Write-Fail "UPX not found at: $UPX_PATH"
    exit 1
}
Write-Success "UPX found"
$env:Path = "$([System.IO.Path]::GetDirectoryName($UPX_PATH));$env:Path"

# PyInstaller
try {
    $piv = & pyinstaller --version 2>&1
    Write-Success "PyInstaller: $piv"
} catch {
    Write-Fail "PyInstaller not installed. Run: pip install pyinstaller"
    exit 1
}

# Spec file
if (-not (Test-Path $SpecFile)) {
    Write-Fail "Spec file not found: $SpecFile"
    exit 1
}
Write-Success "Spec file found: $SpecFile"

if (-not (Test-Path $OnedirFolder)) {
    Write-Warning "Onedir folder not found: $OnedirFolder"
    Write-Warning "Quick Check.exe will be built but NOT copied automatically."
    Write-Warning "Run build.ps1 first to generate the main onedir build."
}


Write-Info "Cleaning previous build artifacts..."

$buildFolder = "build\quick_check"
if (Test-Path $buildFolder) {
    Get-ChildItem $buildFolder -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $buildFolder -ErrorAction SilentlyContinue
    if (Test-Path $buildFolder) {
        Write-Warning "build\quick_check could not be fully removed (may be locked by OneDrive/Defender)"
        Write-Warning "Try closing OneDrive sync or running as Administrator if the build fails."
    } else {
        Write-Success "build\quick_check cleaned"
    }
}
if (Test-Path $OutputExe) {
    Remove-Item -Force $OutputExe
    Write-Success "Previous exe removed"
}


Write-Info "Compiling Quick Check..."
$startTime = Get-Date

try {
    & pyinstaller --clean --noconfirm $SpecFile

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller exited with code $LASTEXITCODE"
    }
} catch {
    Write-Fail "Compilation failed: $_"
    exit 1
}

$duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
Write-Success "Compiled in $duration seconds"

if (-not (Test-Path $OutputExe)) {
    Write-Fail "Compilation produced no exe — check PyInstaller output above."
    exit 1
}

$sizeMB = [math]::Round((Get-Item $OutputExe).Length / 1MB, 2)
Write-Success "Exe created: $sizeMB MB"

if (Test-Path $OnedirFolder) {
    Copy-Item -Force $OutputExe $DestExe
    Write-Success "Deployed to: $DestExe"
} else {
    Write-Warning "Skipped copy — onedir folder not found."
    Write-Warning "Manually copy '$OutputExe' to '$OnedirFolder' when ready."
}

Remove-Item -Force $OutputExe -ErrorAction SilentlyContinue


Write-Title "BUILD COMPLETE"
Write-Info "Exe       : $OutputExe"
Write-Info "Size      : $sizeMB MB"
Write-Info "Duration  : $duration seconds"
if (Test-Path $DestExe) {
    Write-Info "Deployed  : $DestExe"
}
Write-Host ""
Write-Success "Quick Check.exe is ready!"
Write-Host ""