"""足球预测对话 agent —— DeepSeek 函数调用：查数据 + 跑预测模型。"""
from __future__ import annotations

import json
from typing import Any

from app.agent.llm import chat
from app.analysis.analyzer import Analyzer
from app.core.config import get_settings
from app.models.team_alias import resolve_team
from app.predict.poisson import PoissonPredictor
from app.storage.match_repository import MatchRepository

_SYSTEM_PROMPT = (
    "你是足球比赛预测助手。你可以调用工具查询球队统计、历史交锋、未来赛事、球员阵容，"
    "并用泊松模型预测比赛结果（胜平负概率、最可能比分、期望进球、大小球、让球胜平负）。"
    "回答要基于工具返回的真实数据，可结合球队阵容等因素给出简洁的分析和预测，不要编造数据。"
    "支持多轮追问，结合对话上下文回答。球队名请使用简体中文全名。"
)

_MAX_ITER = 6  # 最多工具调用轮数，防止死循环

# 工具定义（OpenAI 函数调用格式）
_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_matches",
            "description": "查询未来未开赛的比赛（对阵和时间）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_stats",
            "description": "查询某球队的历史统计（场次/胜平负/进球/场均进球/场均失球）",
            "parameters": {
                "type": "object",
                "properties": {"team": {"type": "string", "description": "球队名（简体中文全名）"}},
                "required": ["team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_head_to_head",
            "description": "查询两队历史交锋记录",
            "parameters": {
                "type": "object",
                "properties": {
                    "home_team": {"type": "string", "description": "主队名"},
                    "away_team": {"type": "string", "description": "客队名"},
                },
                "required": ["home_team", "away_team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_match",
            "description": "用泊松模型预测两队比赛结果（胜平负概率、期望进球、最可能比分、大小球概率；可传让球数算让球胜平负）",
            "parameters": {
                "type": "object",
                "properties": {
                    "home_team": {"type": "string", "description": "主队名"},
                    "away_team": {"type": "string", "description": "客队名"},
                    "handicap": {"type": "number", "description": "让球数（主队让几球，如 0.5/1/1.5），可选"},
                    "odds": {"type": "array", "items": {"type": "number"}, "description": "欧赔 [主胜, 平, 客胜]，可选，用于赔率融合"},
                },
                "required": ["home_team", "away_team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_players",
            "description": "查询某球队的球员阵容（姓名/位置/号码）",
            "parameters": {
                "type": "object",
                "properties": {"team": {"type": "string", "description": "球队名（简体中文全名）"}},
                "required": ["team"],
            },
        },
    },
]


class PredictAgent:
    """足球预测对话 agent。

    用 DeepSeek 函数调用把「查数据 + 跑预测模型」串起来，
    对用户的自然语言问题给出有数据支撑的预测分析。
    """

    def __init__(self) -> None:
        s = get_settings()
        self._repo = MatchRepository(s.db_path)
        self._predictor = PoissonPredictor()
        self._analyzer = Analyzer()

    def ask(self, question: str, history: list[dict] | None = None) -> dict[str, Any]:
        """回答用户的预测问题（支持多轮追问）。

        参数：
        - question: 自然语言问题
        - history: 历史对话 [{"role": "user"/"assistant", "content": "..."}]

        返回：{"answer": 文本回答}
        """
        messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for h in history or []:
            role, content = h.get("role"), h.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": question})
        for _ in range(_MAX_ITER):
            resp = chat(messages, tools=_TOOLS, temperature=0.3)
            msg = resp["choices"][0]["message"]
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                return {"answer": msg.get("content", "")}
            # 记录 assistant 消息，执行工具，回填结果
            messages.append(msg)
            for tc in tool_calls:
                name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._call_tool(name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        return {"answer": "分析超时，请简化问题后重试"}

    # ── 工具分发 ──

    def _call_tool(self, name: str, args: dict) -> Any:
        """按工具名分发执行（先统一球队别名）。"""
        for key in ("team", "home_team", "away_team"):
            if args.get(key):
                args[key] = resolve_team(args[key])
        if name == "list_upcoming_matches":
            return self._upcoming()
        if name == "get_team_stats":
            return self._team_stats(args.get("team", ""))
        if name == "get_head_to_head":
            return self._head_to_head(args.get("home_team", ""), args.get("away_team", ""))
        if name == "predict_match":
            return self._predict(args.get("home_team", ""), args.get("away_team", ""), args.get("handicap"), args.get("odds"))
        if name == "get_team_players":
            return self._players(args.get("team", ""))
        return {"error": f"未知工具 {name}"}

    # ── 工具实现 ──

    def _finished(self):
        """已完赛的比赛（供统计/预测使用）。"""
        m = self._repo.load_matches()
        if m.empty or "status" not in m.columns:
            return m
        return m[m["status"] == "完场"]

    def _upcoming(self) -> list[dict]:
        """未来未开赛的比赛（含赔率）。"""
        m = self._repo.load_matches()
        if m.empty or "status" not in m.columns:
            return []
        up = m[m["status"] == "未开赛"]
        odds = self._repo.load_odds()
        if not odds.empty:
            up = up.merge(odds, on="match_id", how="left")
        cols = ["date", "league", "home_team", "away_team", "home_win", "draw", "away_win"]
        return up[[c for c in cols if c in up.columns]].to_dict(orient="records")

    def _team_stats(self, team: str) -> dict:
        """某球队统计。"""
        return self._analyzer.team_stats(team, self._finished())

    def _head_to_head(self, home: str, away: str) -> list[dict]:
        """两队历史交锋。"""
        m = self._finished()
        h2h = m[
            ((m["home_team"] == home) & (m["away_team"] == away))
            | ((m["home_team"] == away) & (m["away_team"] == home))
        ]
        return h2h[["date", "home_team", "away_team", "home_goals", "away_goals"]].to_dict(orient="records")

    def _predict(self, home: str, away: str, handicap: float | None = None, odds: list | None = None) -> dict:
        """泊松模型预测（可带让球数、赔率融合）。"""
        return self._predictor.predict(home, away, self._finished(), handicap=handicap, odds=odds)

    def _players(self, team: str) -> list[dict]:
        """某球队球员阵容（含出场/进球/助攻）。"""
        df = self._repo.load_players(team_name=team)
        if df.empty:
            return []
        cols = ["name", "position", "number", "appearances", "goals", "assists"]
        return df[[c for c in cols if c in df.columns]].to_dict(orient="records")
