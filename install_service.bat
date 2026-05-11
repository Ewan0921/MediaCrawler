@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   XunKe MediaCrawler Bridge - Service Install
echo ============================================================
echo.

REM -- Check admin --
net session >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Please run this script as Administrator!
    echo.
    if "%~1"=="/silent" exit /b 1
    goto :pause_exit
)

set ROOT=%~dp0
set SVC_NAME=XunKeMediaCrawlerBridge
set DISPLAY_NAME=XunKe MediaCrawler Bridge

REM -- Auto-detect environment --
REM   1. runtime\python.exe exists  => Full package mode
REM   2. app\xunke_bridge.py/pyc exists => Source-only package mode
REM   3. xunke_bridge.py/pyc in root    => Dev mode

if exist "%ROOT%runtime\python.exe" (
    set "PY_EXE=%ROOT%runtime\python.exe"
    set "APP_DIR=%ROOT%app"
    echo [OK] Full package mode - embedded Python
    goto :env_done
)

if exist "%ROOT%app\xunke_bridge.py" (
    set "APP_DIR=%ROOT%app"
    echo [OK] Source-only package mode
    goto :find_system_python
)
if exist "%ROOT%app\xunke_bridge.pyc" (
    set "APP_DIR=%ROOT%app"
    echo [OK] Source-only package mode (Compiled)
    goto :find_system_python
)

if exist "%ROOT%xunke_bridge.py" (
    set "APP_DIR=%ROOT%"
    echo [OK] Dev mode
    goto :find_system_python
)
if exist "%ROOT%xunke_bridge.pyc" (
    set "APP_DIR=%ROOT%"
    echo [OK] Dev mode (Compiled)
    goto :find_system_python
)

echo [ERROR] Cannot detect environment.
echo         No runtime\python.exe, app\xunke_bridge.py, or xunke_bridge.py found.
if "%~1"=="/silent" exit /b 1
goto :pause_exit

:find_system_python
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python and add to PATH.
    echo.
    if "%~1"=="/silent" exit /b 1
    goto :pause_exit
)
for /f "delims=" %%P in ('where python') do (
    set "PY_EXE=%%P"
    goto :env_done
)

:env_done
echo     Python:  !PY_EXE!
echo     App Dir: !APP_DIR!

set "ENTRY_EXIST=0"
if exist "!APP_DIR!\xunke_bridge.py" set "ENTRY_EXIST=1"
if exist "!APP_DIR!\xunke_bridge.pyc" set "ENTRY_EXIST=1"

if "!ENTRY_EXIST!"=="0" (
    echo [ERROR] Entry script not found: !APP_DIR!\xunke_bridge.py or .pyc
    echo.
    if "%~1"=="/silent" exit /b 1
    goto :pause_exit
)
echo [OK] Entry script found

REM -- Find NSSM --
set "NSSM_EXE="
if exist "%ROOT%nssm.exe" (
    set "NSSM_EXE=%ROOT%nssm.exe"
    goto :nssm_done
)
where nssm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] nssm.exe not found. Place it in current dir or PATH.
    echo         Download: https://nssm.cc/
    echo.
    if "%~1"=="/silent" exit /b 1
    goto :pause_exit
)
set "NSSM_EXE=nssm"
:nssm_done
echo [OK] NSSM found

REM -- Load .env.xunke --
set API_PORT=8890
if exist "!APP_DIR!\.env.xunke" (
    for /f "usebackq tokens=1,* delims==" %%A in ("!APP_DIR!\.env.xunke") do (
        if not "%%A"=="" set "%%A=%%B"
    )
)
if "!API_PORT!"=="" set API_PORT=8890
echo [OK] Config loaded - port: !API_PORT!

set "LOG_DIR=%ROOT%logs\bridge_service"
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"

REM -- Remove old service if exists --
sc query %SVC_NAME% >nul 2>nul
if not errorlevel 1 (
    echo.
    echo [INFO] Existing service found, removing...
    "!NSSM_EXE!" stop %SVC_NAME% >nul 2>nul
    timeout /t 2 /nobreak >nul
    "!NSSM_EXE!" remove %SVC_NAME% confirm >nul 2>nul
    echo [OK] Old service removed
)

REM -- Install service --
echo.
echo [INFO] Registering service...
"!NSSM_EXE!" install %SVC_NAME% "!PY_EXE!" -m uvicorn xunke_bridge:app --host 0.0.0.0 --port !API_PORT!
if errorlevel 1 (
    echo.
    echo [ERROR] Service registration failed!
    echo.
    if "%~1"=="/silent" exit /b 1
    goto :pause_exit
)
echo [OK] Service registered

REM -- Configure service --
echo [INFO] Configuring service...
"!NSSM_EXE!" set %SVC_NAME% AppDirectory "!APP_DIR!"
"!NSSM_EXE!" set %SVC_NAME% DisplayName "%DISPLAY_NAME%"
"!NSSM_EXE!" set %SVC_NAME% Description "MediaCrawler XunKe Bridge FastAPI service."
"!NSSM_EXE!" set %SVC_NAME% AppEnvironmentExtra "PYTHONPATH=!APP_DIR!" "PYTHONUNBUFFERED=1"
"!NSSM_EXE!" set %SVC_NAME% Start SERVICE_AUTO_START

REM -- Restart policy --
"!NSSM_EXE!" set %SVC_NAME% AppExit Default Restart
"!NSSM_EXE!" set %SVC_NAME% AppRestartDelay 5000
"!NSSM_EXE!" set %SVC_NAME% AppThrottle 1500

REM -- Log redirection --
"!NSSM_EXE!" set %SVC_NAME% AppStdout "!LOG_DIR!\stdout.log"
"!NSSM_EXE!" set %SVC_NAME% AppStderr "!LOG_DIR!\stderr.log"
"!NSSM_EXE!" set %SVC_NAME% AppRotateFiles 1
"!NSSM_EXE!" set %SVC_NAME% AppRotateOnline 1
"!NSSM_EXE!" set %SVC_NAME% AppRotateBytes 10485760
echo [OK] Service configured

REM -- Start service --
echo.
echo [INFO] Starting service...
"!NSSM_EXE!" start %SVC_NAME%

REM -- Verify --
echo [INFO] Waiting for service to start...
set STARTED=0
for /L %%i in (1,1,5) do (
    timeout /t 3 /nobreak >nul
    sc query %SVC_NAME% | findstr /i "RUNNING" >nul 2>nul
    if not errorlevel 1 (
        set STARTED=1
        goto :check_done
    )
)
:check_done

echo.
echo ============================================================
if "!STARTED!"=="1" (
    echo   [SUCCESS] Service started!
    echo.
    echo   Service:  %SVC_NAME%
    echo   Port:     !API_PORT!
    echo   Health:   http://127.0.0.1:!API_PORT!/api/health
    echo   Logs:     !LOG_DIR!
) else (
    echo   [FAILED] Service failed to start!
    echo.
    echo   Troubleshoot:
    echo     1. Check log: !LOG_DIR!\stderr.log
    echo     2. Verify port !API_PORT! is not in use
    echo     3. Run run_bridge.bat manually to debug
)
echo ============================================================
echo.
echo   Commands:
echo     Status:   nssm status %SVC_NAME%
echo     Stop:     nssm stop %SVC_NAME%
echo     Restart:  nssm restart %SVC_NAME%
echo     Edit:     nssm edit %SVC_NAME%
echo ============================================================

:pause_exit
if "%~1"=="/silent" exit /b 0
echo.
pause
