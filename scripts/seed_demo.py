"""演示脚本 —— 跑通「抓取 → 落库 → 预测 → 统计」全链路，验证骨架可用。

用法：uv run python scripts/seed_demo.py
"""
from __future__ import annotations

from app.analysis.analyzer import Analyzer
from app.core.config import get_settings
from app.core.http import HttpClient
from app.crawler.mock_crawler import MockCrawler
from app.predict.heuristic import HeuristicPredictor
from app.storage.match_repository import MatchRepository


def main() -> None:
    """执行全链路演示。"""
    repo = MatchRepository(get_settings().db_path)

    # 1. 抓取（mock 源）
    crawler = MockCrawler(HttpClient(), "mock")
    matches = crawler.fetch_matches()
    print(f"[1] 抓取到 {len(matches)} 场比赛")

    # 2. 落库
    repo.save_matches(matches)
    print(f"[2] 已入库，当前共 {repo.count()} 场")

    # 3. 预测
    pred = HeuristicPredictor().predict("曼城", "阿森纳", repo.load_matches())
    print(f"[3] 预测 曼城 vs 阿森纳：{pred}")

    # 4. 统计
    stats = Analyzer().team_stats("曼城", repo.load_matches(team="曼城"))
    print(f"[4] 曼城统计：{stats}")


if __name__ == "__main__":
    main()
