@echo off
REM =================================================================
REM 使用 NSSM 将 xunke_bridge.py 注册为 Windows Service。
REM 前置条件：
REM   1. 已下载 nssm.exe（https://nssm.cc/）并放入 PATH 或当前目录
REM   2. 已经 pip install -r requirements.txt 完成 Python 依赖
REM   3. 已运行过 playwright install chromium
REM =================================================================

setlocal

set SERVICE_NAME=XunKeMediaCrawlerBridge
set DISPLAY_NAME=XunKe MediaCrawler Bridge
set PYTHON_EXE=python
set SCRIPT_DIR=%~dp0
set ENTRY=%SCRIPT_DIR%xunke_bridge.py
set ENV_FILE=%SCRIPT_DIR%.env.xunke
set LOG_DIR=%SCRIPT_DIR%logs\bridge_service

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Installing NSSM service: %SERVICE_NAME%
nssm install %SERVICE_NAME% %PYTHON_EXE% "%ENTRY%"
if errorlevel 1 goto :error

nssm set %SERVICE_NAME% AppDirectory "%SCRIPT_DIR%"
nssm set %SERVICE_NAME% AppEnvironmentExtra "PYTHONUNBUFFERED=1"
nssm set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
nssm set %SERVICE_NAME% Description "MediaCrawler -> XunKe bridge FastAPI service. Auto-restart on crash."
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

REM ── 失败时自动重启策略 ──
nssm set %SERVICE_NAME% AppExit Default Restart
nssm set %SERVICE_NAME% AppRestartDelay 5000
nssm set %SERVICE_NAME% AppThrottle 1500

REM ── 日志重定向（NSSM 会按大小自动滚动）──
nssm set %SERVICE_NAME% AppStdout "%LOG_DIR%\stdout.log"
nssm set %SERVICE_NAME% AppStderr "%LOG_DIR%\stderr.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateOnline 1
nssm set %SERVICE_NAME% AppRotateBytes 10485760

echo.
echo Service registered. Starting service...
nssm start %SERVICE_NAME%

echo.
echo Done. Use the following to manage:
echo   - View status:  nssm status %SERVICE_NAME%
echo   - Stop:         nssm stop %SERVICE_NAME%
echo   - Uninstall:    nssm remove %SERVICE_NAME% confirm
goto :eof

:error
echo NSSM install failed.
exit /b 1
