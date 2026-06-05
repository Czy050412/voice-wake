@echo off
chcp 65001 >nul
title Voice Server (faster-whisper)

echo ============================================
echo   Voice Server for UE5 Integration
echo   faster-whisper small model, port 9876
echo ============================================
echo.
.venv\Scripts\python.exe voice_server.py --port 9876
pause
