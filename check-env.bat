@echo off
chcp 65001 >nul

echo.
echo ================================================
echo     DIF 环境检查工具
echo ================================================
echo.

echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [✗] Python 未安装
) else (
    python --version
    echo [✓] Python 正常
)
echo.

echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [✗] Node.js 未安装
) else (
    node --version
    echo [✓] Node.js 正常
)
echo.

echo [3/5] 检查 pip 工具...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [✗] pip 未安装
) else (
    pip --version
    echo [✓] pip 正常
)
echo.

echo [4/5] 检查后端依赖...
cd /d %~dp0backend
if exist requirements.txt (
    echo [信息] 依赖列表：requirements.txt
) else (
    echo [✗] 未找到 requirements.txt
)
echo.

echo [5/5] 检查前端依赖...
cd /d %~dp0frontend
if exist package.json (
    echo [信息] 依赖列表：package.json
) else (
    echo [✗] 未找到 package.json
)
echo.

echo ================================================
echo     检查完成
echo ================================================
echo.
pause
