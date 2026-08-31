"""采集各球队球员名单到 SQLite。

用法（项目根目录下）：
    PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_players.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.http import HttpClient
from app.crawler.team_lineup import TeamLineupCrawler
from app.storage.match_repository import MatchRepository


def main() -> None:
    """遍历球队名缓存，逐个抓取阵容并落库。"""
    s = get_settings()
    cache_path = Path(s.data_dir) / "team_names.json"
    if not cache_path.exists():
        print("缺少球队名缓存，请先运行 scripts/crawl_500.py 采集比赛")
        sys.exit(1)
    # {team_id: team_name}，team_name 已是完整名
    teams = json.loads(cache_path.read_text(encoding="utf-8"))

    http = HttpClient(min_interval=1.0)
    crawler = TeamLineupCrawler(http)
    repo = MatchRepository(s.db_path)

    total = 0
    for i, (team_id, team_name) in enumerate(teams.items(), 1):
        try:
            players = crawler.fetch_players(team_id, team_name)
            repo.save_players(players)
            total += len(players)
            print(f"[{i}/{len(teams)}] {team_name}: {len(players)} 名球员")
        except Exception as exc:
            # 单队失败不中断整体采集
            print(f"[{i}/{len(teams)}] {team_name}: 失败 ({exc})")

    print(f"累计入库 {total} 名球员")


if __name__ == "__main__":
    main()
