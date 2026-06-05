@echo off
chcp 65001 >nul
title Voice Wake - One-Click Install
echo.
echo  ============================================
echo    Voice Wake - One-Click Installer
echo    Windows Voice Assistant (Offline)
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create venv
    pause
    exit /b 1
)

echo [2/4] Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com >nul 2>&1
.venv\Scripts\pip.exe install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if errorlevel 1 (
    echo [WARN] Some packages failed with mirror, retrying with direct PyPI...
    .venv\Scripts\pip.exe install -r requirements.txt
)

echo [3/4] Downloading speech model (~500MB, one-time)...
.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.whisper_cache')"
if errorlevel 1 (
    echo [WARN] Model download failed. You may need VPN for this step.
    echo Run again after connecting VPN, or manually download the model.
)

echo [4/4] Setup complete!
echo.
echo  ============================================
echo    INSTALLATION COMPLETE!
echo.
echo    Start: double-click start.bat
echo    Calibrate: double-click calibrate.bat (first time)
echo    Background: double-click start_background.bat
echo  ============================================
pause
