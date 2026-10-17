@echo off
setlocal
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m unittest discover -s tests -v
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m unittest discover -s tests -v
    exit /b %ERRORLEVEL%
)

echo [ERROR] Python 3 was not found. Install Python 3 and add it to PATH.
exit /b 1
