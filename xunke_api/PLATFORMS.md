# MediaCrawler 桥接 — 多平台扩展指南

本桥接服务（`xunke_bridge.py` + `xunke_api/`）面向 **XunKe.Automation** 暴露统一的 RESTful API，
当前已上线平台：

| 平台 | 路径前缀 | Client | Factory |
| --- | --- | --- | --- |
| 抖音 DouYin | `/api/dy/...` | `media_platform.douyin.client.DouYinClient` | `xunke_api.services.dy_client_factory.DouYinClientFactory` |

后续新增小红书 / B 站 / 快手等平台时，请遵循以下统一约定。

---

## 路径与命名约定

- 路径前缀使用 **平台代号小写 2 字母** ：`/api/dy`、`/api/xhs`、`/api/ks`、`/api/bili` …
- 资源命名保持一致，让 XunKe 端可以做"按平台后缀切换"的复用：
  - `GET  /api/{p}/comments?aweme_id={id}&cursor={n}&account_id={?}`
  - `GET  /api/{p}/comments/replies?aweme_id={id}&comment_id={cid}&cursor={n}&account_id={?}`
  - `GET  /api/{p}/video/meta?aweme_id={id}&account_id={?}`
- 错误码通过 `ApiResponse.error_code` 统一返回（参考 `xunke_api/schemas/responses.py`）。

> 即便不同平台的 ID 字段名不同（小红书叫 `note_id`、B 站叫 `bvid`），桥接层
> **建议统一使用 `aweme_id` 形式**，由 router 内部做平台特定字段映射。这样 XunKe 端只需一套调用代码。

---

## 接入新平台的步骤模板

以小红书 (`xhs`) 为例：

### 1. 实现/复用平台 Client

MediaCrawler 上游已经有 `media_platform/xhs/client.py`。直接 import，无需修改。

### 2. 新增 client factory

新增 `xunke_api/services/xhs_client_factory.py`：

```python
from playwright.async_api import BrowserContext, Page
from media_platform.xhs.client import XiaoHongShuClient
from .client_factory_base import BasePlatformClientFactory


class XiaoHongShuClientFactory(BasePlatformClientFactory):
    def __init__(self) -> None:
        super().__init__(platform_code="xhs")

    async def create(self, page: Page, browser_context: BrowserContext) -> XiaoHongShuClient:
        # ...准备 cookies / headers
        return XiaoHongShuClient(...)

    async def health_check(self, client: XiaoHongShuClient) -> bool:
        return await client.pong()
```

### 3. 扩展 SessionPool 支持平台分发

当前 `SessionPool` 只支持抖音。建议改造为：

- `SessionInfo` 增加 `platform_code: str` 字段
- 注册请求体增加 `platform: str = "dy"`
- `register()` 内部根据 `platform` 选择对应 factory
- `pick(platform)` 按平台筛选可用会话

### 4. 新增 router

新增 `xunke_api/routers/xhs_comments.py`，复用 `comments.py` 的结构：

```python
@router.get("/api/xhs/comments", response_model=ApiResponse)
async def get_xhs_comments(note_id: str, cursor: int = 0, account_id: Optional[str] = None):
    session = await session_pool.pick(platform="xhs", account_id=account_id)
    raw = await session.client.get_note_comments(note_id=note_id, cursor=cursor)
    return ApiResponse(success=True, data=_map(raw))
```

并在 `xunke_api/routers/__init__.py` 中暴露。

### 5. XunKe 端

- 在 `IMediaCrawlerClient` 上新增 `GetXhsCommentsAsync(...)` 等方法（或新增专门的 `IXhsCrawlerClient` 接口）
- 在 `BrowserWorkerPoolService.ProcessJobSafeAsync` 中按 `job.Platform` 分发到不同 API
- 在 `MonitoredVideos` / `PlatformAccount` 等实体上确保 `Platform` 字段被正确写入

---

## 现有架构的关键不变量

接入新平台时不要破坏以下设计：

1. **会话池只包装 client，不直接做业务**：业务逻辑全部留在 router 层
2. **每个 account 一个独立 client 实例**：彼此隔离，但共享同一个 BrowserContext
3. **签名只读 localStorage**：不会和 XunKe 的 UI 自动化（私信发送）抢 DOM
4. **响应统一走 `ApiResponse` 信封**：success/data/error/error_code 四元组

---

## 错误码扩展规范

如需新增错误码，在 `xunke_api/schemas/responses.py` 顶部的常量区域追加，并同步到
XunKe 端的 `XunKe.Automation.Contracts.Dtos.MediaCrawlerErrorCodes` 类。
