@echo off
title Update Facebook Token - GitHub Actions Autopilot
cd /d "%~dp0"
python update_github_secrets.py
pause