@echo off
setlocal
chcp 936 >nul
cd /d "%~dp0"

echo ==========================================================
echo   Chenguang Agent Platform - local one-click start
echo   frontend: http://localhost:5174
echo   backend : http://127.0.0.1:8000/docs
echo ==========================================================
echo.

set "BACKEND_DIR=%~dp0backend"
set "PY=%BACKEND_DIR%\.venv\Scripts\python.exe"

REM ---------- 1/5 python venv ----------
if not exist "%PY%" (
  echo [1/5] creating python virtualenv ...
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] python not found. Install Python 3.12+ and add it to PATH.
    pause
    exit /b 1
  )
  python -m venv "%BACKEND_DIR%\.venv"
  if errorlevel 1 (
    echo [ERROR] failed to create virtualenv.
    pause
    exit /b 1
  )
  "%PY%" -m pip install --upgrade pip
  "%PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
) else (
  "%PY%" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo [1/5] virtualenv is broken, rebuilding ...
    rmdir /s /q "%BACKEND_DIR%\.venv"
    python -m venv "%BACKEND_DIR%\.venv"
    "%PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
  ) else (
    echo [1/5] python virtualenv OK
  )
)

REM ---------- 2/5 backend deps ----------
"%PY%" -c "import fastapi, uvicorn, sqlalchemy, aiosqlite, pydantic_settings" >nul 2>nul
if errorlevel 1 (
  echo [2/5] installing backend dependencies ...
  "%PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
) else (
  echo [2/5] backend dependencies OK
)

REM ---------- 3/5 database ----------
if not exist "%BACKEND_DIR%\rbac.db" (
  echo [3/5] creating and seeding database ...
  pushd "%BACKEND_DIR%"
  "%PY%" -m app.seed
  popd
) else (
  echo [3/5] database exists, skip seed
)

REM ---------- 4/5 frontend deps ----------
if not exist "%~dp0node_modules" (
  echo [4/5] installing frontend dependencies ...
  call npm.cmd install
) else (
  echo [4/5] frontend dependencies OK
)

REM ---------- 5/5 start services ----------
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if errorlevel 1 (
  echo [5/5] starting backend on port 8000 ...
  start "chenguang-backend" /D "%BACKEND_DIR%" "%PY%" -m uvicorn app.main:app --reload --port 8000
) else (
  echo [5/5] port 8000 already in use, skip backend
)

netstat -ano | findstr ":5174 " | findstr "LISTENING" >nul
if errorlevel 1 (
  echo [5/5] starting frontend on port 5174 ...
  start "chenguang-frontend" cmd /k npm.cmd run dev
) else (
  echo [5/5] port 5174 already in use, skip frontend
)

echo.
echo waiting for services to be ready ...
ping -n 7 127.0.0.1 >nul
start "" http://localhost:5174

echo.
echo   Frontend : http://localhost:5174
echo   Backend  : http://127.0.0.1:8000/docs
echo   Accounts : admin / ops / viewer , password 123456
echo.
echo   To stop: close the two "chenguang-*" windows.
echo.
pause
