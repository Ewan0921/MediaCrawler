"""
XunKe bridge API entrypoint.
Start command:
    uv run uvicorn xunke_bridge:app --host 0.0.0.0 --port 8090 --reload
"""

import asyncio
import sys
import io
import logging

# Force UTF-8 encoding for stdout/stderr to prevent encoding errors
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 关键修复：解决 Windows 下 Playwright 子进程报错问题
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from tools.utils import logger


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xunke_api.routers import comments_router, health_router, sessions_router, video_router
from xunke_api.services.session_pool import SessionPool

# 强制禁用 uvicorn 默认访问日志，防止重复且无参数的日志干扰
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").propagate = False


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
import json
from fastapi import Request
from starlette.responses import Response

async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
        
    start_time = time.time()
    path = request.url.path
    params = dict(request.query_params)
    
    # 捕获请求体 (POST/PUT body)
    body = await request.body()
    await set_body(request, body)
    body_str = body.decode("utf-8", errors="replace") if body else ""
    
    # 获取响应
    response = await call_next(request)
    
    # 为了读取响应体，我们需要特殊处理
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    duration = (time.time() - start_time) * 1000
    
    try:
        resp_str = response_body.decode("utf-8")
    except:
        resp_str = "<binary data or decode error>"
        
    # 取消 JSON 美化，改为单行平铺
    try:
        resp_obj = json.loads(resp_str)
        resp_formatted = json.dumps(resp_obj, ensure_ascii=False)
    except:
        resp_formatted = resp_str
        
    # 多行日志输出，但内容平铺
    log_msg = (
        f"[API] {request.method}\n"
        f"    - Path:   {path}\n"
        f"    - Params: {json.dumps(params, ensure_ascii=False)}\n"
        f"    - Body:   {body_str}\n"
        f"    - Status: {response.status_code} ({duration:.2f}ms)\n"
        f"    - Resp:   {resp_formatted}"
    )
    logger.info(log_msg)

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
    # 再次确保在不同启动方式下 uvicorn 日志都被静默
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").propagate = False
    
    loop = asyncio.get_running_loop()
    logger.info(f"DEBUG: Current event loop: {type(loop).__name__}")
    if sys.platform == 'win32' and type(loop).__name__ == 'SelectorEventLoop':
        logger.warning("WARNING: SelectorEventLoop detected on Windows! Playwright may fail.")
    await session_pool.startup()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await session_pool.shutdown()


if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    # 加载环境配置
    load_dotenv(".env.xunke")
    
    port = int(os.getenv("API_PORT", 8090))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting bridge on {host}:{port}...")
    # 禁用 uvicorn 默认访问日志，避免重复
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    uvicorn.run("xunke_bridge:app", host=host, port=port, reload=False, access_log=False)

