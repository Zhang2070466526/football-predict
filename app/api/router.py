"""FastAPI 路由 —— 纯接入层：解析请求 → 调业务 → 返回响应，不写业务逻辑。"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from app.analysis.analyzer import Analyzer
from app.api.schemas import ChatRequest, IngestRequest, PredictRequest
from app.core.config import get_settings
from app.predict.heuristic import HeuristicPredictor
from app.rag.rag_service import RagService
from app.storage.match_repository import MatchRepository

router = APIRouter()


# ── 懒加载单例：首次调用才初始化，避免未配 API key 或建库导致启动即失败 ──

@lru_cache(maxsize=1)
def _get_rag() -> RagService:
    """RAG 服务单例。"""
    return RagService()


@lru_cache(maxsize=1)
def _get_predictor() -> HeuristicPredictor:
    """预测器单例。"""
    return HeuristicPredictor()


@lru_cache(maxsize=1)
def _get_analyzer() -> Analyzer:
    """统计器单例。"""
    return Analyzer()


@lru_cache(maxsize=1)
def _get_repo() -> MatchRepository:
    """存储仓库单例（SQLite 文件在首次调用时创建）。"""
    return MatchRepository(get_settings().db_path)


# ── 路由 ──

@router.get("/health")
def health() -> dict:
    """健康检查。"""
    return {"status": "ok"}


@router.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    """RAG 问答。"""
    return _get_rag().ask(req.question, k=req.k)


@router.post("/api/predict")
def predict(req: PredictRequest) -> dict:
    """比赛预测：从存储加载历史比赛后交给预测器。"""
    matches = _get_repo().load_matches()
    return _get_predictor().predict(req.home_team, req.away_team, matches)


@router.post("/api/ingest")
def ingest(req: IngestRequest) -> dict:
    """导入文本到向量库。"""
    return _get_rag().ingest_text(req.text, req.source)


@router.get("/api/stats")
def stats(team: str) -> dict:
    """球队统计：只加载该队相关比赛再统计。"""
    matches = _get_repo().load_matches(team=team)
    return _get_analyzer().team_stats(team, matches)


@router.get("/api/docs")
def docs() -> dict:
    """向量库文档数。"""
    return {"documents": _get_rag().count()}


@router.get("/api/sources")
def sources() -> dict:
    """已导入的文档来源。"""
    return {"sources": _get_rag().list_sources()}


@router.delete("/api/clear")
def clear() -> dict:
    """清空向量库。"""
    _get_rag().clear()
    return {"success": True}
