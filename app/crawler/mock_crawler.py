"""模拟数据源 —— 用于在真实数据源接入前跑通「抓取 → 落库 → 预测」链路。"""
from __future__ import annotations

from app.crawler.base import BaseCrawler
from app.models.match import Match


class MockCrawler(BaseCrawler):
    """返回少量内置英超样例数据，验证全链路。真实来源接入后即可删除。

    说明：不依赖网络，纯本地返回样例，避免未确定数据源时阻塞开发。
    """

    # 样例：match_id / date / league / home_team / away_team / home_goals / away_goals
    _SAMPLE: list[tuple] = [
        ("1", "2024-05-01", "英超", "曼城", "阿森纳", 2, 1),
        ("2", "2024-05-02", "英超", "利物浦", "切尔西", 3, 1),
        ("3", "2024-05-03", "英超", "曼城", "热刺", 1, 1),
        ("4", "2024-05-04", "英超", "阿森纳", "曼联", 2, 0),
        ("5", "2024-05-05", "英超", "曼城", "利物浦", 2, 2),
    ]

    def fetch_matches(self, league: str | None = None, season: str | None = None) -> list[Match]:
        """返回内置样例比赛（可按 league 过滤）。

        参数：
        - league: 联赛名过滤（样例均为「英超」）
        - season: 保留参数，样例数据不区分赛季
        """
        rows = self._SAMPLE
        if league:
            rows = [r for r in rows if r[2] == league]
        return [
            Match(match_id=r[0], date=r[1], league=r[2],
                  home_team=r[3], away_team=r[4], home_goals=r[5], away_goals=r[6])
            for r in rows
        ]
