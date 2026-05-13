import logging

from scraper.client import DouyinClient
from scraper.config import HOT_SEARCH_URL, TRENDING_FEED_URL
from scraper.parser import parse_hot_search_items, parse_trending_aweme_items
from scraper.storage import save_to_json, save_to_csv

logger = logging.getLogger(__name__)


class DouyinTrendingScraper:
    def __init__(self, cookies=None, delay_range=None):
        self.client = DouyinClient(cookies=cookies, delay_range=delay_range)

    def fetch_hot_search(self, detail_list=False):
        params = {"detail_list": "1" if detail_list else "0"}
        resp = self.client.get(HOT_SEARCH_URL, params=params)
        if resp is None:
            logger.warning("[热搜] 请求失败，未获取到数据")
            return []

        data = resp.json()
        status_code = data.get("status_code", -1)
        if status_code != 0:
            logger.warning("[热搜] API 返回异常状态码: %s, 消息: %s", status_code, data.get("status_msg", ""))
            return []

        items = parse_hot_search_items(data)
        logger.info("[热搜] 成功获取 %d 条热搜话题", len(items))
        return items

    def fetch_trending_feed(self, count=20, max_cursor=0):
        params = {
            "count": count,
            "max_cursor": max_cursor,
            "type": "hot",
        }
        resp = self.client.get(TRENDING_FEED_URL, params=params)
        if resp is None:
            logger.warning("[热门视频] 请求失败，未获取到数据")
            return [], 0, 0

        data = resp.json()
        status_code = data.get("status_code", -1)
        if status_code != 0:
            logger.warning("[热门视频] API 返回异常状态码: %s, 消息: %s", status_code, data.get("status_msg", ""))
            return [], 0, 0

        items = parse_trending_aweme_items(data)
        has_more = data.get("has_more", 0)
        next_cursor = data.get("max_cursor", 0)

        logger.info("[热门视频] 成功获取 %d 条视频 (has_more=%s, next_cursor=%s)", len(items), has_more, next_cursor)
        return items, has_more, next_cursor

    def fetch_trending_videos(self, total=50):
        all_items = []
        max_cursor = 0
        has_more = 1

        while has_more and len(all_items) < total:
            remaining = total - len(all_items)
            batch_size = min(remaining, 20)

            items, has_more, max_cursor = self.fetch_trending_feed(
                count=batch_size, max_cursor=max_cursor
            )
            all_items.extend(items)

            if not items:
                break

        for idx, item in enumerate(all_items):
            item["rank"] = idx + 1

        logger.info("[热门视频] 共获取 %d 条视频", len(all_items))
        return all_items

    def run(self, mode="hot_search", output_format="json", count=50):
        logger.info("=" * 60)
        logger.info("  抖音热门内容爬虫")
        logger.info("  模式: %s  数量: %d  格式: %s", mode, count, output_format)
        logger.info("=" * 60)

        result = {}

        if mode in ("hot_search", "all"):
            logger.info("--- 热搜榜单 ---")
            hot_items = self.fetch_hot_search(detail_list=True)
            result["hot_search"] = hot_items

        if mode in ("trending", "all"):
            logger.info("--- 热门视频 ---")
            trending_items = self.fetch_trending_videos(total=count)
            result["trending"] = trending_items

        if mode not in ("hot_search", "trending", "all"):
            logger.error("[错误] 未知模式: %s", mode)
            return result

        saved_files = []
        for key, items in result.items():
            if not items:
                continue
            if output_format == "csv":
                saved_files.append(save_to_csv(items, filename=f"{key}.csv"))
            else:
                saved_files.append(save_to_json(items, filename=f"{key}.json"))

        logger.info("[完成] 所有数据已保存!")
        for f in saved_files:
            logger.info("  -> %s", f)
        return result

    def close(self):
        self.client.close()