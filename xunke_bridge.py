"""
XunKe bridge API entrypoint.
Start command:
    uv run uvicorn xunke_bridge:app --host 0.0.0.0 --port 8090 --reload
"""

import asyncio
import sys
import logging

# 关键修复：解决 Windows 下 Playwright 子进程报错问题
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xunke_api.routers import comments_router, health_router, sessions_router, video_router
from xunke_api.services.session_pool import SessionPool


session_pool = SessionPool()

app = FastAPI(
    title="MediaCrawler XunKe Bridge API",
    description="Bridge layer for XunKe to call MediaCrawler Douyin abilities.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
from fastapi import Request
from starlette.responses import Response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
        
    start_time = time.time()
    path = request.url.path
    params = dict(request.query_params)
    
    # 获取响应
    response = await call_next(request)
    
    # 为了读取响应体，我们需要特殊处理
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    duration = (time.time() - start_time) * 1000
    
    print(f"\n[DEBUG API] {request.method} {path}")
    if params:
        print(f"      Params: {params}")
    print(f"      Status: {response.status_code}")
    print(f"      Duration: {duration:.2f}ms")
    try:
        body_str = response_body.decode("utf-8")
        print(f"      Response: {body_str[:500]}{'...' if len(body_str) > 500 else ''}")
    except:
        print(f"      Response: <binary data or decode error>")
    print("-" * 50)

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(comments_router)
app.include_router(video_router)


@app.on_event("startup")
async def _startup() -> None:
    loop = asyncio.get_running_loop()
    print(f"DEBUG: Current event loop: {type(loop).__name__}")
    if sys.platform == 'win32' and type(loop).__name__ == 'SelectorEventLoop':
        print("WARNING: SelectorEventLoop detected on Windows! Playwright may fail.")
    await session_pool.startup()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await session_pool.shutdown()

