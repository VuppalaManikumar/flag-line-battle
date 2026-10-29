@echo off
title Flag Line Battle - Video Generator
cd /d "%~dp0"
echo Generating Flag Line Battle video (1080x1920 HD, 60fps)...
python generate_battle.py
echo.
echo Video generated in output/ folder!
pause
