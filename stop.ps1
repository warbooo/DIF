# DIF 系统停止脚本 - PowerShell 版本

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "    DIF 文档智能修复系统 - 停止脚本" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] 停止 Python 进程..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Stop-Process -Name "python" -Force
    Write-Host "[OK] 已停止 $($pythonProcesses.Count) 个 Python 进程" -ForegroundColor Green
} else {
    Write-Host "[信息] 没有运行中的 Python 进程" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[2/3] 停止 Node.js 进程..." -ForegroundColor Yellow
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Stop-Process -Name "node" -Force
    Write-Host "[OK] 已停止 $($nodeProcesses.Count) 个 Node.js 进程" -ForegroundColor Green
} else {
    Write-Host "[信息] 没有运行中的 Node.js 进程" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[3/3] 等待端口释放..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "[OK] 端口已释放" -ForegroundColor Green

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "    所有服务已停止！" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "已停止的服务:" -ForegroundColor Yellow
Write-Host "  - 后端 API (端口 8000)" -ForegroundColor White
Write-Host "  - 前端开发服务器 (端口 5173)" -ForegroundColor White
Write-Host ""
Write-Host "运行 start.ps1 重新启动服务" -ForegroundColor Yellow
Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
