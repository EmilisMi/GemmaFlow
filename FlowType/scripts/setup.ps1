# FlowType — One-Command Setup
# Run once after cloning to install all dependencies.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host ""
Write-Host "  O FlowType Setup" -ForegroundColor Red
Write-Host "  ---------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Check Python ──────────────────────────────────────────────────
Write-Host "  [1/4] Checking Python..." -ForegroundColor Cyan
$PythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 10) {
                $PythonCmd = $cmd
                Write-Host "        Found: $ver" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "  [!] Python 3.10+ not found. Please install from https://python.org" -ForegroundColor Red
    exit 1
}

# ── 2. Create venv + install Python deps ────────────────────────────
Write-Host "  [2/4] Setting up Python environment..." -ForegroundColor Cyan
$BackendDir = Join-Path $Root "backend"
$VenvDir    = Join-Path $BackendDir ".venv"

if (-not (Test-Path $VenvDir)) {
    & $PythonCmd -m venv $VenvDir
    Write-Host "        Created venv: $VenvDir" -ForegroundColor Green
} else {
    Write-Host "        Venv already exists, skipping." -ForegroundColor DarkGray
}

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PyExe  = Join-Path $VenvDir "Scripts\python.exe"

& $PipExe install --upgrade pip --quiet
& $PipExe install -r (Join-Path $BackendDir "requirements.txt")
Write-Host "        Python deps installed." -ForegroundColor Green

# ── 3. Install Node deps ─────────────────────────────────────────────
Write-Host "  [3/4] Installing Node.js dependencies..." -ForegroundColor Cyan
$FrontendDir = Join-Path $Root "frontend"
Push-Location $FrontendDir
npm install
Pop-Location
Write-Host "        Node deps installed." -ForegroundColor Green

# ── 4. Generate tray icons ───────────────────────────────────────────
Write-Host "  [4/4] Generating tray icons..." -ForegroundColor Cyan
$IconScript = Join-Path $Root "scripts\gen_icons.py"
& $PyExe $IconScript
Write-Host "        Icons ready." -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Run the app with:" -ForegroundColor White
Write-Host "    .\scripts\run_dev.ps1" -ForegroundColor Yellow
Write-Host ""
