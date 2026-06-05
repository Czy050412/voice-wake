@echo off
title Input Box Calibration
echo.
echo  === WorkBuddy Input Box Calibration ===
echo  1. Make sure WorkBuddy is open
echo  2. Click on the input text box when prompted
echo  3. Position will be saved to input_pos.cfg
echo.
pause
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" calibrate.py
pause
