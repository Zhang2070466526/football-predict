"""Dixon-Coles 泊松模型预测器 —— 用球队攻防强度预测比分分布。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import poisson

from app.models.team_alias import resolve_team
from app.predict.base import Predictor

_MAX_GOALS = 10  # 单队进球数上限（截断泊松，覆盖绝大多数比分）
_RHO = -0.1  # Dixon-Coles 低比分相关性系数（负值表示低比分比独立泊松更常见）


class PoissonPredictor(Predictor):
    """基于 Dixon-Coles 泊松模型的比赛预测。

    思路：
    1. 从历史比赛计算每队进攻（场均进球）与防守（场均失球）强度；
    2. 结合联赛平均主/客进球（含主场优势），估计两队期望进球；
    3. 按泊松分布展开比分概率矩阵（含 Dixon-Coles 低比分修正）；
    4. 汇总得到胜/平/负概率、最可能比分、期望进球与大小球概率。
    """

    def predict(
        self,
        home_team: str,
        away_team: str,
        matches: pd.DataFrame,
        handicap: float | None = None,
        odds: tuple | list | None = None,
    ) -> dict:
        """预测主客两队比赛结果。

        参数：
        - home_team / away_team: 主 / 客队名
        - matches: 已完赛的历史比赛 DataFrame，列需含 home_team/away_team/home_goals/away_goals
        - handicap: 让球数（主队让 handicap 球），如 0.5=半球、1=一球；None 表示不算让球
        - odds: 欧赔 [主胜, 平, 客胜]，传入则与泊松概率融合

        返回：胜平负概率、期望进球、最可能比分、大小球概率、预测结论；
              传入 handicap 时额外含让球胜平负概率
        """
        # 统一球队名（简称/全名 → 数据里的规范名）
        home_team = resolve_team(home_team)
        away_team = resolve_team(away_team)

        base: dict = {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": None,
            "draw_prob": None,
            "away_win_prob": None,
            "prediction": "数据不足，无法预测",
        }
        if matches is None or matches.empty:
            return base

        # 联赛平均主/客进球（主场优势体现在主队平均进球更高）
        avg_home = matches["home_goals"].mean()
        avg_away = matches["away_goals"].mean()

        strengths = self._team_strengths(matches, avg_home, avg_away)
        home = strengths.get(home_team, {"attack": 1.0, "defense": 1.0})
        away = strengths.get(away_team, {"attack": 1.0, "defense": 1.0})

        # 期望进球：主队进攻 × 客队防守 × 联赛主场均（客场同理）
        lam_home = home["attack"] * away["defense"] * avg_home
        lam_away = away["attack"] * home["defense"] * avg_away

        # 比分概率矩阵，行=主队进球、列=客队进球
        matrix = self._score_matrix(lam_home, lam_away)
        n = _MAX_GOALS + 1

        home_win = matrix[np.tril_indices(n, -1)].sum()
        draw = np.trace(matrix)
        away_win = matrix[np.triu_indices(n, 1)].sum()

        # 赔率融合：把欧赔隐含概率与泊松概率加权平均（市场共识是最强信号）
        if odds and len(odds) == 3:
            home_win, draw, away_win = self._blend_odds(home_win, draw, away_win, odds)

        # 最可能比分
        best_i, best_j = np.unravel_index(matrix.argmax(), matrix.shape)

        # 大小球（总进球 >= 3 即大于 2.5 球）
        total = np.add.outer(np.arange(n), np.arange(n))
        over25 = matrix[total >= 3].sum()

        prediction = self._result_label(home_win, draw, away_win)

        result = {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(home_win, 3),
            "draw_prob": round(draw, 3),
            "away_win_prob": round(away_win, 3),
            "expected_home_goals": round(lam_home, 2),
            "expected_away_goals": round(lam_away, 2),
            "most_likely_score": f"{best_i}-{best_j}",
            "over_2_5_prob": round(over25, 3),
            "prediction": prediction,
        }
        # 让球盘：主队让 handicap 球后的胜平负
        if handicap is not None:
            hw, hd, hl = self._handicap_result(matrix, handicap)
            result["handicap"] = handicap
            result["handicap_home_win"] = round(hw, 3)
            result["handicap_draw"] = round(hd, 3)
            result["handicap_away_win"] = round(hl, 3)
            result["handicap_prediction"] = self._result_label(hw, hd, hl)
        return result

    # ── 内部计算 ──

    def _team_strengths(
        self, matches: pd.DataFrame, avg_home: float, avg_away: float
    ) -> dict[str, dict[str, float]]:
        """计算每队进攻/防守强度（相对联赛平均的比值）。

        参数：
        - matches: 历史比赛
        - avg_home / avg_away: 联赛平均主/客进球

        返回：{队名: {"attack": 进攻强度, "defense": 防守强度}}
        """
        avg_league = (avg_home + avg_away) / 2
        strengths: dict[str, dict[str, float]] = {}
        for team in set(matches["home_team"]) | set(matches["away_team"]):
            home = matches[matches["home_team"] == team]
            away = matches[matches["away_team"] == team]
            played = len(home) + len(away)
            if played == 0 or avg_league == 0:
                continue
            scored = home["home_goals"].sum() + away["away_goals"].sum()
            conceded = home["away_goals"].sum() + away["home_goals"].sum()
            strengths[team] = {
                "attack": (scored / played) / avg_league,
                "defense": (conceded / played) / avg_league,
            }
        return strengths

    def _score_matrix(self, lam_home: float, lam_away: float) -> np.ndarray:
        """生成比分概率矩阵（含 Dixon-Coles 低比分修正并归一化）。

        参数：
        - lam_home / lam_away: 主 / 客队期望进球

        返回：(_MAX_GOALS+1) × (_MAX_GOALS+1) 的概率矩阵，行=主队进球、列=客队进球
        """
        n = _MAX_GOALS + 1
        matrix = np.outer(
            poisson.pmf(np.arange(n), lam_home),
            poisson.pmf(np.arange(n), lam_away),
        )
        # Dixon-Coles 修正：0-0、1-1 上调，1-0、0-1 下调（低比分更常见）
        matrix[0, 0] *= 1 - lam_home * lam_away * _RHO
        matrix[1, 0] *= 1 + lam_home * _RHO
        matrix[0, 1] *= 1 + lam_away * _RHO
        matrix[1, 1] *= 1 - _RHO
        return matrix / matrix.sum()

    @staticmethod
    def _blend_odds(ph: float, pd: float, pa: float, odds: tuple | list, weight: float = 0.5) -> tuple[float, float, float]:
        """把欧赔隐含概率与泊松概率加权融合。

        参数：
        - ph / pd / pa: 泊松模型的胜平负概率
        - odds: 欧赔 [主胜, 平, 客胜]
        - weight: 泊松概率的权重（1-weight 为赔率权重）

        返回：融合后的胜平负概率
        """
        oh, od, oa = odds
        try:
            total = 1 / oh + 1 / od + 1 / oa  # 归一化去除博彩水位
            ih, idd, ia = (1 / oh) / total, (1 / od) / total, (1 / oa) / total
        except (ZeroDivisionError, TypeError):
            return ph, pd, pa
        return (
            weight * ph + (1 - weight) * ih,
            weight * pd + (1 - weight) * idd,
            weight * pa + (1 - weight) * ia,
        )

    @staticmethod
    def _handicap_result(matrix: np.ndarray, handicap: float) -> tuple[float, float, float]:
        """从比分矩阵计算让球 handicap（主队让 handicap 球）的胜平负概率。

        让球后的主队净胜 = 主队进球 - 客队进球 - handicap：
        - 让球胜：> 0
        - 让球平：== 0（仅整数让球可能出现）
        - 让球负：< 0
        """
        n = _MAX_GOALS + 1
        diff = np.subtract.outer(np.arange(n), np.arange(n))  # 主队进球 - 客队进球
        win = matrix[diff > handicap].sum()
        draw = matrix[diff == handicap].sum()
        lose = matrix[diff < handicap].sum()
        return win, draw, lose

    @staticmethod
    def _result_label(home_win: float, draw: float, away_win: float) -> str:
        """按最高概率返回胜负结论。"""
        if home_win >= max(draw, away_win):
            return "主队胜"
        if away_win >= max(draw, home_win):
            return "客队胜"
        return "平局"
