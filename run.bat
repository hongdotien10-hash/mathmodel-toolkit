@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ================================================
echo   MathModel Toolkit
echo ================================================
echo.

:: Find Python
set PYTHON=
for %%p in (python python3 py) do (
    where %%p >nul 2>&1
    if !errorlevel!==0 (
        set PYTHON=%%p
        goto :found
    )
)

:: Try common install locations
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%PROGRAMFILES%\Python313\python.exe"
    "%PROGRAMFILES%\Python312\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
) do (
    if exist %%d (
        set PYTHON=%%d
        goto :found
    )
)

echo [ERROR] Python not found!
echo Please run install.bat first to install Python.
echo.
pause
exit /b 1

:found
echo Python: %PYTHON%
echo.

:: Check if dependencies are installed
%PYTHON% -c "import numpy" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Dependencies not installed. Running install.bat...
    call "%~dp0install.bat"
)

:: Check if API key is configured
%PYTHON% -c "from api.config import APIConfig; c=APIConfig(); exit(0 if c.is_configured else 1)" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ================================================
    echo   [INFO] No API key configured
    echo ================================================
    echo.
    echo Without API key, the toolkit uses local rules.
    echo With AI ^(DeepSeek^), paper quality is much better.
    echo Cost: ~0.5-1 RMB ^(Free^) or ~3-5 RMB ^(Pro^).
    echo.
    set /p setup_api="Configure API key now? (y/n, default y): "
    if "%setup_api%"=="" set setup_api=y
    if /i "%setup_api%"=="y" (
        call "%~dp0setup_api.bat"
    ) else (
        echo.
        echo Skipping API setup. Run setup_api.bat later to configure.
        echo Continuing with local rules...
    )
)

echo Running MathModel Toolkit...
echo.
%PYTHON% start.py

echo.
echo ================================================
echo   Done! Check output/ folder for paper.
echo ================================================
pause
