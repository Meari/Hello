def parse_hot_search_items(response_data):
    items = []
    try:
        data = response_data if isinstance(response_data, dict) else response_data.json()
        word_list = data.get("data", {}).get("word_list", [])

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
        print(f"[解析] 热搜数据解析失败: {e}")

    return items


def parse_trending_aweme_items(response_data):
    items = []
    try:
        data = response_data if isinstance(response_data, dict) else response_data.json()
        aweme_list = data.get("aweme_list", [])

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
        print(f"[解析] 视频数据解析失败: {e}")

    return items