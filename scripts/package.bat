@echo off
chcp 65001 >nul
title Voice Wake - Package for Distribution
echo.
echo  ============================================
echo    Packaging Voice Wake for distribution
echo  ============================================
echo.

set "PKG_DIR=%~dp0..\voice_wake_portable"
set "SRC_DIR=%~dp0.."

echo Cleaning and preparing package...
rmdir /S /Q "%PKG_DIR%" 2>nul
mkdir "%PKG_DIR%"

echo Copying files...
xcopy /E /I /Y "%SRC_DIR%\voice_wake.py" "%PKG_DIR%\"
xcopy /E /I /Y "%SRC_DIR%\commands" "%PKG_DIR%\commands\"
xcopy /E /I /Y "%SRC_DIR%\config" "%PKG_DIR%\config\"
xcopy /E /I /Y "%SRC_DIR%\scripts" "%PKG_DIR%\scripts\"
xcopy /E /I /Y "%SRC_DIR%\core" "%PKG_DIR%\core\"
copy /Y "%SRC_DIR%\start.bat" "%PKG_DIR%\"
copy /Y "%SRC_DIR%\start_background.bat" "%PKG_DIR%\"
copy /Y "%SRC_DIR%\calibrate.bat" "%PKG_DIR%\"
copy /Y "%SRC_DIR%\calibrate.py" "%PKG_DIR%\"
copy /Y "%SRC_DIR%\install.bat" "%PKG_DIR%\"
copy /Y "%SRC_DIR%\requirements.txt" "%PKG_DIR%\"

echo.
echo  ============================================
echo    Package ready: voice_wake_portable\
echo.
echo    To use: copy this folder, run install.bat
echo  ============================================
pause
