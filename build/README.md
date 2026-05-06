# MediaCrawler 打包与分发（内嵌 Python 运行时）

## 一键打包

在 `MediaCrawler` 根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build\package_mediacrawler_embed.ps1 -Clean
```

默认输出：

- `dist/MediaCrawler-xunke-embed-<version>/`：可直接解压部署目录
- `dist/MediaCrawler-xunke-embed-<version>.zip`：可分发压缩包
- `dist/MediaCrawler-xunke-embed-<version>.release.json`：发布元数据（含 sha256 / fileSize）

## 常用参数

- 指定 Python 版本：

```powershell
.\build\package_mediacrawler_embed.ps1 -PythonVersion 3.11.9
```

- 指定产物版本号：

```powershell
.\build\package_mediacrawler_embed.ps1 -PackageVersion 1.0.0
```

- 临时跳过 Playwright 浏览器安装（调试打包流程）：

```powershell
.\build\package_mediacrawler_embed.ps1 -SkipPlaywrightInstall
```

## 产物如何安装

解压 zip 后：

1. 编辑 `app/.env.xunke.local`（不存在就从 `app/.env.xunke` 复制）
2. 前台运行：双击 `run_bridge.bat`
3. 服务化运行：双击 `install_service.bat`（需安装 `nssm`）

健康检查：

`http://127.0.0.1:8090/api/health`

## 接入 XunKe.Updater 的建议

可以接入，推荐两种方式：

1. **同源发布（推荐）**
   - 将 `zip` 上传到与你当前 XunKe 更新同一发布站点/CDN
   - 使用 `.release.json` 的 `sha256` 与 `fileSize` 作为校验信息
   - 在 Manage 端新增 `component=MediaCrawlerBridge` 的版本记录
   - XunKe 客户端在更新流程里新增“桥接组件更新”分支

2. **后置钩子更新**
   - 继续由现有 `XunKe.Updater` 只更新 XunKe 主程序
   - XunKe 启动后后台检查 `MediaCrawlerBridge` 新版本并执行替换（停服务/替换/启服务）

当前脚本已经输出接入更新系统所需最小信息：版本号、文件名、sha256、文件大小。
