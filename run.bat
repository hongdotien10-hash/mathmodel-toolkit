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

:: Let user choose Free or Pro
echo Select version:
echo   [1] Free version (python start.py)
echo   [2] Pro version  (python start_pro.py)
echo.
set /p choice="Enter 1 or 2 (default 1): "
if "%choice%"=="" set choice=1
if "%choice%"=="1" (
    echo.
    echo Running Free version...
    %PYTHON% start.py
) else if "%choice%"=="2" (
    echo.
    echo Running Pro version...
    %PYTHON% start_pro.py
) else (
    echo Invalid choice. Running Free version...
    %PYTHON% start.py
)

echo.
echo ================================================
echo   Done! Check output/ folder for paper.
echo ================================================
pause
