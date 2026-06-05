@echo off
title ErDan Background Service

set "PYTHONW=F:\Agent\Claw\voice_wake\.venv\Scripts\pythonw.exe"
set "PYTHON=F:\Agent\Claw\voice_wake\.venv\Scripts\python.exe"
set "DIR=%~dp0"

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found
    pause
    exit /b 1
)

"%PYTHON%" -c "import speech_recognition" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    "%PYTHON%" -m pip install SpeechRecognition pyaudio -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -q
)

echo [INFO] Voice Overlay starting...
start "" /min "%PYTHONW%" "%DIR%voice_overlay.py"

echo [INFO] Voice Wake Service starting (background)...
start "" /min "%PYTHONW%" "%DIR%voice_wake.py"

timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo   ErDan is running!
echo   - Overlay: screen top-right
echo   - Service: background
echo.
echo   To stop: Task Manager - end pythonw.exe
echo ============================================
echo.
pause
