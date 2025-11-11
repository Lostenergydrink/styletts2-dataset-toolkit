# StyleTTS2 Launch Script
# This script activates the isolated virtual environment and launches the StyleTTS2 web UI
# 
# Configuration:
# - Set STYLETTS2_PATH environment variable to override default path
# - Set FFMPEG_PATH environment variable to override FFmpeg location

$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "       StyleTTS2 Web UI Launcher" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Determine StyleTTS2 installation path
# Priority: 1. Environment variable, 2. Default location, 3. Current directory
$STYLETTS2_BASE = $env:STYLETTS2_PATH
if ([string]::IsNullOrEmpty($STYLETTS2_BASE)) {
    # Try default location
    $defaultPath = "E:\AI\tts-webui\styletts2"
    if (Test-Path $defaultPath) {
        $STYLETTS2_BASE = $defaultPath
    } else {
        # Fallback to current directory (for portable installations)
        $STYLETTS2_BASE = $PSScriptRoot
        Write-Host "⚠️  Using current directory as StyleTTS2 path" -ForegroundColor Yellow
        Write-Host "   Set STYLETTS2_PATH environment variable to override" -ForegroundColor Yellow
    }
}

$VENV_PATH = Join-Path $STYLETTS2_BASE ".venv"
$SCRIPT_PATH = Join-Path $STYLETTS2_BASE "styletts2_webui.py"
$SERVER_PORT = 7860

# Check if virtual environment exists
if (-not (Test-Path "$VENV_PATH\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found at $VENV_PATH" -ForegroundColor Red
    Write-Host "Please run the installation script first." -ForegroundColor Yellow
    Write-Host "Or set STYLETTS2_PATH environment variable to point to your StyleTTS2 installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if web UI script exists
if (-not (Test-Path $SCRIPT_PATH)) {
    Write-Host "ERROR: Web UI script not found at $SCRIPT_PATH" -ForegroundColor Red
    Write-Host "Please ensure StyleTTS2 is installed correctly." -ForegroundColor Yellow
    Write-Host "Or set STYLETTS2_PATH environment variable to point to your StyleTTS2 installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "StyleTTS2 Path: $STYLETTS2_BASE" -ForegroundColor Green
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "$VENV_PATH\Scripts\Activate.ps1"

# Add FFmpeg to PATH (check multiple locations)
$ffmpegFound = $false
$ffmpegInPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegInPath) {
    Write-Host "FFmpeg found in system PATH" -ForegroundColor Green
    $ffmpegFound = $true
} else {
    # Try common locations
    $ffmpegPaths = @(
        $env:FFMPEG_PATH,
        "E:\AI\tools\ffmpeg\bin",
        "C:\ffmpeg\bin",
        "$env:ProgramFiles\ffmpeg\bin",
        "$env:ProgramFiles(x86)\ffmpeg\bin"
    )
    
    foreach ($path in $ffmpegPaths) {
        if (-not [string]::IsNullOrEmpty($path) -and (Test-Path "$path\ffmpeg.exe")) {
            $env:PATH = "$path;$env:PATH"
            Write-Host "FFmpeg found at: $path" -ForegroundColor Green
            $ffmpegFound = $true
            break
        }
    }
}

if (-not $ffmpegFound) {
    Write-Host "⚠️  FFmpeg not found. Some features may not work." -ForegroundColor Yellow
    Write-Host "   Install FFmpeg or set FFMPEG_PATH environment variable." -ForegroundColor Yellow
}

Write-Host "Starting StyleTTS2 Web UI on port $SERVER_PORT..." -ForegroundColor Green
Write-Host ""
Write-Host "Once started, the web UI will be available at:" -ForegroundColor Yellow
Write-Host "  http://localhost:$SERVER_PORT (or next available port)" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 If port $SERVER_PORT is busy, the script will try ports $($SERVER_PORT+1), $($SERVER_PORT+2), etc." -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host ""

# Change to the script directory
Set-Location $STYLETTS2_BASE

# Launch the web UI
& "$VENV_PATH\Scripts\python.exe" $SCRIPT_PATH --server_port $SERVER_PORT

Write-Host ""
Write-Host "StyleTTS2 Web UI has stopped." -ForegroundColor Yellow
