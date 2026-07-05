@echo off
REM OpenComputer Desktop Application Launcher (Windows)
REM Double-click this file to start the desktop app.

echo ============================================
echo   OpenComputer Desktop - Starting...
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.9+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check PyQt5
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyQt5...
    pip install PyQt5>=5.15
)

REM Check project dependencies
python -c "import dotenv" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing project dependencies...
    pip install -r requirements.txt
)

REM Launch the desktop app
python desktop_app/main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
