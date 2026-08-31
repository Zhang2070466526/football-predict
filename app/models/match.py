"""比赛记录领域模型。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Match:
    """一场比赛的完整记录。

    字段含义：
    - match_id: 比赛唯一 ID（可空，空时由存储层自动生成）
    - date: 比赛日期，如 "2024-05-01"（可空）
    - league: 联赛名（可空）
    - home_team / away_team: 主 / 客队名
    - home_goals / away_goals: 主 / 客队进球数
    """

    match_id: str | None
    date: str | None
    league: str | None
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int