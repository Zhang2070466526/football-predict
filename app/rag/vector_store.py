"""ChromaDB 向量存储封装 —— 持久化、添加、检索、管理。"""
from __future__ import annotations

import logging
from typing import Any

from langchain_chroma import Chroma

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class VectorStore:
    """封装 ChromaDB，提供「添加 → 检索 → 管理」能力。"""

    def __init__(self) -> None:
        s = get_settings()
        self._store = Chroma(
            collection_name=s.collection_name,
            embedding_function=get_embeddings(),
            persist_directory=s.chroma_dir,
        )

    # ── 写入 ──

    def add_texts(self, texts: list[str], ids: list[str] | None = None,
                  metadatas: list[dict] | None = None) -> list[str]:
        """添加文本及其元数据，返回文档 id 列表。"""
        return self._store.add_texts(texts, ids=ids, metadatas=metadatas)

    # ── 检索 ──

    def search(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        """相似度检索，返回 [{content, metadata, score}, ...]；异常返回空列表。"""
        try:
            docs = self._store.similarity_search_with_score(query, k=k)
            return [
                {"content": doc.page_content, "metadata": doc.metadata, "score": score}
                for doc, score in docs
            ]
        except Exception as exc:
            logger.error("检索失败: %s", exc)
            return []

    # ── 管理 ──

    def count(self) -> int:
        """向量库中的文档数，异常返回 0。"""
        try:
            return self._store._collection.count()
        except Exception:
            return 0

    def list_sources(self) -> list[str]:
        """列出所有已入库文档的 source（去重排序）。"""
        try:
            data = self._store.get()
            if data and data.get("metadatas"):
                return sorted({m["source"] for m in data["metadatas"] if m and "source" in m})
        except Exception:
            pass
        return []

    def delete_by_source(self, source: str) -> int:
        """按 source 删除对应分块，返回删除数量。"""
        try:
            data = self._store.get()
            ids = [i for i, m in zip(data.get("ids", []), data.get("metadatas", []))
                   if m and m.get("source") == source]
            if ids:
                self._store.delete(ids=ids)
            return len(ids)
        except Exception as exc:
            logger.error("删除失败: %s", exc)
            return 0

    def clear(self) -> None:
        """清空整个向量库。"""
        try:
            ids = self._store.get().get("ids", [])
            if ids:
                self._store.delete(ids=ids)
        except Exception as exc:
            logger.error("清空失败: %s", exc)
