@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr /i "PID"') do (
    >nul 2>&1 wmic process where "ProcessId=%%p and CommandLine like '%%voice_overlay%%'" call terminate
    >nul 2>&1 wmic process where "ProcessId=%%p and CommandLine like '%%voice_wake%%'" call terminate
    >nul 2>&1 wmic process where "ProcessId=%%p and CommandLine like '%%voice_wake%%' and Name='pythonw.exe'" call terminate
)
del /f overlay.lock 2>nul
echo Voice Wake 已停止。
timeout /t 2 >nul
