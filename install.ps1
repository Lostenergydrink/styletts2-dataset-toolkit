# StyleTTS2 Dataset Toolkit
# Installation script for quick setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "StyleTTS2 Dataset Toolkit - Quick Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.10 or 3.11 from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check CUDA
Write-Host "Checking NVIDIA GPU..." -ForegroundColor Yellow
try {
    $null = nvidia-smi 2>&1
    Write-Host "  GPU detected" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: nvidia-smi not found. GPU acceleration may not work." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Stem Separation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location stem-separation

# Create venv
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install PyTorch
Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Yellow
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other packages
Write-Host "Installing other dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Test
Write-Host "Testing installation..." -ForegroundColor Yellow
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

Write-Host "  Stem Separation installed!" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing StyleTTS2" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location ..\styletts2-setup

# Create venv
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv

# Activate
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install PyTorch
Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Yellow
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install StyleTTS2
Write-Host "Installing StyleTTS2 and dependencies..." -ForegroundColor Yellow
pip install styletts2
pip install gradio>=4.0.0
pip install openai-whisper
pip install pydub librosa soundfile

# Test
Write-Host "Testing installation..." -ForegroundColor Yellow
python -c "import styletts2; print('StyleTTS2 OK')"

Write-Host "  StyleTTS2 installed!" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Launch Stem Separation: " -NoNewline
Write-Host "cd stem-separation; .\launch_stem_separation.bat" -ForegroundColor Yellow
Write-Host "  2. Launch StyleTTS2: " -NoNewline
Write-Host "cd styletts2-setup; .\launch_styletts2.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation: docs\WORKFLOW_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
