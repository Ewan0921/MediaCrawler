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
if (-not (Test-Path $embedZipPath)) {
    Invoke-WebRequest -Uri $embedUrl -OutFile $embedZipPath -UseBasicParsing
} else {
    Write-Host "    Using cached Python runtime zip"
}
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
if (-not (Test-Path $bootstrapPipPath)) {
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $bootstrapPipPath -UseBasicParsing
} else {
    Write-Host "    Using cached get-pip.py"
}
Invoke-Checked ('"{0}" "{1}" --no-warn-script-location' -f $pyExe, $bootstrapPipPath) "Install pip failed"

Write-Step "Download and install dependencies"
$pypiMirror = "https://pypi.tuna.tsinghua.edu.cn/simple"

# Pre-download setuptools and wheel so that source distributions (e.g. jieba) can be built offline
Invoke-Checked ('"{0}" -m pip download -i {1} setuptools wheel -d "{2}"' -f $pyExe, $pypiMirror, $wheelhouseDir) "Download setuptools/wheel failed"
Invoke-Checked ('"{0}" -m pip install --no-index --find-links "{1}" setuptools wheel' -f $pyExe, $wheelhouseDir) "Install setuptools/wheel failed"

Invoke-Checked ('"{0}" -m pip download -i {1} -r "{2}" -d "{3}"' -f $pyExe, $pypiMirror, (Join-Path $repoRoot "requirements.txt"), $wheelhouseDir) "Download wheels failed"
Invoke-Checked ('"{0}" -m pip install --no-index --find-links "{1}" -r "{2}"' -f $pyExe, $wheelhouseDir, (Join-Path $repoRoot "requirements.txt")) "Install dependencies failed"

if (-not $SkipPlaywrightInstall) {
    Write-Step "Install Playwright Chromium"
    $env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
    Invoke-Checked ('"{0}" -m playwright install chromium' -f $pyExe) "Install Playwright failed"
}

Write-Step "Copy app files"
$appItems = @("api","base","cache","cmd_arg","config","constant","database","db.py","libs","media_platform","model","proxy","store","tools","var.py","xunke_api","xunke_bridge.py","xunke_bridge.bat",".env.xunke","requirements.txt","README.md")
foreach ($item in $appItems) {
    $src = Join-Path $repoRoot $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $appDir $item) -Recurse -Force
    }
}

# 拷贝 nssm.exe 到产物根目录（如果开发者放入了的话）
$nssmSrc = Join-Path $buildRoot "nssm.exe"
if (Test-Path $nssmSrc) {
    Copy-Item -Path $nssmSrc -Destination (Join-Path $artifactDir "nssm.exe") -Force
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

Write-Step "Copy service scripts"
# 统一的服务安装/卸载脚本（自动检测打包/开发环境）
foreach ($scriptName in @("install_service.bat", "uninstall_service.bat")) {
    $scriptSrc = Join-Path $repoRoot $scriptName
    if (Test-Path $scriptSrc) {
        Copy-Item -Path $scriptSrc -Destination (Join-Path $artifactDir $scriptName) -Force
        Write-Host "    Copied $scriptName"
    } else {
        Write-Warning "$scriptName not found at $scriptSrc"
    }
}

# 读取 .env.xunke 获取端口号（用于 README）
$envFile = Join-Path $appDir ".env.xunke"
$apiPort = "8090"
if (Test-Path $envFile) {
    $envLines = Get-Content -Path $envFile -Encoding UTF8
    foreach ($line in $envLines) {
        if ($line -match "^\s*API_PORT\s*=\s*(\d+)") {
            $apiPort = $matches[1]
        }
    }
}

[string[]]$readmeLines = @(
    "# MediaCrawler XunKe Bridge (Embedded Runtime Package)",
    "",
    "## Quick Start",
    "1. (可选) 编辑 ``app\.env.xunke`` 修改端口等配置。",
    "2. 方式一: 双击 ``run_bridge.bat`` 前台运行（调试用）。",
    "3. 方式二: 右键 ``install_service.bat`` → 以管理员身份运行 → 安装为 Windows 服务。",
    "",
    "## 管理服务",
    "- 卸载服务: 右键 ``uninstall_service.bat`` → 以管理员身份运行",
    "- 查看状态: ``nssm status XunKeMediaCrawlerBridge``",
    "- 查看日志: ``logs\bridge_service\`` 目录",
    "",
    "## Health Check",
    "http://127.0.0.1:$apiPort/api/health"
)
Set-Content -Path (Join-Path $artifactDir "README-PACKAGE.md") -Value $readmeLines -Encoding utf8

Write-Step "Done"
Write-Host "artifact dir: $artifactDir" -ForegroundColor Green
Write-Host "Skipped zip compression as it's handled by XunKe release." -ForegroundColor Cyan
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
