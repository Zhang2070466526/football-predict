"""MD5 去重工具 —— 避免重复导入相同内容。"""
from __future__ import annotations

import hashlib
import os

from app.core.config import get_settings


def get_string_md5(text: str) -> str:
    """计算字符串的 MD5 十六进制值。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def is_processed(md5: str) -> bool:
    """检查 MD5 是否已处理过（逐行匹配记录文件）。"""
    path = get_settings().md5_path
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return any(line.strip() == md5 for line in f)


def mark_processed(md5: str) -> None:
    """把 MD5 追加写入记录文件。"""
    path = get_settings().md5_path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(md5 + "\n")
