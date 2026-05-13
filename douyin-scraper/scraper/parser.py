import logging

logger = logging.getLogger(__name__)


def _validate_structure(data, path, context=""):
    if isinstance(path, str):
        path = [path]
    current = data
    for i, key in enumerate(path):
        if not isinstance(current, dict):
            logger.warning(
                "[校验] %s期望字段路径 %s 中的 '%s' 不可访问，当前值类型为 %s",
                context, " -> ".join(path), key, type(current).__name__,
            )
            return False
        if key not in current:
            logger.warning(
                "[校验] %s缺少预期字段 '%s'（完整路径: %s），接口响应结构可能已变更",
                context, key, " -> ".join(path),
            )
            return False
        current = current[key]
    return True


def _check_status(data, context=""):
    status_code = data.get("status_code", -1)
    if status_code is None or status_code == -1:
        logger.warning("[校验] %s响应中缺少 status_code 字段", context)
        return False
    if status_code != 0:
        logger.warning(
            "[校验] %sAPI 返回非零状态码: %s, 消息: %s",
            context, status_code, data.get("status_msg", ""),
        )
    return status_code == 0


def parse_hot_search_items(response_data):
    items = []
    try:
        data = response_data if isinstance(response_data, dict) else response_data.json()

        if not _validate_structure(data, ["data", "word_list"], context="热搜"):
            return items

        if not _check_status(data, context="热搜"):
            return items

        word_list = data.get("data", {}).get("word_list", [])

        if not isinstance(word_list, list):
            logger.warning("[校验] 热搜 word_list 不是列表类型，实际类型: %s", type(word_list).__name__)
            return items

        for rank, word in enumerate(word_list, 1):
            item = {
                "rank": rank,
                "word": word.get("word", ""),
                "hot_value": word.get("hot_value", 0),
                "video_count": word.get("video_count", 0),
                "view_count": word.get("view_count", 0),
                "sentence_id": word.get("sentence_id", ""),
                "event_time": word.get("event_time", 0),
                "cover_url": "",
                "author_name": "",
                "digg_count": 0,
                "comment_count": 0,
                "share_count": 0,
            }
            items.append(item)

    except Exception as e:
        logger.error("[解析] 热搜数据解析失败: %s", e)

    return items


def parse_trending_aweme_items(response_data):
    items = []
    try:
        data = response_data if isinstance(response_data, dict) else response_data.json()

        if not _validate_structure(data, "aweme_list", context="热门视频"):
            return items

        if not _check_status(data, context="热门视频"):
            return items

        aweme_list = data.get("aweme_list", [])

        if not isinstance(aweme_list, list):
            logger.warning("[校验] 热门视频 aweme_list 不是列表类型，实际类型: %s", type(aweme_list).__name__)
            return items

        for rank, aweme in enumerate(aweme_list, 1):
            statistics = aweme.get("statistics", {})
            author = aweme.get("author", {})
            video = aweme.get("video", {})
            cover = video.get("cover", {}) if isinstance(video, dict) else {}

            cover_url_list = cover.get("url_list", []) if isinstance(cover, dict) else []
            cover_url = cover_url_list[0] if cover_url_list else ""

            item = {
                "rank": rank,
                "aweme_id": aweme.get("aweme_id", ""),
                "desc": aweme.get("desc", ""),
                "create_time": aweme.get("create_time", 0),
                "author_name": author.get("nickname", ""),
                "author_id": author.get("uid", ""),
                "author_sec_uid": author.get("sec_uid", ""),
                "cover_url": cover_url,
                "video_play_url": "",
                "digg_count": statistics.get("digg_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "share_count": statistics.get("share_count", 0),
                "play_count": statistics.get("play_count", 0),
                "duration": aweme.get("duration", 0),
                "share_url": aweme.get("share_url", ""),
            }

            video_play_addr = video.get("play_addr", {}) if isinstance(video, dict) else {}
            if isinstance(video_play_addr, dict):
                url_list = video_play_addr.get("url_list", [])
                item["video_play_url"] = url_list[0] if url_list else ""

            items.append(item)

    except Exception as e:
        logger.error("[解析] 视频数据解析失败: %s", e)

    return items