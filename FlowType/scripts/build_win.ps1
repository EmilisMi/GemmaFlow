# FlowType — Build Script for Windows
# This script bundles the Python backend and then builds the Electron installer.

$ErrorActionPreference = "Stop"

Write-Host "`n--- Building FlowType Installer ---" -ForegroundColor Cyan

# 1. Build Python Backend
Write-Host "`n[1/3] Freezing Python backend with PyInstaller..." -ForegroundColor Yellow
cd backend

# Ensure PyInstaller is installed
& .\.venv\Scripts\pip.exe install pyinstaller

# Run PyInstaller
# --noconsole: Hide the terminal window when the backend runs
# --name main: Keep the entry point name consistent
# --collect-all: Ensure Whisper and CTranslate2 dependencies are bundled
& .\.venv\Scripts\python.exe -m PyInstaller `
    --noconsole `
    --name main `
    --collect-all faster_whisper `
    --collect-all ctranslate2 `
    --clean `
    main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

cd ..

# 2. Build Electron Frontend
Write-Host "`n[2/3] Building Electron installer..." -ForegroundColor Yellow
cd frontend

# Ensure dependencies are installed
npm install

# Run electron-builder
npm run build:win

if ($LASTEXITCODE -ne 0) {
    Write-Host "Electron build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

cd ..

Write-Host "`n--- Success! ---" -ForegroundColor Green
Write-Host "Installer is ready in: FlowType\dist" -ForegroundColor Green
