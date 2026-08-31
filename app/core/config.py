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
    - dashscope_api_key: DashScope（阿里云）API key，嵌入与 LLM 共用（必填）
    - embedding_model: 嵌入模型名
    - llm_model: LLM 模型名
    - chroma_dir: ChromaDB 向量库持久化目录（RAG 用）
    - collection_name: ChromaDB collection 名
    - data_dir: 数据目录
    - db_path: SQLite 结构化数据（比赛/赔率）落地路径
    - chunk_size / chunk_overlap: 文本导入向量库前的分块参数
    - md5_path: MD5 去重记录文件路径
    """

    # DashScope（嵌入 + LLM）
    dashscope_api_key: str = field(default_factory=lambda: _read("DASHSCOPE_API_KEY"))
    embedding_model: str = field(default_factory=lambda: _read("EMBEDDING_MODEL", "text-embedding-v2"))
    llm_model: str = field(default_factory=lambda: _read("LLM_MODEL", "qwen-plus"))

    # 向量库（RAG）
    chroma_dir: str = field(default_factory=lambda: _read("CHROMA_DIR", "./chroma_data"))
    collection_name: str = field(default_factory=lambda: _read("COLLECTION_NAME", "football"))

    # 数据目录与结构化存储（爬虫/预测/统计）
    data_dir: str = field(default_factory=lambda: _read("DATA_DIR", "./data"))
    db_path: str = field(default_factory=lambda: _read("DB_PATH", "./data/football.db"))

    # 文本分块
    chunk_size: int = 500
    chunk_overlap: int = 50

    # MD5 去重记录文件
    md5_path: str = field(default_factory=lambda: _read("MD5_PATH", "./data/processed_md5.txt"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局唯一配置实例。"""
    return Settings()
