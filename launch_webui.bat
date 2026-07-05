@echo off
title OpenComputer Desktop
echo Starting OpenComputer Desktop...
python "%~dp0launch_webui.py"
if errorlevel 1 (
    echo.
    echo Failed to start. Make sure Python 3.8+ is installed.
    pause
)
