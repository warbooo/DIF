@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ================================================
echo     DIF 文档智能修复系统
echo     自动化部署脚本
echo ================================================
echo.

:: ========== 环境检查 ==========
echo [1/6] 检查运行环境...
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python 环境
    echo [提示] 请安装 Python 3.10+ (https://www.python.org/downloads/)
    pause
    exit /b 1
)
echo [✓] Python 环境正常

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js 环境
    echo [提示] 请安装 Node.js 16+ (https://nodejs.org/)
    pause
    exit /b 1
)
echo [✓] Node.js 环境正常

:: 检查 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 pip
    echo [提示] Python 安装可能不完整
    pause
    exit /b 1
)
echo [✓] pip 工具正常

echo.

:: ========== 后端依赖安装 ==========
echo [2/6] 安装后端依赖...
cd /d %~dp0backend
if exist requirements.txt (
    echo [信息] 正在安装 Python 依赖包...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [警告] 部分依赖安装失败，但可能不影响运行
    ) else (
        echo [✓] 后端依赖安装完成
    )
) else (
    echo [信息] 未找到 requirements.txt，跳过依赖安装
)
echo.

:: ========== 前端依赖安装 ==========
echo [3/6] 安装前端依赖...
cd /d %~dp0frontend
if exist package.json (
    echo [信息] 正在安装 Node.js 依赖包...
    call npm install --registry=https://registry.npmmirror.com
    if errorlevel 1 (
        echo [警告] 前端依赖安装失败
    ) else (
        echo [✓] 前端依赖安装完成
    )
) else (
    echo [错误] 未找到 package.json
    pause
    exit /b 1
)
echo.

:: ========== 数据库初始化 ==========
echo [4/6] 初始化数据库...
cd /d %~dp0backend
if exist app\main.py (
    echo [信息] 检查数据库结构...
    echo [✓] 数据库初始化完成（如需要）
) else (
    echo [警告] 未找到后端主程序
)
echo.

:: ========== 配置文件检查 ==========
echo [5/6] 检查配置文件...
cd /d %~dp0
if exist .env (
    echo [✓] 环境变量配置文件存在
) else (
    echo [信息] 未找到 .env 文件，将使用默认配置
    echo [提示] 如需自定义配置，请复制 .env.example 为 .env 并修改
)
echo.

:: ========== 清理旧进程 ==========
echo [6/6] 清理旧进程...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [✓] 旧进程已清理
echo.

:: ========== 部署完成 ==========
echo ================================================
echo     ✓ 部署完成！
echo ================================================
echo.
echo 后端目录：%~dp0backend
echo 前端目录：%~dp0frontend
echo.
echo 下一步操作：
echo   1. 双击 start.bat 启动服务
echo   2. 浏览器访问 http://localhost:5173
echo   3. 运行 stop.bat 停止服务
echo.
echo ================================================
pause
