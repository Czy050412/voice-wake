@echo off
title ErDan Voice Wake Service

set "PYTHON=F:\Agent\Claw\voice_wake\.venv\Scripts\python.exe"
set "DIR=%~dp0"

if not exist "%PYTHON%" (
    echo [ERROR] Python venv not found
    echo [FIX] Check path: %PYTHON%
    pause
    exit /b 1
)

"%PYTHON%" -c "import speech_recognition" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    "%PYTHON%" -m pip install SpeechRecognition pyaudio -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -q
    if errorlevel 1 (
        echo [ERROR] Install failed
        pause
        exit /b 1
    )
)

echo [INFO] ErDan Voice Wake Service starting...
echo [INFO] Make sure mic is ready and WorkBuddy is open
echo.
"%PYTHON%" "%DIR%voice_wake.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Process exited abnormally
    pause
)
