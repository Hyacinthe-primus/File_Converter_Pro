# Build Script for File Converter Pro (onedir + UPX)

# Optional explicit fallback if UPX is not available on PATH.
$UPX_FALLBACK_PATH = ""

function Resolve-UpxPath {
    $command = Get-Command upx -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) {
        return $command.Source
    }

    if ($UPX_FALLBACK_PATH -and (Test-Path -LiteralPath $UPX_FALLBACK_PATH -PathType Leaf)) {
        return $UPX_FALLBACK_PATH
    }

    $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $wingetRoot) {
        $candidate = Get-ChildItem -LiteralPath $wingetRoot -Filter "upx.exe" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "\\UPX\.UPX_" } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate.FullName
        }
    }

    foreach ($candidate in @(
        (Join-Path $env:ProgramFiles "upx\upx.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "upx\upx.exe")
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    return $null
}

# Colors for output
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error   { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info    { param($msg) Write-Host "󰙎 $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host " $msg" -ForegroundColor Yellow }

Write-Info "Checking environment..."

$UPX_PATH = Resolve-UpxPath
if (-not $UPX_PATH) {
    Write-Error "UPX not found on PATH. Add it to PATH or set `$UPX_FALLBACK_PATH in this script."
    exit 1
}
Write-Success "UPX found: $UPX_PATH"

try {
    $pyinstallerVersion = & pyinstaller --version 2>&1
    Write-Success "PyInstaller installed: $pyinstallerVersion"
} catch {
    Write-Error "PyInstaller is not installed. Install it with: pip install pyinstaller"
    exit 1
}

if (-not (Test-Path "build.spec")) {
    Write-Error "build.spec not found in current directory"
    exit 1
}
Write-Success "Spec file found"


Write-Info "Configuring UPX for PyInstaller..."

$env:Path = "$([System.IO.Path]::GetDirectoryName($UPX_PATH));$env:Path"

try {
    $upxVersion = & $UPX_PATH --version 2>&1 | Select-Object -First 1
    Write-Success "UPX accessible: $upxVersion"
} catch {
    Write-Error "Unable to run UPX"
    exit 1
}


Write-Info "Cleaning up old builds..."

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Success "Build folder cleaned"
}

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Success "Dist folder cleaned"
}


Write-Info "Starting compilation with PyInstaller + UPX..."
Write-Info "This may take several minutes..."

$startTime = Get-Date

try {
    & pyinstaller --clean --noconfirm build.spec
    
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code: $LASTEXITCODE"
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Success "Compilation succeeded in $([math]::Round($duration.TotalMinutes, 2)) minutes"
    
} catch {
    Write-Error "Error during compilation: $_"
    exit 1
}

$parasiteExe = "dist\FCP.exe"
if (Test-Path $parasiteExe) {
    Remove-Item -Force $parasiteExe
    Write-Success "Parasite exe removed from dist\"
}

$exePath = "dist\FCP\FCP.exe"
$distFolder = "dist\FCP"

if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    
    $folderSize = [math]::Round((Get-ChildItem $distFolder -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    
    Write-Success "Executable created: $exePath"
    Write-Info "Exe size: $sizeMB MB"
    Write-Info "Total folder size: $folderSize MB"
    
    Write-Info "Running quick launch test..."
    try {
        $process = Start-Process -FilePath $exePath -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 3
        if (-not $process.HasExited) {
            $process.Kill()
            Write-Success "Executable launches correctly"
        } else {
            Write-Warning "Executable exited immediately (please check manually)"
        }
    } catch {
        Write-Warning "Automatic test failed. Please test manually."
    }
    
} else {
    Write-Error "Executable not found after compilation"
    exit 1
}

Write-Info ""
Write-Info "═══════════════════════════════════════════"
Write-Success "BUILD COMPLETE"
Write-Info "═══════════════════════════════════════════"
Write-Info "Folder: $distFolder"
Write-Info "Executable: $exePath"
Write-Info "Total size: $folderSize MB"
Write-Info ""
Write-Info "Distribution:"
Write-Warning "• Share the entire '$distFolder' folder"
Write-Warning "• Do NOT move the exe outside its folder"
Write-Info ""
Write-Success "Test the application before distributing!"
Write-Info "═══════════════════════════════════════════"