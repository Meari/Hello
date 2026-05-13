import json
import csv
import logging
import os
from datetime import datetime

from scraper.config import OUTPUT_DIR, ensure_output_dir

logger = logging.getLogger(__name__)


def save_to_json(data, filename=None):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"douyin_trending_{timestamp}.json"

    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("[存储] JSON 已保存至: %s", filepath)
    except OSError as e:
        logger.error("[存储] JSON 写入失败: %s", e)
        return None
    return filepath


def save_to_csv(records, filename=None):
    if not records:
        logger.warning("[存储] 没有数据可保存")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"douyin_trending_{timestamp}.csv"

    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, filename)
    fieldnames = list(records[0].keys())

    try:
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        logger.info("[存储] CSV 已保存至: %s", filepath)
    except OSError as e:
        logger.error("[存储] CSV 写入失败: %s", e)
        return None
    return filepath