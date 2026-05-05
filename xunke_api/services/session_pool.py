import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from media_platform.douyin.client import DouYinClient
from tools import utils

from .dy_client_factory import create_douyin_client


@dataclass
class SessionInfo:
    account_id: str
    cdp_url: str
    browser: Browser
    context: BrowserContext
    page: Page
    dy_client: DouYinClient
    request_count: int = 0
    cooldown_until: Optional[float] = None


class SessionPool:
    def __init__(self):
        self._playwright_ctx = None
        self._playwright: Optional[Playwright] = None
        self._sessions: Dict[str, SessionInfo] = {}
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        if self._playwright is not None:
            return
        self._playwright_ctx = async_playwright()
        self._playwright = await self._playwright_ctx.start()
        utils.logger.info("[xunke_bridge] SessionPool startup complete")

    async def shutdown(self) -> None:
        async with self._lock:
            for account_id in list(self._sessions.keys()):
                await self._close_session(account_id)
        if self._playwright_ctx is not None:
            await self._playwright_ctx.stop()
        self._playwright = None
        self._playwright_ctx = None
        utils.logger.info("[xunke_bridge] SessionPool shutdown complete")

    async def register(self, account_id: str, cdp_url: str) -> SessionInfo:
        if self._playwright is None:
            raise RuntimeError("SessionPool is not started")
        async with self._lock:
            if account_id in self._sessions:
                await self._close_session(account_id)

            browser = await self._playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            if "douyin.com" not in page.url:
                await page.goto("https://www.douyin.com")

            dy_client = await create_douyin_client(page=page, browser_context=context)
            session = SessionInfo(
                account_id=account_id,
                cdp_url=cdp_url,
                browser=browser,
                context=context,
                page=page,
                dy_client=dy_client,
            )
            self._sessions[account_id] = session
            utils.logger.info(f"[xunke_bridge] Registered session for account={account_id}")
            return session

    async def unregister(self, account_id: str) -> None:
        async with self._lock:
            await self._close_session(account_id)

    async def _close_session(self, account_id: str) -> None:
        session = self._sessions.pop(account_id, None)
        if session is None:
            return
        try:
            await session.browser.close()
        except Exception as exc:
            utils.logger.warning(f"[xunke_bridge] Close browser failed account={account_id}: {exc}")

    async def get(self, account_id: str) -> Optional[SessionInfo]:
        async with self._lock:
            return self._sessions.get(account_id)

    async def pick(self) -> Optional[SessionInfo]:
        async with self._lock:
            now = time.time()
            candidates = [
                session
                for session in self._sessions.values()
                if session.cooldown_until is None or session.cooldown_until <= now
            ]
            if not candidates:
                return None
            return sorted(candidates, key=lambda item: item.request_count)[0]

    async def mark_rate_limited(self, account_id: str, cooldown_seconds: int = 120) -> None:
        async with self._lock:
            session = self._sessions.get(account_id)
            if session is None:
                return
            session.cooldown_until = time.time() + cooldown_seconds

    async def touch_request(self, account_id: str) -> None:
        async with self._lock:
            session = self._sessions.get(account_id)
            if session is None:
                return
            session.request_count += 1

    async def status(self) -> Dict[str, Dict]:
        async with self._lock:
            sessions = list(self._sessions.values())

        data: Dict[str, Dict] = {}
        for session in sessions:
            cookie_valid = False
            connected = False
            try:
                connected = session.browser.is_connected()
                cookie_valid = await session.dy_client.pong(browser_context=session.context)
            except Exception:
                cookie_valid = False
            data[session.account_id] = {
                "account_id": session.account_id,
                "connected": connected,
                "cookie_valid": cookie_valid,
                "request_count": session.request_count,
                "cooldown_until": session.cooldown_until,
            }
        return data

