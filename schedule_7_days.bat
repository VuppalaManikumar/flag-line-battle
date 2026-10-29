@echo off
title 7-Day Facebook Auto-Scheduler (21 Reels - 3 per day)
cd /d "%~dp0"

echo ======================================================================
echo    FLAG LINE BATTLE - 7-DAY AUTOMATIC FACEBOOK REELS SCHEDULER
echo ======================================================================
echo.
echo  This tool will:
echo   1. Connect to your Facebook Page (or ask for Page ID and Token once)
echo   2. Automatically generate 21 unique 1080x1920 HD Flag Battle videos
echo   3. Format viral titles, country emojis, hooks, and hashtags
echo   4. Schedule all 21 videos across the next 7 days (3 Reels each day:
echo      Morning 10:00 AM, Afternoon 3:00 PM, Evening 8:00 PM)
echo.
echo ======================================================================
echo.

python schedule_7_days.py

echo.
echo ======================================================================
echo All 7 days (21 videos) processed!
echo ======================================================================
pause
