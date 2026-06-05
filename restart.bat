@echo off
cd /d F:\Agent\Claw\voice_wake
start "" /min F:\Agent\Claw\voice_wake\.venv\Scripts\pythonw.exe voice_overlay.py
sleep 2
start "" /min F:\Agent\Claw\voice_wake\.venv\Scripts\pythonw.exe voice_wake.py
