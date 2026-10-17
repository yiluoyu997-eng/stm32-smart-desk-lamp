@echo off
setlocal
cd /d "%~dp0"

if not exist "ui\smart-lamp-simulator.html" (
    echo [ERROR] ui\smart-lamp-simulator.html was not found.
    exit /b 1
)

start "" "ui\smart-lamp-simulator.html"
exit /b 0
