@echo off
REM ============================================================
REM  Consilience Atlas Engine - one-time setup (Windows)
REM  Double-click this file ONCE.
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo [1/4] Locating Python...
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo ERROR: Python 3.11+ was not found. Install it from python.org then re-run.
        pause
        exit /b 1
    )
)

echo [1/4] Creating virtual environment (.venv)...
if not exist ".venv" (
    %PY% -m venv .venv
    if errorlevel 1 ( echo ERROR creating venv & pause & exit /b 1 )
) else (
    echo    .venv already exists - reusing.
)

echo [2/4] Installing dependencies...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo ERROR installing dependencies & pause & exit /b 1 )

echo [3/4] Initializing database and folders...
call ".venv\Scripts\python.exe" -c "from atlas import config, database; config.ensure_dirs(); database.init_db(); print('   database ready:', config.DB_PATH)"
if errorlevel 1 ( echo ERROR initializing database & pause & exit /b 1 )

echo [4/4] Creating .env if missing...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo    Created .env  - open it to add your DEEPSEEK_API_KEY (optional).
)

echo.
echo ============================================================
echo  SETUP COMPLETE.  Now double-click  run.bat  to start.
echo ============================================================
pause
