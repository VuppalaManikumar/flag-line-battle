@echo off
title Facebook Auto-Poster - Flag Line Battle (10 Reels/Day)
cd /d "%~dp0"

echo ======================================================================
echo    FLAG LINE BATTLE - DAILY 10x FACEBOOK REELS AUTO-POSTER
echo ======================================================================
echo.
echo Running daily automation pipeline...
echo  - Generating 10 distinct 1080x1920 HD 60FPS Flag Battle videos
echo  - Formats viral titles, descriptions, and hashtags
echo  - Uploads and schedules them across 10 peak slots on your Facebook Page
echo.

python fb_auto_poster.py --count 10

echo.
echo ======================================================================
echo Pipeline execution finished. All 10 Reels processed!
echo ======================================================================
pause
