"""统计分析与报表生成。"""
from __future__ import annotations

import pandas as pd

from app.models.team_alias import resolve_team


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
        team = resolve_team(team)
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
                # 每场比赛场均进球 / 场均失球
                "avg_scored": round(scored / played, 2) if played else 0,
                "avg_conceded": round(conceded / played, 2) if played else 0,
            },
        }

    def league_table(self, matches: pd.DataFrame | None = None) -> list[dict]:
        """生成联赛积分榜（按积分、净胜球、进球降序）。

        参数：
        - matches: 历史比赛 DataFrame，列需含 home_team/away_team/home_goals/away_goals

        返回：每队一条 {team, played, wins, draws, losses, scored, conceded, goal_diff, points}
        """
        if matches is None or matches.empty:
            return []

        table: list[dict] = []
        # 遍历数据中出现的所有球队（主客双方合并去重）
        for team in sorted(set(matches["home_team"]) | set(matches["away_team"])):
            home = matches[matches["home_team"] == team]
            away = matches[matches["away_team"] == team]
            wins = len(home[home["home_goals"] > home["away_goals"]]) + len(away[away["away_goals"] > away["home_goals"]])
            draws = len(home[home["home_goals"] == home["away_goals"]]) + len(away[away["away_goals"] == away["home_goals"]])
            played = len(home) + len(away)
            losses = played - wins - draws
            scored = home["home_goals"].sum() + away["away_goals"].sum()
            conceded = home["away_goals"].sum() + away["home_goals"].sum()
            # 该队最常出现的联赛（有的队会打欧战，取出现次数最多的主联赛）
            leagues = list(home["league"]) + list(away["league"])
            league = max(set(leagues), key=leagues.count) if leagues else ""
            table.append({
                "team": team,
                "league": league,
                "played": played,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "scored": int(scored),
                "conceded": int(conceded),
                "goal_diff": int(scored - conceded),
                "points": wins * 3 + draws,
                "avg_scored": round(scored / played, 2) if played else 0,
                "avg_conceded": round(conceded / played, 2) if played else 0,
            })
        # 按积分、净胜球、进球依次降序排列
        table.sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["scored"]))
        return table
