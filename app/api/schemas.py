"""API 请求/响应模型（Pydantic）。

说明：请求 DTO 体积小、数量多，按 FastAPI 惯例集中放在一个文件，
与「一文件一类」规范对领域模型（models/）的要求区分开。
"""
from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """RAG 问答请求。question: 用户问题；k: 检索片段数。"""

    question: str
    k: int = 4


class PredictRequest(BaseModel):
    """比赛预测请求。home_team/away_team: 主 / 客队名。"""

    home_team: str
    away_team: str


class IngestRequest(BaseModel):
    """文本导入请求。text: 待导入文本；source: 来源标注。"""

    text: str
    source: str = ""
