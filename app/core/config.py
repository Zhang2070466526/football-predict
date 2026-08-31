"""统一配置加载 —— 集中管理环境变量，通过 get_settings() 获取单例。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _read(name: str, default: str = "") -> str:
    """读取环境变量，空值回退到默认值。"""
    raw = os.getenv(name, "").strip()
    return raw if raw else default


@dataclass(frozen=True)
class Settings:
    """项目配置（不可变单例）。

    字段含义：
    - llm_api_key: DeepSeek API key（对话预测 agent 用）
    - llm_base_url: DeepSeek OpenAI 兼容接口地址
    - llm_model: LLM 模型名
    - data_dir: 数据目录
    - db_path: SQLite 结构化数据（比赛/赔率/球员）落地路径
    """

    # LLM（DeepSeek，用于对话预测 agent，OpenAI 兼容）
    llm_api_key: str = field(default_factory=lambda: _read("LLM_API_KEY"))
    llm_base_url: str = field(default_factory=lambda: _read("LLM_BASE_URL", "https://api.deepseek.com"))
    llm_model: str = field(default_factory=lambda: _read("LLM_MODEL", "deepseek-v4-pro"))

    # 数据目录与结构化存储（爬虫/预测/统计）
    data_dir: str = field(default_factory=lambda: _read("DATA_DIR", "./data"))
    db_path: str = field(default_factory=lambda: _read("DB_PATH", "./data/football.db"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局唯一配置实例。"""
    return Settings()
