# Run build steps, stop on failure.

[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '')]
param()

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Run-Step {
    param(
        [string]$Label,
        [string]$Script
    )
    $path = Join-Path $ScriptDir $Script
    Write-Host ""
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Label" -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan

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

$Start = Get-Date

Run-Step "1/2  Main Build"  "build.ps1"
Run-Step "2/2  Installer"   "build_installer.ps1"

$Duration = (Get-Date) - $Start
Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Full build completed in $([math]::Round($Duration.TotalSeconds))s" -ForegroundColor Green
Write-Host "══════════════════════════════════════════" -ForegroundColor Green