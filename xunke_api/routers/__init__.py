from .comments import router as comments_router
from .health import router as health_router
from .sessions import router as sessions_router
from .video import router as video_router

__all__ = [
    "comments_router",
    "health_router",
    "sessions_router",
    "video_router",
]

