"""平台 Client 工厂抽象基类。

为支持后续新增平台（小红书 XHS、快手 KS、B 站 BILI 等）而预留的统一约定：
- 每个平台都需提供一个 client_factory，在已 attach 到指纹浏览器（CDP）的 Page+BrowserContext
  之上构造对应的平台 SDK 客户端。
- 平台 client 必须支持以下能力：
    * 签名/Token 注入（典型为 a_bogus、x-secsdk 等）
    * 获取一页评论列表（page_comments）
    * 获取一页二级回复（page_comment_replies）
    * 视频元数据查询（video_meta）
- SessionPool 通过 PlatformClientFactory 协议对接各平台，互不感知具体实现。

接入新平台的步骤模板见 ``xunke_api/PLATFORMS.md``。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from playwright.async_api import BrowserContext, Page


class PlatformClient(Protocol):
    """各平台 SDK Client 必须遵守的最小协议（仅用于类型标注，不强制继承）。

    具体实现为 MediaCrawler 现有的 ``DouYinClient`` / ``XiaoHongShuClient`` / ...
    它们历史上没有继承自统一基类，因此这里用 Protocol 做"鸭子类型"约束。
    """

    async def pong(self, *args, **kwargs) -> bool:  # type: ignore[no-untyped-def]
        ...


@runtime_checkable
class PlatformClientFactoryProtocol(Protocol):
    """工厂协议：把 (page, browser_context) 转换为某平台的 Client。

    采用协议而非抽象基类，是为了与 MediaCrawler 上游 ``DouYinClient`` 等
    第三方实现解耦：上游变更其构造签名时，只需修改具体 factory 即可。
    """

    async def __call__(self, page: Page, browser_context: BrowserContext) -> Any: ...


class BasePlatformClientFactory(ABC):
    """可继承的工厂基类（适合内部状态较多的平台，例如需要预热 cookie / 注入 a_bogus 脚本）。

    建议每平台提供一个 ``XxxClientFactory(BasePlatformClientFactory)`` 实现，并在 ``SessionPool``
    中按 ``account.platform`` 分发。
    """

    platform_code: str = ""

    def __init__(self, platform_code: str) -> None:
        self.platform_code = platform_code

    @abstractmethod
    async def create(self, page: Page, browser_context: BrowserContext) -> Any:
        """根据 page+context 构造平台 Client。"""

    async def warmup(self, page: Page, browser_context: BrowserContext) -> None:
        """可选：在创建 client 之前做的预热操作（注入脚本、等待 cookie 等）。

        默认空实现，子类可按需覆盖。
        """
        return None

    async def health_check(self, client: Any) -> bool:
        """可选：判断 client 当前的会话是否可用。默认调用 client.pong() 若存在。"""
        pong = getattr(client, "pong", None)
        if pong is None:
            return True
        try:
            return bool(await pong())
        except Exception:
            return False
