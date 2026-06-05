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

start "" /min "%PYTHONW%" "%DIR%voice_wake.py"

timeout /t 1 /nobreak >nul

tasklist /fi "imagename eq pythonw.exe" 2>nul | find "pythonw.exe" >nul
if errorlevel 1 (
    echo [ERROR] Start failed. Use start.bat to check details.
    pause
    exit /b 1
)

echo ErDan is running in background. You can close this window safely.
echo To stop: end pythonw.exe in Task Manager
echo.
echo TTS feedback file: %DIR%tts.txt
echo.
pause
