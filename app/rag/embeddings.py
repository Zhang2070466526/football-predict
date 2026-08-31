"""DashScope 文本嵌入封装。"""
from __future__ import annotations

from langchain_community.embeddings import DashScopeEmbeddings

from app.core.config import get_settings


def get_embeddings() -> DashScopeEmbeddings:
    """返回 DashScope 嵌入实例（嵌入模型从配置读取）。"""
    s = get_settings()
    return DashScopeEmbeddings(
        model=s.embedding_model,
        dashscope_api_key=s.dashscope_api_key,
    )
