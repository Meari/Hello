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
            print("[热搜] 请求失败，未获取到数据")
            return []

        data = resp.json()
        status_code = data.get("status_code", -1)
        if status_code != 0:
            print(f"[热搜] API 返回异常状态码: {status_code}, 消息: {data.get('status_msg', '')}")
            return []

        items = parse_hot_search_items(data)
        print(f"[热搜] 成功获取 {len(items)} 条热搜话题")
        return items

    def fetch_trending_feed(self, count=20, max_cursor=0):
        params = {
            "count": count,
            "max_cursor": max_cursor,
            "type": "hot",
        }
        resp = self.client.get(TRENDING_FEED_URL, params=params)
        if resp is None:
            print("[热门视频] 请求失败，未获取到数据")
            return []

        data = resp.json()
        status_code = data.get("status_code", -1)
        if status_code != 0:
            print(f"[热门视频] API 返回异常状态码: {status_code}, 消息: {data.get('status_msg', '')}")
            return []

        items = parse_trending_aweme_items(data)
        has_more = data.get("has_more", 0)
        next_cursor = data.get("max_cursor", 0)

        print(f"[热门视频] 成功获取 {len(items)} 条视频 (has_more={has_more}, next_cursor={next_cursor})")
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

        print(f"[热门视频] 共获取 {len(all_items)} 条视频")
        return all_items

    def run(self, mode="hot_search", output_format="json", count=50):
        print("=" * 60)
        print("  抖音热门内容爬虫")
        print(f"  模式: {mode}  数量: {count}  格式: {output_format}")
        print("=" * 60)

        if mode == "hot_search":
            items = self.fetch_hot_search(detail_list=True)
        elif mode == "trending":
            items = self.fetch_trending_videos(total=count)
        elif mode == "all":
            print("\n--- 热搜榜单 ---")
            hot_items = self.fetch_hot_search(detail_list=True)
            print("\n--- 热门视频 ---")
            trending_items = self.fetch_trending_videos(total=count)

            saved_files = []
            if hot_items:
                if output_format == "csv":
                    saved_files.append(save_to_csv(hot_items, filename="hot_search.csv"))
                else:
                    saved_files.append(save_to_json(hot_items, filename="hot_search.json"))

            if trending_items:
                if output_format == "csv":
                    saved_files.append(save_to_csv(trending_items, filename="trending_videos.csv"))
                else:
                    saved_files.append(save_to_json(trending_items, filename="trending_videos.json"))

            print("\n[完成] 所有数据已保存!")
            for f in saved_files:
                print(f"  -> {f}")
            return {"hot_search": hot_items, "trending": trending_items}
        else:
            print(f"[错误] 未知模式: {mode}")
            return []

        if output_format == "csv":
            save_to_csv(items)
        else:
            save_to_json(items)

        print("\n[完成] 数据已保存!")
        return items

    def close(self):
        self.client.close()