@echo off
echo ============================================
echo   LeakMoon - Campus Website Leak Inspection Platform
echo ============================================
echo.

cd /d "%~dp0backend"
echo [1/3] Starting backend service...
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0"
timeout /t 3 /nobreak >nul

cd /d "%~dp0frontend"
echo [2/3] Starting frontend service...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo [3/3] Done!
echo.
echo Frontend:   http://localhost:5173
echo Backend:    http://localhost:8000/api/health
echo API Docs:   http://localhost:8000/docs
echo.
echo Note: If port 8000 is occupied, backend will auto-find next available port.
echo.
pause
