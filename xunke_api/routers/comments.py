from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from xunke_api.schemas.responses import ApiResponse
from xunke_api.services.session_pool import SessionInfo, SessionPool


router = APIRouter(tags=["douyin-comments"])


def _map_comment(raw: Dict[str, Any]) -> Dict[str, Any]:
    user = raw.get("user") or {}
    return {
        "comment_id": raw.get("cid"),
        "content": raw.get("text", ""),
        "user_id": user.get("uid"),
        "sec_uid": user.get("sec_uid"),
        "nickname": user.get("nickname"),
        "avatar": (user.get("avatar_thumb") or {}).get("url_list", [""])[0]
        if isinstance(user.get("avatar_thumb"), dict)
        else "",
        "create_time": raw.get("create_time"),
        "like_count": raw.get("digg_count", 0),
        "reply_comment_total": raw.get("reply_comment_total", 0),
        "parent_comment_id": raw.get("reply_id") or "0",
        "ip_location": raw.get("ip_label", ""),
        "pictures": "",
        "reply_to_reply_id": raw.get("reply_to_reply_id"),
        "level": raw.get("level"),
    }


async def _resolve_session(pool: SessionPool, account_id: Optional[str]) -> Optional[SessionInfo]:
    if account_id:
        return await pool.get(account_id)
    return await pool.pick()


@router.get("/api/dy/comments", response_model=ApiResponse)
async def get_dy_comments(
    aweme_id: str = Query(..., min_length=1),
    cursor: int = Query(0, ge=0, description="抖音分页下标（不包含该下标位置）"),
    account_id: Optional[str] = Query(None),
) -> ApiResponse:
    from xunke_bridge import session_pool

    session = await _resolve_session(session_pool, account_id)
    if session is None:
        return ApiResponse(success=False, error_code="NO_AVAILABLE_SESSION", error="No available session")

    try:
        res = await session.dy_client.get_aweme_comments(aweme_id=aweme_id, cursor=cursor)
        await session_pool.touch_request(session.account_id)
        comments = [_map_comment(item) for item in (res.get("comments") or [])]
        return ApiResponse(
            success=True,
            data={
                "aweme_id": aweme_id,
                "comments": comments,
                "cursor": res.get("cursor", cursor),
                "has_more": bool(res.get("has_more", 0)),
                "total": res.get("total", 0),
            },
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg:
            await session_pool.mark_rate_limited(session.account_id)
            return ApiResponse(success=False, error_code="RATE_LIMITED", error=str(exc))
        return ApiResponse(success=False, error_code="UNKNOWN_ERROR", error=str(exc))


@router.get("/api/dy/comments/replies", response_model=ApiResponse)
async def get_dy_comment_replies(
    aweme_id: str = Query(..., min_length=1),
    comment_id: str = Query(..., min_length=1),
    cursor: int = Query(0, ge=0, description="抖音分页下标（不包含该下标位置）"),
    account_id: Optional[str] = Query(None),
) -> ApiResponse:
    from xunke_bridge import session_pool

    session = await _resolve_session(session_pool, account_id)
    if session is None:
        return ApiResponse(success=False, error_code="NO_AVAILABLE_SESSION", error="No available session")

    try:
        res = await session.dy_client.get_sub_comments(aweme_id=aweme_id, comment_id=comment_id, cursor=cursor)
        await session_pool.touch_request(session.account_id)
        comments = [_map_comment(item) for item in (res.get("comments") or [])]
        return ApiResponse(
            success=True,
            data={
                "aweme_id": aweme_id,
                "comment_id": comment_id,
                "comments": comments,
                "cursor": res.get("cursor", cursor),
                "has_more": bool(res.get("has_more", 0)),
            },
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg:
            await session_pool.mark_rate_limited(session.account_id)
            return ApiResponse(success=False, error_code="RATE_LIMITED", error=str(exc))
        return ApiResponse(success=False, error_code="UNKNOWN_ERROR", error=str(exc))

