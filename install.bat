@echo off
REM Install script for Hermes Shared Memory Skill (Windows)
REM Run this from the repo root directory

echo ============================================
echo  Hermes Shared Memory Skill - Install (Windows)
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: python is required but not found.
    echo Install Python 3 from https://python.org
    exit /b 1
)

echo [1/4] Python found
python --version

set "SKILL_DIR=%USERPROFILE%\.hermes\skills\shared-memory"
set "SCRIPT_DIR=%SKILL_DIR%\scripts"
set "DB_DIR=%USERPROFILE%\.hermes\shared-memory"

if not exist "%SCRIPT_DIR%" mkdir "%SCRIPT_DIR%"
if not exist "%DB_DIR%" mkdir "%DB_DIR%"
echo [2/4] Directories created

copy "%~dp0scripts\shared_memory.py" "%SCRIPT_DIR%\"
echo [3/4] Script copied to %SCRIPT_DIR%

if exist "%~dp0SKILL.md" (
    copy "%~dp0SKILL.md" "%SKILL_DIR%\"
    echo [3/4] SKILL.md copied
)

python "%SCRIPT_DIR%\shared_memory.py" stats >nul 2>nul
echo [4/4] Database initialized at %DB_DIR%\memory.db

echo.
echo ============================================
echo  Installation complete!
echo ============================================
echo.
echo Verify with:
echo   python "%SCRIPT_DIR%\shared_memory.py" stats
echo.
echo --- Multi-agent setup (Windows + WSL) ---
echo To share memory between Windows and WSL, both must use
echo the same database file. Set SHARED_MEMORY_DB to a shared
echo location. Example:
echo   setx SHARED_MEMORY_DB C:\Users\%USERNAME%\hermes-shared-memory\memory.db
echo.

pause
