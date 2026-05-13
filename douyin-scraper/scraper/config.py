import json
import logging
import os
import random

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

REQUEST_TIMEOUT = 15
REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 3.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0

HOT_SEARCH_URL = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
TRENDING_FEED_URL = "https://www.douyin.com/aweme/v1/web/aweme/hot/"
COOKIE_CHECK_URL = "https://www.douyin.com/"

PROXY_LIST = []

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.douyin.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}


def random_user_agent():
    return random.choice(USER_AGENTS)


def build_headers(extra=None):
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random_user_agent()
    if extra:
        headers.update(extra)
    return headers


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.warning("[配置] 保存配置文件失败: %s", e)