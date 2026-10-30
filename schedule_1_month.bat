@echo off
title 1-Month (30 Days x 10 Reels) Facebook Advance Scheduler
cd /d "%~dp0"

echo ======================================================================
echo    FLAG LINE BATTLE - 1-MONTH ADVANCE FACEBOOK REELS SCHEDULER
echo ======================================================================
echo.
echo This script will generate and schedule 300 Flag Battle videos:
echo  - 10 distinct 1080x1920 60FPS videos per day
echo  - Scheduled across the next 30 days on "Daily Flag Battles"
echo  - Automatic resume: you can close and resume anytime!
echo  - Local auto-cleanup: keeps your hard drive clean.
echo.

python schedule_1_month.py --days 30 --per-day 10

echo.
echo ======================================================================
echo All 300 Reels processed! Your entire next month is locked in Meta!
echo ======================================================================
pause