@echo off
REM Install mcm-math-modeling into an agent's skills directory.
REM
REM   install.bat              auto-detect and install into every agent found
REM   install.bat claude       install into Claude Code only
REM   install.bat workbuddy    install into WorkBuddy only
REM   install.bat --list       list detected agents without installing
REM
REM Copies the whole mcm-math-modeling\ folder (SKILL.md, references\, scripts\,
REM assets\, icon.png). The source directory is left untouched.
REM
REM NOTE: output is intentionally ASCII-only. cmd.exe renders non-ASCII batch
REM text as mojibake unless the file is UTF-8 with BOM plus a codepage switch,
REM which still breaks on many setups.
REM
REM NOTE: variable indirection is avoided on purpose. `call set` and `for /f`
REM over `set` both misbehave here (the latter trips the "access denied"
REM on the internal SET command), so each agent is handled by an explicit branch.

setlocal EnableDelayedExpansion

set "SKILL_NAME=mcm-math-modeling"
set "SRC_DIR=%~dp0"
if "%SRC_DIR:~-1%"=="\" set "SRC_DIR=%SRC_DIR:~0,-1%"

if not exist "%SRC_DIR%\SKILL.md" (
    echo ERROR: SKILL.md not found in "%SRC_DIR%".
    echo Run this script from inside the skill package folder.
    exit /b 1
)

set "TARGETS="

if "%~1"=="--list" goto :list
if "%~1"=="-l" goto :list

if "%~1"=="" goto :probe
if "%~1"=="claude"            set "TARGETS=claude"            & goto :install
if "%~1"=="workbuddy"         set "TARGETS=workbuddy"         & goto :install
if "%~1"=="workbuddy_intl"    set "TARGETS=workbuddy_intl"    & goto :install
if "%~1"=="codex"             set "TARGETS=codex"             & goto :install
if "%~1"=="cursor"            set "TARGETS=cursor"            & goto :install
if "%~1"=="gemini"            set "TARGETS=gemini"            & goto :install
if "%~1"=="opencode"          set "TARGETS=opencode"          & goto :install
if "%~1"=="windsurf"          set "TARGETS=windsurf"          & goto :install

echo Unknown agent: %~1
echo Options: claude workbuddy workbuddy_intl codex cursor gemini opencode windsurf
exit /b 1

:probe
if exist "%USERPROFILE%\.claude\skills"           set "TARGETS=!TARGETS! claude"
if exist "%USERPROFILE%\.workbuddy\skills"        set "TARGETS=!TARGETS! workbuddy"
if exist "%USERPROFILE%\.workbuddy-intl\skills"   set "TARGETS=!TARGETS! workbuddy_intl"
if exist "%USERPROFILE%\.codex\skills"            set "TARGETS=!TARGETS! codex"
if exist "%USERPROFILE%\.cursor\skills"           set "TARGETS=!TARGETS! cursor"
if exist "%USERPROFILE%\.gemini\skills"           set "TARGETS=!TARGETS! gemini"
if exist "%USERPROFILE%\.config\opencode\skills"  set "TARGETS=!TARGETS! opencode"
if exist "%USERPROFILE%\.windsurf\skills"         set "TARGETS=!TARGETS! windsurf"
if "!TARGETS!"=="" (
    echo No agent skills directory detected.
    echo Copy this folder manually, or see the README install section.
    exit /b 1
)

:install
echo Installing %SKILL_NAME% ...
for %%T in (%TARGETS%) do call :install_one %%T

echo.
echo Optional dependencies (only for plotting and solver templates):
echo    python -m pip install -r requirements.txt
echo.
echo Note: verify_checkpoint.py needs only the Python standard library.
echo       The document workflow (read - model - write - verify) runs without extras.
goto :eof

:install_one
set "agent=%~1"
if "%agent%"=="claude"         set "target_root=%USERPROFILE%\.claude\skills"
if "%agent%"=="workbuddy"      set "target_root=%USERPROFILE%\.workbuddy\skills"
if "%agent%"=="workbuddy_intl" set "target_root=%USERPROFILE%\.workbuddy-intl\skills"
if "%agent%"=="codex"          set "target_root=%USERPROFILE%\.codex\skills"
if "%agent%"=="cursor"         set "target_root=%USERPROFILE%\.cursor\skills"
if "%agent%"=="gemini"         set "target_root=%USERPROFILE%\.gemini\skills"
if "%agent%"=="opencode"       set "target_root=%USERPROFILE%\.config\opencode\skills"
if "%agent%"=="windsurf"       set "target_root=%USERPROFILE%\.windsurf\skills"

set "target=%target_root%\%SKILL_NAME%"
if not exist "%target_root%" mkdir "%target_root%" 2>nul
if exist "%target%" (
    echo   - replacing existing copy: %target%
    rmdir /s /q "%target%"
)
xcopy "%SRC_DIR%" "%target%" /E /I /Q /Y >nul
if errorlevel 1 (
    echo   x FAILED to copy to %target%
) else (
    echo   + installed to %target%
)
goto :eof

:list
echo Detected agents:
if exist "%USERPROFILE%\.claude\skills"           echo    * claude           %USERPROFILE%\.claude\skills
if exist "%USERPROFILE%\.workbuddy\skills"        echo    * workbuddy        %USERPROFILE%\.workbuddy\skills
if exist "%USERPROFILE%\.workbuddy-intl\skills"   echo    * workbuddy_intl   %USERPROFILE%\.workbuddy-intl\skills
if exist "%USERPROFILE%\.codex\skills"            echo    * codex            %USERPROFILE%\.codex\skills
if exist "%USERPROFILE%\.cursor\skills"           echo    * cursor           %USERPROFILE%\.cursor\skills
if exist "%USERPROFILE%\.gemini\skills"           echo    * gemini           %USERPROFILE%\.gemini\skills
if exist "%USERPROFILE%\.config\opencode\skills"  echo    * opencode         %USERPROFILE%\.config\opencode\skills
if exist "%USERPROFILE%\.windsurf\skills"         echo    * windsurf         %USERPROFILE%\.windsurf\skills
goto :eof
