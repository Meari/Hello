#!/usr/bin/env python3
import argparse
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.trending import DouyinTrendingScraper


def parse_cookies(cookie_str):
    if not cookie_str:
        return {}
    cookies = {}
    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


def main():
    parser = argparse.ArgumentParser(
        description="抖音热门内容爬虫 - 抓取抖音热搜榜单和热门视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 抓取热搜榜单
  python main.py

  # 抓取热门视频（最多50条）
  python main.py -m trending -n 50

  # 同时抓取热搜和热门视频
  python main.py -m all

  # 保存为 CSV 格式
  python main.py -f csv

  # 使用 Cookie（提高成功率）
  python main.py -c "sessionid=xxx; passport_csrf_token=xxx"

  # 调试模式
  python main.py -v
        """,
    )

    parser.add_argument(
        "-m", "--mode",
        choices=["hot_search", "trending", "all"],
        default="hot_search",
        help="抓取模式: hot_search(热搜榜单), trending(热门视频), all(全部) (默认: hot_search)",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=50,
        help="抓取视频数量，仅对 trending 模式有效 (默认: 50)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "csv"],
        default="json",
        help="输出格式 (默认: json)",
    )
    parser.add_argument(
        "-c", "--cookies",
        default="",
        help='Cookie 字符串，格式: "key1=val1; key2=val2"',
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=1.0,
        help="请求最小间隔秒数 (默认: 1.0)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=3.0,
        help="请求最大间隔秒数 (默认: 3.0)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细日志",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    cookies = parse_cookies(args.cookies)
    if cookies:
        print(f"[配置] 已加载 {len(cookies)} 个 Cookie")

    scraper = DouyinTrendingScraper(
        cookies=cookies if cookies else None,
        delay_range=(args.min_delay, args.max_delay),
    )

    try:
        scraper.run(
            mode=args.mode,
            output_format=args.format,
            count=args.count,
        )
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作")
    except Exception as e:
        print(f"\n[错误] {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()