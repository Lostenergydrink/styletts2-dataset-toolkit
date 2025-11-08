@echo off
REM Stem Separation Launcher

echo ========================================
echo Stem Separation Web Interface
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo.
    echo Please run install_stem_separation.bat first.
    pause
    exit /b 1
)

REM Activate local virtual environment
call venv\Scripts\activate.bat

REM Add FFmpeg to PATH
set PATH=E:\AI\tools\ffmpeg\bin;%PATH%

REM Force all caches to E drive to avoid filling C drive
set PIP_CACHE_DIR=E:\AI\.cache\pip
set HF_HOME=E:\AI\.cache\huggingface
set TORCH_HOME=E:\AI\.cache\torch
set XDG_CACHE_HOME=E:\AI\.cache

echo Starting Stem Separation Web Interface...
echo Web interface will open at: http://127.0.0.1:7861
echo.
echo Press Ctrl+C to stop the server
echo.

python stem_separation_webui.py

if errorlevel 1 (
    echo.
    echo An error occurred. Check the output above.
    pause
)
