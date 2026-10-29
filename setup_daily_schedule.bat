@echo off
title Setup Windows Daily Task - Flag Battle Auto Poster
cd /d "%~dp0"

echo ======================================================================
echo    SCHEDULE AUTOMATIC DAILY FACEBOOK POSTS (WINDOWS TASK SCHEDULER)
echo ======================================================================
echo.
echo This will schedule Windows to automatically run the Flag Battle generator
echo and post 3 videos to your Facebook Page every day at 8:00 AM on autopilot!
echo.
set /p confirm="Do you want to enable this daily scheduled task? (Y/N): "
if /i not "%confirm%"=="Y" goto end

set SCRIPT_PATH=%~dp0auto_post_to_facebook.bat

schtasks /create /tn "FlagBattleFacebookDailyPoster" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 08:00 /f

echo.
echo Task successfully created! It will run automatically every day at 8:00 AM.
echo To remove it later, run: schtasks /delete /tn "FlagBattleFacebookDailyPoster" /f
echo.
:end
pause
