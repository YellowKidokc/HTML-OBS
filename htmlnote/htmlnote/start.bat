@echo off
setlocal
echo Starting HTMLNote...
echo.
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%HTMLNOTE_ROOT%"
if "%TARGET%"=="" set "TARGET=%CD%"
set "PORT=%~2"
if "%PORT%"=="" set "PORT=%HTMLNOTE_PORT%"
if "%PORT%"=="" set "PORT=3377"
echo Scanning: %TARGET%
echo Port: %PORT%
echo.
node "%~dp0server.js" "%TARGET%" "%PORT%"
pause
