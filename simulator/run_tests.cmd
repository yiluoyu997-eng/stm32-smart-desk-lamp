@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"

py -3 --version >nul 2>nul
if not errorlevel 1 (
    py -3 -m unittest discover -s tests -v
    exit /b !ERRORLEVEL!
)

python --version >nul 2>nul
if not errorlevel 1 (
    python -m unittest discover -s tests -v
    exit /b !ERRORLEVEL!
)

echo [ERROR] Python 3 was not found. Install Python 3 and add it to PATH.
exit /b 1
