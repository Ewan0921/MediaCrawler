# XunKe Bridge 启动与调试指南 (Windows)

针对执行 `xunke_bridge.bat` 闪退以及在 Windows 环境下启动报错的问题，请参考以下步骤进行配置和启动。

## 1. 环境准备 (推荐使用 uv)

项目推荐使用 `uv` 进行包管理，它可以自动处理 Python 版本和依赖隔离。

### 安装 uv
在 PowerShell 中执行：
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
*安装完成后请重启终端。*

### 安装浏览器内核
Playwright 运行需要 Chromium 内核：
```powershell
uv run playwright install chromium
```

## 2. 代码修复 (Windows 必做)

由于 Windows 的异步机制限制，启动 Playwright 必须强制指定 `ProactorEventLoop`。

在 `xunke_bridge.py` 的**最顶部**（所有 import 之前）确保包含以下代码：

```python
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

## 3. 正确的启动命令

在 Windows 上调试时，**请勿使用 `--reload` 参数**，否则会导致事件循环冲突。

### 终端启动 (推荐)
```powershell
uv run uvicorn xunke_bridge:app --host 0.0.0.0 --port 8090
```

### 为什么之前的 .bat 会闪退？
1. **找不到命令**：系统没有安装 `uvicorn` 或未将其加入 PATH。
2. **环境缺失**：脚本没有自动激活虚拟环境。
3. **报错即关**：`.bat` 脚本执行失败后窗口会立即关闭，建议在脚本最后一行添加 `pause` 以便查看错误。

## 4. 常见问题
- **端口占用**：如果报 `[Errno 10048]`，说明 8090 端口被占用，请在 `.env.xunke` 中修改 `API_PORT`。
- **NotImplementedError**：这通常是因为没加第 2 步的代码，或者加了代码但使用了 `--reload` 参数启动。
