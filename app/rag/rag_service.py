"""RAG 问答服务 —— 查询重写 + 检索 + 上下文 + LLM 生成；文本分块 + MD5 去重导入。"""
from __future__ import annotations

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.rag.llm import chat
from app.rag.md5_utils import get_string_md5, is_processed, mark_processed
from app.rag.vector_store import VectorStore

_SYSTEM_PROMPT = (
    "你是足球数据分析助手。请基于下面提供的检索上下文回答问题，"
    "只使用上下文中出现的事实；上下文没有的信息就明确说不知道，不要编造。"
)

_REWRITE_PROMPT = (
    "你是查询重写助手。把用户的口语化问题改写成更具体、更利于语义检索的查询语句。"
    "可以补充关键同义词和关键词，但不要添加用户没有询问的内容。"
    "只输出改写后的查询，不要任何解释。"
)

# 分块分隔符优先级：段落 → 换行 → 中文标点 → 空格 → 单字符兜底
_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]


class RagService:
    """封装「查询重写 → 检索 → 拼接上下文 → LLM 回答」与「分块 → 去重 → 导入」。"""

    def __init__(self) -> None:
        s = get_settings()
        self._store = VectorStore()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=s.chunk_size,
            chunk_overlap=s.chunk_overlap,
            separators=_SEPARATORS,
            length_function=len,
        )

    # ── 问答 ──

    def _rewrite_query(self, query: str) -> str:
        """用 LLM 重写查询，让向量检索更准确；失败回退原问题。"""
        try:
            rewritten = chat([
                {"role": "system", "content": _REWRITE_PROMPT},
                {"role": "user", "content": f"原始问题：{query}\n改写后的查询："},
            ], temperature=0.3)
            return rewritten.strip() if rewritten and rewritten.strip() else query
        except Exception:
            return query

    def ask(self, question: str, k: int = 4) -> dict[str, Any]:
        """RAG 问答：返回 {answer, sources}。"""
        hits = self._store.search(self._rewrite_query(question), k=k)
        context = "\n\n".join(
            f"[{i + 1}] {h['content']}" for i, h in enumerate(hits)
        )

        answer = chat([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"检索上下文：\n{context}\n\n问题：{question}"},
        ])

        return {
            "answer": answer,
            "sources": [
                {"content": h["content"], "metadata": h["metadata"], "score": h["score"]}
                for h in hits
            ],
        }

    # ── 导入 ──

    def ingest_text(self, text: str, source: str = "") -> dict:
        """导入一段文本：MD5 去重 → 分块 → 写入向量库。返回 {success, chunks_count, message}。"""
        md5 = get_string_md5(text)
        if is_processed(md5):
            return {"success": False, "message": f'内容 "{source}" 已存在，跳过'}

        chunks = self._splitter.split_text(text)
        if not chunks:
            return {"success": False, "message": "分块后为空"}

        ids = [f"{source}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": source, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        self._store.add_texts(chunks, ids=ids, metadatas=metadatas)
        mark_processed(md5)
        return {"success": True, "chunks_count": len(chunks),
                "message": f'已导入 "{source}"，{len(chunks)} 个分块'}

    def ingest(self, texts: list[str], metadatas: list[dict] | None = None) -> int:
        """直接导入已分块文本（不做分块/去重），返回条数。"""
        self._store.add_texts(texts, metadatas=metadatas)
        return len(texts)

    # ── 管理 ──

    def count(self) -> int:
        return self._store.count()

    def list_sources(self) -> list[str]:
        return self._store.list_sources()

    def delete_by_source(self, source: str) -> int:
        return self._store.delete_by_source(source)

    def clear(self) -> None:
        self._store.clear()
