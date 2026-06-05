@echo off
chcp 65001 >nul 2>&1
title Voice Wake
cd /d "%~dp0"

:: Kill old instances
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr /i "PID"') do (
    >nul 2>&1 wmic process where "ProcessId=%%p and CommandLine like '%%voice_overlay%%'" call terminate
    >nul 2>&1 wmic process where "ProcessId=%%p and CommandLine like '%%voice_wake%%'" call terminate
)
timeout /t 1 >nul

:: Delete stale lock files
del /f overlay.lock 2>nul

:: Start overlay (hidden window)
start "" /min "%~dp0.venv\Scripts\pythonw.exe" "%~dp0voice_overlay.py"

:: Wait for overlay to settle
timeout /t 2 >nul

:: Start voice_wake (hidden window)
start "" /min "%~dp0.venv\Scripts\pythonw.exe" "%~dp0voice_wake.py"

echo Voice Wake 已启动！
echo 语音浮窗在第二个显示器上，说"狗蛋"唤醒。
timeout /t 3 >nul
