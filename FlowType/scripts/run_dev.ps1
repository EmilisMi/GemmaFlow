# FlowType — Dev Launcher
# Run this from the FlowType root directory to start the app in development mode.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host ""
Write-Host "  ◉ FlowType — Dev Mode" -ForegroundColor Red
Write-Host "  ─────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Check Python venv
$Venv = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Venv)) {
    Write-Host "  [!] Python venv not found. Run scripts\setup.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Check node_modules
$NM = Join-Path $Root "frontend\node_modules"
if (-not (Test-Path $NM)) {
    Write-Host "  [!] node_modules missing. Run scripts\setup.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Set PYTHON_PATH so Electron knows which Python to use
$env:PYTHON_PATH = $Venv

Write-Host "  Python : $Venv" -ForegroundColor DarkGray
Write-Host "  Starting Electron..." -ForegroundColor DarkGray
Write-Host ""

Set-Location (Join-Path $Root "frontend")
npx electron . --dev
