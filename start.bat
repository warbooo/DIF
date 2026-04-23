@echo off
REM ================================================
REM     DIF Document Intelligence Fix System
REM     Start Script
REM ================================================
echo.
echo ================================================
echo     DIF Document Intelligence Fix System
echo     Start Script
echo ================================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    echo.
    echo Press Enter to exit...
    set /p dummy=
    exit /b 1
)
echo OK Python environment ready

echo.
echo [2/4] Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+
    echo.
    echo Press Enter to exit...
    set /p dummy=
    exit /b 1
)
echo OK Node.js environment ready

echo.
echo [3/4] Stopping old processes...
echo [INFO] Cleaning up existing processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul
echo OK Old processes stopped

echo.
echo [4/4] Starting services...
echo.
echo ^+---------------------------------------------^+
echo ^|  Backend:  http://localhost:8000           ^|
echo ^|  Frontend: http://localhost:5173           ^|
echo ^|                                            ^|
echo ^|  Services run in separate windows          ^|
echo ^|  Close this window after services start    ^|
echo ^+---------------------------------------------^+
echo.

:: Start backend in new window
echo Starting backend service...
cd /d %~dp0backend
start "DIF Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

:: Start frontend in new window
echo Starting frontend service...
cd /d %~dp0frontend
start "DIF Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ================================================
echo     Services started successfully!
echo ================================================
echo.
echo     Access URLs:
echo       Backend API:  http://localhost:8000
echo       Frontend UI:  http://localhost:5173
echo       API Docs:     http://localhost:8000/docs
echo.
echo     Tips:
echo       - Services run in separate windows
echo       - Close this window to exit
echo       - Run stop.bat to stop all services
echo ================================================
echo.
echo You can close this window now.
echo.

:: Keep this window open
:loop
timeout /t 10 /nobreak >nul
goto loop
