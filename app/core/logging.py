"""统一日志配置 —— 提供一致的日志格式与级别。"""
from __future__ import annotations

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """配置根日志器：统一格式、默认 INFO 级别。

    参数：
    - level: 日志级别，默认 INFO
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )