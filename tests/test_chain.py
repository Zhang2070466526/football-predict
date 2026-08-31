"""全链路冒烟测试 —— 验证「抓取 → 落库 → 预测 → 统计」骨架可用。"""
from __future__ import annotations

from app.analysis.analyzer import Analyzer
from app.core.http import HttpClient
from app.crawler.mock_crawler import MockCrawler
from app.predict.heuristic import HeuristicPredictor
from app.storage.match_repository import MatchRepository


def test_full_chain(tmp_path):
    """mock 源抓取 → SQLite 落库 → 预测 + 统计 全链路。"""
    repo = MatchRepository(str(tmp_path / "test.db"))
    crawler = MockCrawler(HttpClient(), "mock")

    # 抓取 + 落库
    repo.save_matches(crawler.fetch_matches())
    assert repo.count() == 5

    # 预测
    matches = repo.load_matches()
    pred = HeuristicPredictor().predict("曼城", "阿森纳", matches)
    assert pred["home_team"] == "曼城"
    assert pred["home_win_prob"] is not None

    # 统计（曼城在样例里打了 3 场：vs 阿森纳/热刺/利物浦）
    stats = Analyzer().team_stats("曼城", repo.load_matches(team="曼城"))
    assert stats["stats"]["played"] == 3


def test_repo_dedup(tmp_path):
    """重复落库同一批比赛不应产生冗余。"""
    repo = MatchRepository(str(tmp_path / "test.db"))
    crawler = MockCrawler(HttpClient(), "mock")
    repo.save_matches(crawler.fetch_matches())
    repo.save_matches(crawler.fetch_matches())  # 再写一次
    assert repo.count() == 5
