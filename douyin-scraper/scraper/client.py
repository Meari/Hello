import time
import random
import logging

import requests

from scraper.config import (
    REQUEST_TIMEOUT,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    MAX_RETRIES,
    build_headers,
)

logger = logging.getLogger(__name__)


class DouyinClient:
    def __init__(self, cookies=None, timeout=None, delay_range=None, max_retries=None):
        self.session = requests.Session()
        self.timeout = timeout or REQUEST_TIMEOUT
        self.delay_min, self.delay_max = delay_range or (REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        self.max_retries = max_retries or MAX_RETRIES

        if cookies:
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain=".douyin.com")

    def _random_delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug("Sleeping %.2fs before request", delay)
        time.sleep(delay)

    def get(self, url, params=None, headers=None, **kwargs):
        return self._request("GET", url, params=params, headers=headers, **kwargs)

    def _request(self, method, url, params=None, headers=None, **kwargs):
        merged_headers = build_headers(headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                self._random_delay()
                logger.info("[%d/%d] %s %s", attempt, self.max_retries, method, url)

                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=merged_headers,
                    timeout=self.timeout,
                    **kwargs,
                )

                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 429:
                    wait = 5 * attempt
                    logger.warning("Rate limited (429), waiting %ds before retry", wait)
                    time.sleep(wait)
                    continue
                else:
                    logger.warning("HTTP %d for %s", resp.status_code, url)
                    if attempt < self.max_retries:
                        continue
                    resp.raise_for_status()

            except requests.exceptions.Timeout:
                logger.warning("Request timeout (attempt %d/%d)", attempt, self.max_retries)
                if attempt == self.max_retries:
                    raise
            except requests.exceptions.ConnectionError:
                logger.warning("Connection error (attempt %d/%d)", attempt, self.max_retries)
                if attempt == self.max_retries:
                    raise

        return None

    def close(self):
        self.session.close()