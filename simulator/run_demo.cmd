@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"

py -3 --version >nul 2>nul
if not errorlevel 1 (
    py -3 run_demo.py
    exit /b !ERRORLEVEL!
)

python --version >nul 2>nul
if not errorlevel 1 (
    python run_demo.py
    exit /b !ERRORLEVEL!
)

echo [ERROR] Python 3 was not found. Install Python 3 and add it to PATH.
exit /b 1
