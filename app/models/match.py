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
    - home_goals / away_goals: 主 / 客队全场进球数（未开赛为 None）
    - home_halftime_goals / away_halftime_goals: 主 / 客队半场进球数（可空）
    - status: 比赛状态（"完场" / "未开赛" / "进行中"）
    """

    match_id: str | None
    date: str | None
    league: str | None
    home_team: str
    away_team: str
    home_goals: int | None = None
    away_goals: int | None = None
    home_halftime_goals: int | None = None
    away_halftime_goals: int | None = None
    status: str | None = None