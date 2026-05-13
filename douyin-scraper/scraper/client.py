import time
import random
import logging

import requests

from scraper.config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    build_headers,
    PROXY_LIST,
    PROXY_MODE,
    COOKIE_CHECK_URL,
)

logger = logging.getLogger(__name__)


class DouyinClient:
    def __init__(self, cookies=None, timeout=None, delay_range=None, max_retries=None, proxies=None):
        self.session = requests.Session()
        self.timeout = timeout or REQUEST_TIMEOUT
        self.delay_min, self.delay_max = delay_range or (REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        self.max_retries = max_retries or MAX_RETRIES

        self._proxies = proxies or list(PROXY_LIST)
        self._proxy_index = 0

        if cookies:
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain=".douyin.com")

    def _backoff_delay(self, attempt):
        base = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
        jitter = random.uniform(0, base * 0.5)
        return base + jitter

    def _random_delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug("Sleeping %.2fs before request", delay)
        time.sleep(delay)

    def _next_proxy(self):
        if not self._proxies:
            return None
        proxy = self._proxies[self._proxy_index % len(self._proxies)]
        self._proxy_index += 1
        logger.debug("Using proxy: %s", proxy)
        return {"http": proxy, "https": proxy}

    def verify_cookies(self):
        if not self.session.cookies:
            logger.info("[Cookie] 未配置 Cookie，跳过有效性检测")
            return True

        try:
            resp = self.session.get(
                COOKIE_CHECK_URL,
                headers=build_headers(),
                timeout=self.timeout,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                if "login" in resp.url.lower() or "passport" in resp.url.lower():
                    logger.warning("[Cookie] Cookie 可能已过期，响应被重定向到登录页: %s", resp.url)
                    return False
                logger.info("[Cookie] Cookie 有效性检测通过")
                return True
            else:
                logger.warning("[Cookie] Cookie 检测请求返回 HTTP %d", resp.status_code)
                return False
        except requests.exceptions.RequestException as e:
            logger.warning("[Cookie] Cookie 检测请求失败: %s", e)
            return False

    def get(self, url, params=None, headers=None, **kwargs):
        return self._request("GET", url, params=params, headers=headers, **kwargs)

    def _request(self, method, url, params=None, headers=None, **kwargs):
        merged_headers = build_headers(headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                self._random_delay()
                logger.info("[%d/%d] %s %s", attempt, self.max_retries, method, url)

                proxy_kwargs = {}
                proxy = self._next_proxy()
                if proxy:
                    proxy_kwargs["proxies"] = proxy

                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=merged_headers,
                    timeout=self.timeout,
                    **proxy_kwargs,
                    **kwargs,
                )

                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 429:
                    wait = self._backoff_delay(attempt)
                    logger.warning("Rate limited (429), backing off %.1fs before retry", wait)
                    time.sleep(wait)
                    continue
                elif resp.status_code >= 500:
                    wait = self._backoff_delay(attempt)
                    logger.warning("Server error (HTTP %d), backing off %.1fs before retry", resp.status_code, wait)
                    time.sleep(wait)
                    continue
                else:
                    logger.warning("HTTP %d for %s", resp.status_code, url)
                    if attempt < self.max_retries:
                        wait = self._backoff_delay(attempt)
                        logger.debug("Backing off %.1fs before retry %d", wait, attempt + 1)
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()

            except requests.exceptions.Timeout:
                wait = self._backoff_delay(attempt)
                logger.warning("Request timeout (attempt %d/%d), backing off %.1fs", attempt, self.max_retries, wait)
                time.sleep(wait)
                if attempt == self.max_retries:
                    raise
            except requests.exceptions.ConnectionError as e:
                wait = self._backoff_delay(attempt)
                logger.warning("Connection error (attempt %d/%d): %s, backing off %.1fs", attempt, self.max_retries, e, wait)
                time.sleep(wait)
                if attempt == self.max_retries:
                    raise

        return None

    def close(self):
        self.session.close()