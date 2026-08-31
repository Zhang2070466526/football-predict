"""采集 500 彩票网足彩数据到 SQLite。

用法（项目根目录下执行）：
    PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_500.py 26114            # 采单期
    PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_500.py 26112 26113 26114  # 采多期
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.http import HttpClient
from app.crawler.team_resolver import TeamNameResolver
from app.crawler.zucai_500 import Zucai500Crawler
from app.storage.match_repository import MatchRepository


def main() -> None:
    """按命令行传入的期号逐个抓取并落库。"""
    periods = sys.argv[1:]
    if not periods:
        print("用法: python scripts/crawl_500.py <期号> [期号...]")
        sys.exit(1)

    s = get_settings()
    http = HttpClient(min_interval=1.0)
    crawler = Zucai500Crawler(http)
    # 用球队 ID 补全被站点截断的队名（结果缓存在 data/team_names.json）
    resolver = TeamNameResolver(http, str(Path(s.data_dir) / "team_names.json"))
    repo = MatchRepository(s.db_path)

    for period in periods:
        try:
            rows = crawler.fetch_period(period)
            for r in rows:
                r["home_team"] = resolver.resolve(r["home_team_id"]) or r["home_team"]
                r["away_team"] = resolver.resolve(r["away_team_id"]) or r["away_team"]
            matches = crawler.to_matches(rows)
            odds = crawler.to_odds(rows)
            repo.save_matches(matches)
            repo.save_odds(odds)
            print(f"期 {period}: {len(matches)} 场比赛, {len(odds)} 条赔率")
        except Exception as exc:
            # 单期失败不中断整体采集
            print(f"期 {period}: 抓取失败 ({exc})")

    print(f"累计入库 {repo.count()} 场比赛")


if __name__ == "__main__":
    main()
