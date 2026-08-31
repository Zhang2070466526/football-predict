"""预测器接口 —— 定义统一预测方法，便于多模型可插拔。"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Predictor(ABC):
    """预测器抽象基类：所有预测模型实现统一 predict 接口。

    各实现的 predict 签名一致：输入主/客队名 + 历史比赛 DataFrame，
    输出包含三类概率与预测结论的 dict。
    """

    @abstractmethod
    def predict(self, home_team: str, away_team: str, matches: pd.DataFrame) -> dict:
        """预测主客两队比赛结果。

        参数：
        - home_team / away_team: 主 / 客队名
        - matches: 历史比赛 DataFrame，列需含 home_team/away_team/home_goals/away_goals

        返回：{"home_team", "away_team", "home_win_prob", "draw_prob",
               "away_win_prob", "prediction"}
        """
        raise NotImplementedError
