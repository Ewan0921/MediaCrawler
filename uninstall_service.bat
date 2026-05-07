@echo off
chcp 65001 >nul 2>nul
setlocal enabledelayedexpansion

echo ============================================================
echo   XunKe MediaCrawler Bridge - Service Uninstall
echo ============================================================
echo.

REM -- Check admin --
net session >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Please run this script as Administrator!
    echo         Right-click and select "Run as administrator".
    echo.
    goto :pause_exit
)

set ROOT=%~dp0
set SVC_NAME=XunKeMediaCrawlerBridge

REM -- Check if service exists --
sc query %SVC_NAME% >nul 2>nul
if errorlevel 1 (
    echo [INFO] Service %SVC_NAME% does not exist or is already removed.
    echo.
    goto :pause_exit
)
echo [OK] Found service: %SVC_NAME%

REM -- Confirm --
echo.
set /p CONFIRM=Uninstall service %SVC_NAME%? (Y/N): 
if /i not "!CONFIRM!"=="Y" (
    echo.
    echo [CANCEL] Operation cancelled.
    echo.
    goto :pause_exit
)

REM -- Find NSSM --
set "NSSM_EXE="
if exist "%ROOT%nssm.exe" (
    set "NSSM_EXE=%ROOT%nssm.exe"
) else (
    where nssm >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] nssm.exe not found. Place it in current dir or PATH.
        echo.
        goto :pause_exit
    )
    set "NSSM_EXE=nssm"
)

REM -- Stop service --
echo.
echo [INFO] Stopping service...
"!NSSM_EXE!" stop %SVC_NAME% >nul 2>nul
timeout /t 2 /nobreak >nul
echo [OK] Service stopped

REM -- Remove service --
echo [INFO] Removing service...
"!NSSM_EXE!" remove %SVC_NAME% confirm
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to remove. Run manually: nssm remove %SVC_NAME% confirm
    echo.
    goto :pause_exit
)

echo.
echo ============================================================
echo   [SUCCESS] Service %SVC_NAME% has been uninstalled!
echo ============================================================

:pause_exit
echo.
pause