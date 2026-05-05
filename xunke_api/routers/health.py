from fastapi import APIRouter

from xunke_api.schemas.responses import ApiResponse


router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=ApiResponse)
async def health() -> ApiResponse:
    return ApiResponse(success=True, data={"status": "ok"})


@router.get("/api/health/browser", response_model=ApiResponse)
async def browser_health() -> ApiResponse:
    from xunke_bridge import session_pool

    status = await session_pool.status()
    connected_count = sum(1 for item in status.values() if item.get("connected"))
    return ApiResponse(
        success=True,
        data={
            "sessions_total": len(status),
            "sessions_connected": connected_count,
            "sessions": status,
        },
    )

