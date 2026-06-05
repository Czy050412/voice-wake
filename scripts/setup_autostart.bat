@echo off
chcp 65001 >nul
title Setup Auto-Start
echo.
echo  ============================================
echo    Setup Voice Wake Auto-Start
echo    Launches in background when Windows starts
echo  ============================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SCRIPT_DIR=%~dp0.."
set "SHORTCUT=%STARTUP_DIR%\VoiceWake.lnk"

echo Creating shortcut: %SHORTCUT%
powershell -NoP -C ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
  "$s.TargetPath='%SCRIPT_DIR%\start_background.bat';" ^
  "$s.WorkingDirectory='%SCRIPT_DIR%';" ^
  "$s.WindowStyle=7;" ^
  "$s.Save()"

if exist "%SHORTCUT%" (
    echo [OK] Voice Wake will auto-start with Windows!
) else (
    echo [FAIL] Could not create shortcut
)
pause
