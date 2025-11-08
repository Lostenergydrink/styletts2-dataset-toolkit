# StyleTTS2 Launch Script
# This script activates the isolated virtual environment and launches the StyleTTS2 web UI

$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "       StyleTTS2 Web UI Launcher" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Set paths
$VENV_PATH = "E:\AI\tts-webui\styletts2\.venv"
$SCRIPT_PATH = "E:\AI\tts-webui\styletts2\styletts2_webui.py"
$SERVER_PORT = 7860

# Check if virtual environment exists
if (-not (Test-Path "$VENV_PATH\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found at $VENV_PATH" -ForegroundColor Red
    Write-Host "Please run the installation script first." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if web UI script exists
if (-not (Test-Path $SCRIPT_PATH)) {
    Write-Host "ERROR: Web UI script not found at $SCRIPT_PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& "$VENV_PATH\Scripts\Activate.ps1"

# Add FFmpeg to PATH
$env:PATH = "E:\AI\tools\ffmpeg\bin;$env:PATH"
Write-Host "FFmpeg added to PATH" -ForegroundColor Green

Write-Host "Starting StyleTTS2 Web UI on port $SERVER_PORT..." -ForegroundColor Green
Write-Host ""
Write-Host "Once started, the web UI will be available at:" -ForegroundColor Yellow
Write-Host "  http://localhost:$SERVER_PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host ""

# Change to the script directory
Set-Location "E:\AI\tts-webui\styletts2"

# Launch the web UI
& "$VENV_PATH\Scripts\python.exe" $SCRIPT_PATH --server_port $SERVER_PORT

Write-Host ""
Write-Host "StyleTTS2 Web UI has stopped." -ForegroundColor Yellow
