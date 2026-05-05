@echo off
setlocal

if exist ".env.xunke" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env.xunke") do (
    if not "%%A"=="" (
      set "%%A=%%B"
    )
  )
)

if "%API_PORT%"=="" set API_PORT=8090

echo Starting XunKe bridge on port %API_PORT% ...
uvicorn xunke_bridge:app --host 0.0.0.0 --port %API_PORT%

