"""统计分析与报表生成。"""
from __future__ import annotations

import pandas as pd


class Analyzer:
    """数据统计与报表生成器。

    说明：统计逻辑保持纯函数化，只依赖传入的 matches DataFrame；
    数据从哪读由调用方（storage）决定，业务层不做 I/O，便于复用与测试。
    """

    def team_stats(self, team: str, matches: pd.DataFrame | None = None) -> dict:
        """返回某球队的基础统计指标。

        参数：
        - team: 球队名
        - matches: 历史比赛 DataFrame，列需含 home_team/away_team/home_goals/away_goals

        返回：{"team", "stats": {played/wins/scored/conceded/goal_diff}}
        """
        if matches is None or matches.empty:
            return {"team": team, "stats": {}, "message": "数据不足"}

        home = matches[matches["home_team"] == team]
        away = matches[matches["away_team"] == team]
        played = len(home) + len(away)
        scored = home["home_goals"].sum() + away["away_goals"].sum()
        conceded = home["away_goals"].sum() + away["home_goals"].sum()
        wins = len(home[home["home_goals"] > home["away_goals"]]) + len(away[away["away_goals"] > away["home_goals"]])

        return {
            "team": team,
            "stats": {
                "played": played,
                "wins": wins,
                "scored": int(scored),
                "conceded": int(conceded),
                "goal_diff": int(scored - conceded),
            },
        }

    def league_table(self, matches: pd.DataFrame | None = None) -> list[dict]:
        """生成联赛积分榜（骨架占位，数据接入后实现）。

        参数：
        - matches: 历史比赛 DataFrame
        """
        # TODO: 数据接入后实现完整积分榜
        return []
