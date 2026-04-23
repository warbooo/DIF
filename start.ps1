# DIF System Start Script

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "    DIF Document Intelligence Fix System" -ForegroundColor Green
Write-Host "    Start Script" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/4] Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check Node.js
Write-Host "[2/4] Checking Node.js environment..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js 16+ from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Node.js $nodeVersion" -ForegroundColor Green
Write-Host ""

# Stop old processes
Write-Host "[3/4] Stopping old processes..." -ForegroundColor Yellow
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Old processes stopped" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "[4/4] Starting services..." -ForegroundColor Yellow
Write-Host ""
Write-Host "+---------------------------------------------+" -ForegroundColor Cyan
Write-Host "|  Backend:  http://localhost:8000           |" -ForegroundColor White
Write-Host "|  Frontend: http://localhost:5173           |" -ForegroundColor White
Write-Host "|  Services will start in new windows...     |" -ForegroundColor White
Write-Host "+---------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# Start backend
$backendPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "backend"
Write-Host "[INFO] Starting backend service..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k", "cd /d `"$backendPath`" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

Write-Host "[INFO] Waiting for backend to start (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start frontend
$frontendPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "frontend"
Write-Host "[INFO] Starting frontend service..." -ForegroundColor Cyan
Start-Process cmd -ArgumentList "/k", "cd /d `"$frontendPath`" && npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "    [SUCCESS] Services started!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - Check the new windows for service status" -ForegroundColor White
Write-Host "  - You can close this window after services start" -ForegroundColor White
Write-Host "  - Run stop.ps1 to stop all services" -ForegroundColor White
Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this window"
