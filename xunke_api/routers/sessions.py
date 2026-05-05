from fastapi import APIRouter

from xunke_api.schemas.responses import ApiResponse, SessionRegisterRequest


router = APIRouter(tags=["sessions"])


@router.post("/api/sessions/register", response_model=ApiResponse)
async def register_session(req: SessionRegisterRequest) -> ApiResponse:
    from xunke_bridge import session_pool

    try:
        await session_pool.register(account_id=req.account_id, cdp_url=req.cdp_url)
        status_map = await session_pool.status()
        return ApiResponse(success=True, data=status_map.get(req.account_id))
    except Exception as exc:
        return ApiResponse(success=False, error_code="REGISTER_FAILED", error=str(exc))


@router.delete("/api/sessions/{account_id}", response_model=ApiResponse)
async def unregister_session(account_id: str) -> ApiResponse:
    from xunke_bridge import session_pool

    try:
        await session_pool.unregister(account_id=account_id)
        return ApiResponse(success=True, data={"account_id": account_id})
    except Exception as exc:
        return ApiResponse(success=False, error_code="UNREGISTER_FAILED", error=str(exc))


@router.get("/api/sessions", response_model=ApiResponse)
async def list_sessions() -> ApiResponse:
    """列出所有已注册的会话状态。

    返回结构：
        {
            "total": int,
            "sessions": [SessionStatus, ...]
        }
    """
    from xunke_bridge import session_pool

    try:
        status_map = await session_pool.status()
        sessions = list(status_map.values())
        return ApiResponse(
            success=True,
            data={
                "total": len(sessions),
                "sessions": sessions,
            },
        )
    except Exception as exc:
        return ApiResponse(success=False, error_code="STATUS_FAILED", error=str(exc))


@router.get("/api/sessions/{account_id}/status", response_model=ApiResponse)
async def session_status(account_id: str) -> ApiResponse:
    from xunke_bridge import session_pool

    try:
        status_map = await session_pool.status()
        item = status_map.get(account_id)
        if item is None:
            return ApiResponse(success=False, error_code="SESSION_NOT_FOUND", error="Session not found")
        return ApiResponse(success=True, data=item)
    except Exception as exc:
        return ApiResponse(success=False, error_code="STATUS_FAILED", error=str(exc))

