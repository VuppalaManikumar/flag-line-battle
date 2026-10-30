@echo off
title Setup Windows Daily Auto-Poster Task
cd /d "%~dp0"

echo ======================================================================
echo    INSTALLING LOCAL WINDOWS DAILY AUTO-POSTER BACKUP
echo ======================================================================
echo.
echo Creating scheduled task: "FlagLineBattle_AutoPoster"...
echo It will automatically run fb_auto_poster.py every day at 08:00 AM.
echo.

schtasks /create /tn "FlagLineBattle_AutoPoster" /tr "cmd.exe /c \"cd /d %~dp0 && python fb_auto_poster.py --count 10\"" /sc daily /st 08:00 /f

echo.
if %errorlevel% equ 0 (
    echo [SUCCESS] Windows Task Scheduler registered successfully!
    echo Even if GitHub is ever offline, your local computer will post 10 reels.
) else (
    echo [NOTE] Could not register schtasks (might require admin rights). GitHub cloud automation handles it.
)
echo.
pause