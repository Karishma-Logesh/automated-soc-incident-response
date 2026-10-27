@echo off
title SOC Incident Response Platform v2.0
echo ================================================================
echo   Automated SOC Incident Response + DFIR Platform
echo   KCG College of Technology ^| Karishma L ^| B.E. CSE (CS)
echo ================================================================
cd /d "%~dp0"

REM Load .env file if it exists
if exist ".env" (
    echo [*] Loading environment from .env
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" (
            set "%%A=%%B"
        )
    )
)

REM Find Python
where py >nul 2>&1
if %errorlevel% equ 0 ( set PY_CMD=py & goto :FOUND )

where python >nul 2>&1
if %errorlevel% equ 0 ( set PY_CMD=python & goto :FOUND )

if exist ".venv\Scripts\python.exe" ( set PY_CMD=.venv\Scripts\python.exe & goto :FOUND )

echo [!] Python not found. Install Python 3.10+ and try again.
pause & exit /b 1

:FOUND
echo [*] Python: %PY_CMD%
echo [*] Starting SOC Dashboard on http://localhost:8000
echo [*] SQLite DB will be initialised on first run
echo [*] Press Ctrl+C to stop
echo ================================================================
%PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
