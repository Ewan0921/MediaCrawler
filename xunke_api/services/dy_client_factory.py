from typing import Dict, Tuple

from playwright.async_api import BrowserContext, Page

from media_platform.douyin.client import DouYinClient
from tools import utils

from .client_factory_base import BasePlatformClientFactory


DOUYIN_COOKIE_URLS = [
    "https://douyin.com",
    "https://www.douyin.com",
    "https://creator.douyin.com",
    "https://douhot.douyin.com",
    "https://live.douyin.com",
]


async def build_douyin_headers(page: Page, browser_context: BrowserContext) -> Tuple[Dict, Dict]:
    cookie_str, cookie_dict = await utils.convert_browser_context_cookies(
        browser_context,
        urls=DOUYIN_COOKIE_URLS,
    )
    user_agent = await page.evaluate("() => navigator.userAgent")
    headers = {
        "User-Agent": user_agent,
        "Cookie": cookie_str,
        "Host": "www.douyin.com",
        "Origin": "https://www.douyin.com/",
        "Referer": "https://www.douyin.com/",
        "Content-Type": "application/json;charset=UTF-8",
    }
    return headers, cookie_dict


class DouYinClientFactory(BasePlatformClientFactory):
    """抖音平台 Client 工厂。"""

    def __init__(self) -> None:
        super().__init__(platform_code="dy")

    async def create(self, page: Page, browser_context: BrowserContext) -> DouYinClient:
        headers, cookie_dict = await build_douyin_headers(page=page, browser_context=browser_context)
        return DouYinClient(
            proxy=None,
            headers=headers,
            playwright_page=page,
            cookie_dict=cookie_dict,
            proxy_ip_pool=None,
        )

    async def health_check(self, client: DouYinClient) -> bool:
        try:
            return await client.pong(browser_context=client.playwright_page.context)  # type: ignore[arg-type]
        except Exception:
            return False


async def create_douyin_client(page: Page, browser_context: BrowserContext) -> DouYinClient:
    """函数式入口（保持向后兼容，会话池目前仍使用此调用）。"""
    factory = DouYinClientFactory()
    return await factory.create(page=page, browser_context=browser_context)

