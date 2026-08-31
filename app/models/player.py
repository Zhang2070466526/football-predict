"""球员领域模型。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Player:
    """一名球员的阵容信息。

    字段含义：
    - team_id: 所属球队 ID（500 彩票网球队编号）
    - team_name: 所属球队名（冗余存储，便于展示/查询）
    - name: 球员姓名
    - number: 球衣号码（可空）
    - position: 位置（前锋 / 中场 / 后卫 / 门将）
    - nationality: 国籍（可空）
    - age: 年龄（可空）
    - height: 身高，如 "173cm"（可空）
    - weight: 体重，如 "65kg"（可空）
    - market_value: 身价，如 "50万"（可空）
    - appearances: 出场次数（可空）
    - goals: 进球数（可空）
    - assists: 助攻数（可空）
    """

    team_id: str
    team_name: str
    name: str
    number: str | None = None
    position: str | None = None
    nationality: str | None = None
    age: str | None = None
    height: str | None = None
    weight: str | None = None
    market_value: str | None = None
    appearances: str | None = None
    goals: str | None = None
    assists: str | None = None
