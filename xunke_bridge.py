# -*- coding: utf-8 -*-
"""
XunKe bridge API entrypoint.
Start command:
    uvicorn xunke_bridge:app --host 0.0.0.0 --port 8090
"""

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

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(comments_router)
app.include_router(video_router)


@app.on_event("startup")
async def _startup() -> None:
    await session_pool.startup()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await session_pool.shutdown()

