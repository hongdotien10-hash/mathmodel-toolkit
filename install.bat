@echo off
echo ========================================
echo   MathModel Toolkit - One-Click Install
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

:: Install dependencies
echo.
echo Installing dependencies...
pip install -e . -q
echo.

:: Install optional dependencies
echo Installing optional features (PDF, optimization)...
pip install -e ".[pdf,optimization,timeseries]" -q
echo.

:: Copy env template
if not exist .env (
    copy api\.env.example .env >nul
    echo [INFO] Created .env from template
    echo [INFO] Edit .env to add your DeepSeek API key (optional)
) else (
    echo [OK] .env already exists
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo   Usage:
echo     1. Put your problem files in problems\ folder
echo     2. Run: python start.py
echo.
echo   Optional: Edit .env to add AI analysis
echo ========================================
pause
