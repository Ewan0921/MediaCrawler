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


@router.get("/api/dy/video/search", response_model=ApiResponse)
async def search_dy_videos(
    keyword: str = Query(..., min_length=1),
    offset: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    account_id: Optional[str] = Query(None),
) -> ApiResponse:
    from xunke_bridge import session_pool
    from media_platform.douyin.field import SearchChannelType

    session = await session_pool.get(account_id) if account_id else await session_pool.pick()
    if session is None:
        return ApiResponse(success=False, error_code="NO_AVAILABLE_SESSION", error="No available session")

    try:
        # 使用 VIDEO 频道进行搜索，确保返回的是视频内容
        res = await session.dy_client.search_info_by_keyword(
            keyword=keyword,
            offset=offset,
            search_channel=SearchChannelType.VIDEO
        )
        await session_pool.touch_request(session.account_id)

        items = []
        for post_item in res.get("data", []):
            try:
                # 兼容不同返回结构
                aweme_info = post_item.get("aweme_info") or post_item.get("aweme_mix_info", {}).get("mix_items", [{}])[0]
                if not aweme_info:
                    continue

                author = aweme_info.get("author", {})
                stats = aweme_info.get("statistics", {})
                video = aweme_info.get("video", {})

                items.append({
                    "aweme_id": aweme_info.get("aweme_id"),
                    "desc": aweme_info.get("desc"),
                    "create_time": aweme_info.get("create_time"),
                    "author": {
                        "uid": author.get("uid"),
                        "sec_uid": author.get("sec_uid"),
                        "nickname": author.get("nickname"),
                        "avatar": (author.get("avatar_thumb") or {}).get("url_list", [None])[0]
                    },
                    "statistics": {
                        "comment_count": stats.get("comment_count", 0),
                        "digg_count": stats.get("digg_count", 0),
                        "share_count": stats.get("share_count", 0),
                    },
                    "video": {
                        "duration": video.get("duration", 0),
                    }
                })
            except (KeyError, IndexError, TypeError):
                continue

        return ApiResponse(
            success=True,
            data={
                "items": items,
                "has_more": bool(res.get("has_more", False)),
                "cursor": offset + len(items)
            }
        )
    except Exception as exc:
        return ApiResponse(success=False, error_code="UNKNOWN_ERROR", error=str(exc))

