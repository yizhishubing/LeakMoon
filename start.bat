@echo off
chcp 65001 >nul
echo ============================================
echo   校园网站敏感信息泄露巡检平台 - 一键启动
echo ============================================
echo.

cd /d "%~dp0backend"
echo [1/3] 启动后端服务...
start "LeakMoon Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0"
timeout /t 3 /nobreak >nul

cd /d "%~dp0frontend"
echo [2/3] 启动前端服务...
start "LeakMoon Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo [3/3] 启动完成！
echo.
echo 前端地址: http://localhost:5173
echo 后端API:  http://localhost:8000/api/health
echo API文档:  http://localhost:8000/docs
echo.
echo 提示: 如果8000端口被占用，后端会自动寻找下一个空闲端口
echo       请查看后端窗口的输出确认实际端口
echo.
pause
