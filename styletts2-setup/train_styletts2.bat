@echo off
REM StyleTTS2 Training Launcher
REM Launches the PowerShell training script

powershell.exe -ExecutionPolicy Bypass -File "%~dp0train_styletts2.ps1"
pause
