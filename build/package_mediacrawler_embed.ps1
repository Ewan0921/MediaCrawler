param(
    [string]$PythonVersion = "3.11.9",
    [string]$PackageVersion = "",
    [string]$OutputRoot = ".\dist",
    [switch]$SkipPlaywrightInstall,
    [switch]$Clean,
    [switch]$NoPauseOnError
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command: $Name"
    }
}

function Invoke-Checked([string]$Command, [string]$ErrorMessage) {
    Write-Host "    $Command"
    cmd.exe /c $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage (exit code=$LASTEXITCODE)"
    }
}

function Pause-OnError {
    if ($NoPauseOnError) { return }
    Write-Host ""
    Write-Host "脚本执行失败。按任意键退出..." -ForegroundColor Red
    try {
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } catch {
        Start-Sleep -Seconds 3
    }
}

try {
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$buildRoot = Join-Path $repoRoot "build"
$outputRootAbs = if ([System.IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot } else { Join-Path $repoRoot $OutputRoot }
$artifactVersion = if ([string]::IsNullOrWhiteSpace($PackageVersion)) { (Get-Date -Format "yyyyMMdd-HHmmss") } else { $PackageVersion }
$artifactName = "MediaCrawler-xunke-embed-$artifactVersion"
$artifactDir = Join-Path $outputRootAbs $artifactName
$runtimeDir = Join-Path $artifactDir "runtime"
$appDir = Join-Path $artifactDir "app"
$logsDir = Join-Path $artifactDir "logs"
$tempDir = Join-Path $buildRoot "tmp-package"
$versionParts = $PythonVersion.Split(".")
if ($versionParts.Length -lt 2) { throw "Invalid PythonVersion: $PythonVersion" }
$pythonShort = "$($versionParts[0])$($versionParts[1])"
$embedZipName = "python-$PythonVersion-embed-amd64.zip"
$embedZipPath = Join-Path $tempDir $embedZipName
$embedUrl = "https://www.python.org/ftp/python/$PythonVersion/$embedZipName"
$bootstrapPipPath = Join-Path $tempDir "get-pip.py"
$wheelhouseDir = Join-Path $tempDir "wheelhouse"
$zipPath = Join-Path $outputRootAbs "$artifactName.zip"

Write-Step "Check prerequisite commands"
Ensure-Command "python"

if ($Clean) {
    Write-Step "Clean previous outputs"
    if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
    if (Test-Path $artifactDir) { Remove-Item -Path $artifactDir -Recurse -Force }
    if (Test-Path $zipPath) { Remove-Item -Path $zipPath -Force }
}

Write-Step "Prepare folders"
New-Item -ItemType Directory -Force -Path $tempDir, $outputRootAbs, $wheelhouseDir | Out-Null
if (Test-Path $artifactDir) { Remove-Item -Path $artifactDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $runtimeDir, $appDir, $logsDir | Out-Null

Write-Step "Download Python embeddable runtime"
Invoke-WebRequest -Uri $embedUrl -OutFile $embedZipPath
Expand-Archive -LiteralPath $embedZipPath -DestinationPath $runtimeDir -Force

$pthName = "python${pythonShort}._pth"
$pthPath = Join-Path $runtimeDir $pthName
if (-not (Test-Path $pthPath)) { throw "Cannot find $pthName" }
$pth = Get-Content -Path $pthPath
$pth = $pth | ForEach-Object { if ($_ -match "^\s*#\s*import site\s*$") { "import site" } else { $_ } }
if (-not ($pth -contains "import site")) { $pth += "import site" }
Set-Content -Path $pthPath -Value $pth -Encoding ascii

$pyExe = Join-Path $runtimeDir "python.exe"
if (-not (Test-Path $pyExe)) { throw "runtime python.exe not found: $pyExe" }

Write-Step "Install pip"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $bootstrapPipPath
Invoke-Checked ('"{0}" "{1}" --no-warn-script-location' -f $pyExe, $bootstrapPipPath) "Install pip failed"

Write-Step "Download and install dependencies"
Invoke-Checked ('"{0}" -m pip download setuptools wheel -d "{1}"' -f $pyExe, $wheelhouseDir) "Download build dependencies failed"
Invoke-Checked ('"{0}" -m pip download -r "{1}" -d "{2}"' -f $pyExe, (Join-Path $repoRoot "requirements.txt"), $wheelhouseDir) "Download wheels failed"
Invoke-Checked ('"{0}" -m pip install --no-index --find-links "{1}" -r "{2}"' -f $pyExe, $wheelhouseDir, (Join-Path $repoRoot "requirements.txt")) "Install dependencies failed"

if (-not $SkipPlaywrightInstall) {
    Write-Step "Install Playwright Chromium"
    Invoke-Checked ('"{0}" -m playwright install chromium' -f $pyExe) "Install Playwright failed"
}

Write-Step "Copy app files"
$appItems = @("api","cmd_arg","config","db.py","libs","media_platform","model","schema","store","tools","var.py","xunke_api","xunke_bridge.py","xunke_bridge.bat","xunke_bridge_install_service.bat","xunke_bridge_uninstall_service.bat",".env.xunke","requirements.txt","README.md")
foreach ($item in $appItems) {
    $src = Join-Path $repoRoot $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $appDir $item) -Recurse -Force
    }
}

Write-Step "Write runtime scripts"
[string[]]$runBridgeLines = @(
    "@echo off",
    "setlocal",
    "set ROOT=%~dp0",
    "set APP_DIR=%ROOT%app",
    "set PY_DIR=%ROOT%runtime",
    "if not exist ""%PY_DIR%\python.exe"" (",
    "  echo runtime\python.exe not found.",
    "  exit /b 1",
    ")",
    "cd /d ""%APP_DIR%""",
    "if exist "".env.xunke.local"" (",
    "  for /f ""usebackq tokens=1,* delims=="" %%A in ("".env.xunke.local"") do (",
    "    if not ""%%A""=="""" set ""%%A=%%B""",
    "  )",
    ") else if exist "".env.xunke"" (",
    "  for /f ""usebackq tokens=1,* delims=="" %%A in ("".env.xunke"") do (",
    "    if not ""%%A""=="""" set ""%%A=%%B""",
    "  )",
    ")",
    "if ""%API_PORT%""=="""" set API_PORT=8090",
    "set PYTHONPATH=%APP_DIR%",
    "set PYTHONUNBUFFERED=1",
    "echo Starting bridge on %API_PORT% ...",
    """%PY_DIR%\python.exe"" -m uvicorn xunke_bridge:app --host 0.0.0.0 --port %API_PORT%"
)
Set-Content -Path (Join-Path $artifactDir "run_bridge.bat") -Value $runBridgeLines -Encoding ascii

[string[]]$installServiceLines = @(
    "@echo off",
    "setlocal",
    "set ROOT=%~dp0",
    "set SVC_NAME=XunKeMediaCrawlerBridge",
    "set DISPLAY_NAME=XunKe MediaCrawler Bridge",
    "set CMD=""%ROOT%run_bridge.bat""",
    "set LOG_DIR=%ROOT%logs\bridge_service",
    "if not exist ""%LOG_DIR%"" mkdir ""%LOG_DIR%""",
    "where nssm >nul 2>nul",
    "if errorlevel 1 (",
    "  echo nssm.exe not found in PATH.",
    "  exit /b 1",
    ")",
    "nssm stop %SVC_NAME% >nul 2>nul",
    "nssm remove %SVC_NAME% confirm >nul 2>nul",
    "nssm install %SVC_NAME% cmd.exe /c %CMD%",
    "if errorlevel 1 (",
    "  echo failed to install service",
    "  exit /b 1",
    ")",
    "nssm set %SVC_NAME% AppDirectory ""%ROOT%""",
    "nssm set %SVC_NAME% DisplayName ""%DISPLAY_NAME%""",
    "nssm set %SVC_NAME% Start SERVICE_AUTO_START",
    "nssm set %SVC_NAME% AppExit Default Restart",
    "nssm set %SVC_NAME% AppStdout ""%LOG_DIR%\stdout.log""",
    "nssm set %SVC_NAME% AppStderr ""%LOG_DIR%\stderr.log""",
    "nssm set %SVC_NAME% AppRotateFiles 1",
    "nssm set %SVC_NAME% AppRotateOnline 1",
    "nssm set %SVC_NAME% AppRotateBytes 10485760",
    "nssm start %SVC_NAME%",
    "echo service installed: %SVC_NAME%"
)
Set-Content -Path (Join-Path $artifactDir "install_service.bat") -Value $installServiceLines -Encoding ascii

[string[]]$uninstallServiceLines = @(
    "@echo off",
    "setlocal",
    "set SVC_NAME=XunKeMediaCrawlerBridge",
    "where nssm >nul 2>nul",
    "if errorlevel 1 (",
    "  echo nssm.exe not found in PATH.",
    "  exit /b 1",
    ")",
    "nssm stop %SVC_NAME% >nul 2>nul",
    "nssm remove %SVC_NAME% confirm",
    "echo service removed: %SVC_NAME%"
)
Set-Content -Path (Join-Path $artifactDir "uninstall_service.bat") -Value $uninstallServiceLines -Encoding ascii

[string[]]$readmeLines = @(
    "# MediaCrawler XunKe Bridge (Embedded Runtime Package)",
    "",
    "## Quick Start",
    "1. Edit app\.env.xunke.local (or copy from app\.env.xunke).",
    "2. Run run_bridge.bat.",
    "3. Or run install_service.bat to install Windows service.",
    "",
    "## Health Check",
    "http://127.0.0.1:8090/api/health"
)
Set-Content -Path (Join-Path $artifactDir "README-PACKAGE.md") -Value $readmeLines -Encoding utf8

Write-Step "Zip package"
if (Test-Path $zipPath) { Remove-Item -Path $zipPath -Force }
Compress-Archive -Path $artifactDir -DestinationPath $zipPath -Force

Write-Step "Write release metadata"
$hash = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
$size = (Get-Item -Path $zipPath).Length
$releaseMetadata = [ordered]@{
    component = "MediaCrawlerBridge"
    version = $artifactVersion
    platform = "win-x64"
    channel = "stable"
    fileName = [System.IO.Path]::GetFileName($zipPath)
    fileSize = $size
    sha256 = $hash
    generatedAt = (Get-Date).ToUniversalTime().ToString("o")
    downloadUrl = "REPLACE_ME"
}
Set-Content -Path (Join-Path $outputRootAbs "$artifactName.release.json") -Value ($releaseMetadata | ConvertTo-Json -Depth 5) -Encoding utf8

Write-Step "Done"
Write-Host "artifact dir: $artifactDir" -ForegroundColor Green
Write-Host "artifact zip: $zipPath" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "Script failed." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.InvocationInfo) {
        Write-Host "Error location:" -ForegroundColor DarkYellow
        Write-Host $_.InvocationInfo.PositionMessage -ForegroundColor DarkYellow
    }
    Pause-OnError
    exit 1
}
