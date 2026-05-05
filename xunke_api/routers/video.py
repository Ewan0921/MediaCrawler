from typing import Optional

from fastapi import APIRouter, Query

from xunke_api.schemas.responses import ApiResponse


router = APIRouter(tags=["douyin-video"])


@router.get("/api/dy/video/meta", response_model=ApiResponse)
async def get_dy_video_meta(
    aweme_id: str = Query(..., min_length=1),
    account_id: Optional[str] = Query(None),
) -> ApiResponse:
    from xunke_bridge import session_pool

    session = await session_pool.get(account_id) if account_id else await session_pool.pick()
    if session is None:
        return ApiResponse(success=False, error_code="NO_AVAILABLE_SESSION", error="No available session")

    try:
        detail = await session.dy_client.get_video_by_id(aweme_id=aweme_id)
        await session_pool.touch_request(session.account_id)
        return ApiResponse(
            success=True,
            data={
                "aweme_id": aweme_id,
                "desc": detail.get("desc", ""),
                "comment_count": (detail.get("statistics") or {}).get("comment_count", 0),
                "digg_count": (detail.get("statistics") or {}).get("digg_count", 0),
                "share_count": (detail.get("statistics") or {}).get("share_count", 0),
                "author_sec_uid": (detail.get("author") or {}).get("sec_uid"),
            },
        )
    except Exception as exc:
        return ApiResponse(success=False, error_code="UNKNOWN_ERROR", error=str(exc))

