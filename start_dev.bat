@echo off
title SlideAlert Developer Workspace Launcher
echo ===================================================
echo Starting SlideAlert Full-Stack Development Services
echo ===================================================
echo.

set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

echo [1/2] Launching SlideAlert Backend (Django REST Framework)...
start "SlideAlert Backend" cmd /k "title SlideAlert Backend && .venv\Scripts\python.exe backend\manage.py runserver"

echo [2/2] Launching SlideAlert Frontend (Vite + React)...
start "SlideAlert Frontend" cmd /k "title SlideAlert Frontend && cd /d frontend && npm run dev"

echo.
echo ===================================================
echo Services launched successfully in separate windows!
echo - Backend API: http://127.0.0.1:8000/
echo - Frontend Dashboard: http://localhost:5173/
echo.
echo Close individual windows to stop the servers.
echo ===================================================
pause
