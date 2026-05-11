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
    search_id: str = Query(""),
) -> ApiResponse:
    from xunke_bridge import session_pool
    from media_platform.douyin.field import SearchChannelType

    session = await session_pool.get(account_id) if account_id else await session_pool.pick()
    if session is None:
        return ApiResponse(success=False, error_code="NO_AVAILABLE_SESSION", error="No available session")

    try:
        # 预检查浏览器连接状态
        if not session.browser.is_connected():
            await session_pool.unregister(session.account_id)
            return ApiResponse(success=False, error_code="BROWSER_DISCONNECTED", error="Browser connection lost")

        # 使用 VIDEO 频道进行搜索，确保返回的是视频内容
        res = await session.dy_client.search_info_by_keyword(
            keyword=keyword,
            offset=offset,
            search_channel=SearchChannelType.VIDEO,
            search_id=search_id
        )
        await session_pool.touch_request(session.account_id)

        items = []
        for post_item in res.get("data", []):
            try:
                # 兼容不同返回结构
                aweme_info = post_item.get("aweme_info") or post_item.get("aweme_mix_info", {}).get("mix_items", [{}])[0]
                if not aweme_info:
                    continue
                
                # 过滤非视频内容：必须包含有效视频对象及播放地址
                video = aweme_info.get("video", {})
                if not video or not video.get("play_addr"):
                    continue

                author = aweme_info.get("author", {})
                stats = aweme_info.get("statistics", {})
                video = aweme_info.get("video", {})

                # 尝试从多个字段获取发布时间
                create_time = aweme_info.get("create_time") or aweme_info.get("create_time_v2")
                if not create_time and "create_time" in post_item:
                    create_time = post_item.get("create_time")
                
                items.append({
                    "aweme_id": aweme_info.get("aweme_id"),
                    "desc": aweme_info.get("desc"),
                    "create_time": create_time,
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

        # 兼容性提取 search_id (抖音综合搜索接口通常放在 extra.logid 或 log_pb.impr_id)
        raw_search_id = (
            res.get("search_id") 
            or res.get("extra", {}).get("logid") 
            or res.get("log_pb", {}).get("impr_id") 
            or ""
        )

        return ApiResponse(
            success=True,
            data={
                "items": items,
                "has_more": bool(res.get("has_more", False)),
                "cursor": res.get("cursor") or (offset + 15),
                "search_id": raw_search_id
            }
        )
    except Exception as exc:
        error_msg = str(exc)
        if "Target page, context or browser has been closed" in error_msg:
            try:
                await session_pool.unregister(session.account_id)
            except:
                pass
            return ApiResponse(success=False, error_code="BROWSER_DISCONNECTED", error="Browser connection lost during request")
        return ApiResponse(success=False, error_code="UNKNOWN_ERROR", error=error_msg)

