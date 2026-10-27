@echo off
title "Automated SOC Attack Simulation - Rule 100051"
echo ========================================================
echo   Running Automated Brute Force Attack Simulation
echo ========================================================
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\simulate_bruteforce.ps1"

echo.
echo ========================================================
echo   Simulation finished! Check http://localhost:8000
echo ========================================================
pause
