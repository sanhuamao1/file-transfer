@echo off
cd /d "%~dp0"

echo === Codelink Dev Server ===
echo.

if not exist .env (
    copy .env.example .env
    echo [INFO] Created .env from .env.example
)

findstr /B "STORAGE_BACKEND=" .env >nul 2>&1
if errorlevel 1 (
    echo STORAGE_BACKEND=local >> .env
    echo [INFO] Added STORAGE_BACKEND=local
)

if not exist .venv (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [INFO] Installing dependencies...
pip install -r requirements.txt -q

if not exist data mkdir data
if not exist storage mkdir storage

echo.
echo ========================================
echo  http://localhost:5000
echo  Press Ctrl+C to stop
echo ========================================
echo.

python app.py

pause