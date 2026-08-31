"""赔率领域模型。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Odds:
    """一场比赛的赔率（以欧赔 1X2 为主，亚盘/大小球可选）。

    字段含义：
    - match_id: 关联的比赛 ID
    - home_win / draw / away_win: 欧赔 1X2（主胜 / 平 / 客胜），可空
    - over_under: 大小球盘口线（如 2.5），可空
    - asian_handicap: 亚盘让球数（正值表示主队受让），可空
    """

    match_id: str
    home_win: float | None = None
    draw: float | None = None
    away_win: float | None = None
    over_under: float | None = None
    asian_handicap: float | None = None