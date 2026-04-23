@echo off
REM ================================================
REM     DIF Document Intelligence Fix System
REM     Stop Script
REM ================================================
echo.
echo ================================================
echo     DIF Document Intelligence Fix System
echo     Stop Script
echo ================================================
echo.

echo [1/4] Stopping Python processes...
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr python.exe >nul 2>&1
if errorlevel 1 (
    echo No Python processes running
) else (
    echo Found Python processes, stopping...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 3 /nobreak >nul
    
    tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr python.exe >nul 2>&1
    if not errorlevel 1 (
        echo Warning: Some Python processes still running, forcing stop...
        taskkill /F /IM python.exe /T >nul 2>&1
        timeout /t 3 /nobreak >nul
    )
    
    tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr python.exe >nul 2>&1
    if not errorlevel 1 (
        echo ERROR: Failed to stop Python processes
    ) else (
        echo OK Python processes stopped
    )
)

echo.
echo [2/4] Stopping Node.js processes...
tasklist /FI "IMAGENAME eq node.exe" /FO TABLE | findstr node.exe >nul 2>&1
if errorlevel 1 (
    echo No Node.js processes running
) else (
    echo Found Node.js processes, stopping...
    taskkill /F /IM node.exe >nul 2>&1
    timeout /t 3 /nobreak >nul
    
    tasklist /FI "IMAGENAME eq node.exe" /FO TABLE | findstr node.exe >nul 2>&1
    if not errorlevel 1 (
        echo Warning: Some Node.js processes still running, forcing stop...
        taskkill /F /IM node.exe /T >nul 2>&1
        timeout /t 3 /nobreak >nul
    )
    
    tasklist /FI "IMAGENAME eq node.exe" /FO TABLE | findstr node.exe >nul 2>&1
    if not errorlevel 1 (
        echo ERROR: Failed to stop Node.js processes
    ) else (
        echo OK Node.js processes stopped
    )
)

echo.
echo [3/4] Waiting for ports to be released...
timeout /t 5 /nobreak >nul
echo OK Ports released

echo.
echo [4/4] Cleaning up temporary files...
if exist "e:\DIF\backend\__pycache__" (
    rd /s /q "e:\DIF\backend\__pycache__" >nul 2>&1
    echo OK Cache cleared
) else (
    echo No cache files to clean
)

echo.
echo ================================================
echo     All services stopped successfully!
echo ================================================
echo.
echo     Stopped services:
echo       - Backend API (port 8000)
echo       - Frontend dev server (port 5173)
echo       - RapidOCR subprocess
echo       - All Python and Node.js processes
echo.
echo     Run start.bat to restart services
echo ================================================
echo.
echo Press Enter to close this window...
set /p dummy=
