@echo off
chcp 65001 >nul

echo.
echo ================================================
echo     DIF 快速部署 (静默模式)
echo ================================================
echo.

:: 快速部署：不显示详细日志，适合熟练用户
echo [部署中] 请稍候...

:: 安装后端依赖
cd /d %~dp0backend
pip install -r requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1

:: 安装前端依赖
cd /d %~dp0frontend
call npm install --silent --registry=https://registry.npmmirror.com >nul 2>&1

:: 清理旧进程
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo.
echo [✓] 部署完成！
echo.
echo 运行 start.bat 启动服务
echo.
pause
