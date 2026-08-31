"""FastAPI 路由 —— 纯接入层：解析请求 → 调业务 → 返回响应，不写业务逻辑。"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from app.agent.agent import PredictAgent
from app.analysis.analyzer import Analyzer
from app.api.schemas import AgentRequest, PredictRequest
from app.core.config import get_settings
from app.predict.poisson import PoissonPredictor
from app.storage.match_repository import MatchRepository

router = APIRouter()


# ── 懒加载单例：首次调用才初始化，避免未配 API key 或建库导致启动即失败 ──

@lru_cache(maxsize=1)
def _get_predictor() -> PoissonPredictor:
    """预测器单例（泊松模型）。"""
    return PoissonPredictor()


@lru_cache(maxsize=1)
def _get_agent() -> PredictAgent:
    """预测 agent 单例。"""
    return PredictAgent()


@lru_cache(maxsize=1)
def _get_analyzer() -> Analyzer:
    """统计器单例。"""
    return Analyzer()


@lru_cache(maxsize=1)
def _get_repo() -> MatchRepository:
    """存储仓库单例（SQLite 文件在首次调用时创建）。"""
    return MatchRepository(get_settings().db_path)


def _finished(df):
    """只保留已完赛的比赛（有比分），供统计/预测使用，排除未开赛。"""
    if df.empty or "status" not in df.columns:
        return df
    return df[df["status"] == "完场"]


# ── 路由 ──

@router.get("/health")
def health() -> dict:
    """健康检查。"""
    return {"status": "ok"}


@router.post("/api/predict")
def predict(req: PredictRequest) -> dict:
    """比赛预测：从存储加载历史比赛后交给泊松预测器。"""
    matches = _finished(_get_repo().load_matches())
    return _get_predictor().predict(req.home_team, req.away_team, matches, handicap=req.handicap)


@router.post("/api/agent")
def agent_chat(req: AgentRequest) -> dict:
    """对话式预测 agent。"""
    return _get_agent().ask(req.question, history=req.history)


@router.get("/api/stats")
def stats(team: str) -> dict:
    """球队统计：只加载该队相关比赛再统计。"""
    matches = _finished(_get_repo().load_matches(team=team))
    return _get_analyzer().team_stats(team, matches)


@router.get("/api/matches")
def list_matches() -> dict:
    """列出全部已采集比赛（左连赔率）。"""
    matches = _get_repo().load_matches()
    odds = _get_repo().load_odds()
    merged = matches.merge(odds, on="match_id", how="left") if not odds.empty else matches
    return {"matches": merged.to_dict(orient="records")}


@router.get("/api/table")
def league_table() -> dict:
    """全部球队积分榜。"""
    matches = _finished(_get_repo().load_matches())
    return {"table": _get_analyzer().league_table(matches)}


@router.get("/api/players")
def list_players(team: str | None = None) -> dict:
    """球员名单（可按球队筛选）。"""
    df = _get_repo().load_players(team_name=team)
    return {"players": df.to_dict(orient="records")}


@router.get("/api/teams")
def list_teams() -> dict:
    """全部球队名（供下拉选择）。"""
    matches = _get_repo().load_matches()
    teams = sorted(set(matches["home_team"]) | set(matches["away_team"])) if not matches.empty else []
    return {"teams": teams}
