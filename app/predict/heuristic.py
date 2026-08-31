"""启发式预测器 —— 基于历史胜率的简单模型，作为 ML 模型接入前的兜底。"""
from __future__ import annotations

import pandas as pd

from app.predict.base import Predictor


class HeuristicPredictor(Predictor):
    """基于「主队历史胜率 + 客队历史失利率」的粗略概率估算。

    说明：当前为占位实现，数据充足后建议替换为泊松模型 / 梯度提升等更准确的方法。
    """

    def predict(self, home_team: str, away_team: str, matches: pd.DataFrame) -> dict:
        """预测主客两队比赛结果（详见基类注释）。"""
        if matches is None or matches.empty:
            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_win_prob": None,
                "draw_prob": None,
                "away_win_prob": None,
                "prediction": "数据不足，无法预测",
            }

        # 主队历史胜率
        home_wins = len(matches[(matches["home_team"] == home_team) & (matches["home_goals"] > matches["away_goals"])])
        home_total = len(matches[matches["home_team"] == home_team]) or 1
        # 客队历史失利率（客队客场比赛中主队获胜的比例，即客队客场脆弱度）
        away_losses = len(matches[(matches["away_team"] == away_team) & (matches["home_goals"] > matches["away_goals"])])
        away_total = len(matches[matches["away_team"] == away_team]) or 1

        home_strength = home_wins / home_total
        away_weakness = away_losses / away_total

        # 粗略概率（占位，数据充足后可引入泊松分布）
        home_win_prob = round(0.5 + (home_strength + away_weakness) / 4, 3)
        away_win_prob = round((1 - home_win_prob) * 0.6, 3)
        draw_prob = round(1 - home_win_prob - away_win_prob, 3)

        if home_win_prob >= max(draw_prob, away_win_prob):
            prediction = "主队胜"
        elif away_win_prob >= max(draw_prob, home_win_prob):
            prediction = "客队胜"
        else:
            prediction = "平局"

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": home_win_prob,
            "draw_prob": draw_prob,
            "away_win_prob": away_win_prob,
            "prediction": prediction,
        }
