"""API 请求/响应模型（Pydantic）。"""
from __future__ import annotations

from pydantic import BaseModel


class PredictRequest(BaseModel):
    """比赛预测请求。home_team/away_team: 主 / 客队名；handicap: 让球数（可选）。"""

    home_team: str
    away_team: str
    handicap: float | None = None


class AgentRequest(BaseModel):
    """对话式预测 agent 请求。

    - question: 当前问题
    - history: 历史对话 [{"role": "user"/"assistant", "content": "..."}]，用于多轮追问
    """

    question: str
    history: list[dict] | None = None
