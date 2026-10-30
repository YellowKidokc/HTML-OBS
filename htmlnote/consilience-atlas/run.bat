@echo off
REM ============================================================
REM  Consilience Atlas Engine - start the app (Windows)
REM  Double-click this file to launch. Opens at http://127.0.0.1:8501
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Consilience Atlas at http://127.0.0.1:8501
echo (Close this window or press Ctrl+C to stop the server.)
echo.

call ".venv\Scripts\python.exe" -m streamlit run app.py ^
    --server.address 127.0.0.1 ^
    --server.port 8501 ^
    --browser.gatherUsageStats false

pause
