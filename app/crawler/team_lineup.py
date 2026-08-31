"""球队阵容爬虫 —— 抓取并解析某球队的球员名单。"""
from __future__ import annotations

import re

from app.core.http import HttpClient
from app.models.player import Player

_LINEUP_URL = "https://liansai.500.com/team/{team_id}/teamlineup/"
_ENCODING = "gb18030"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class TeamLineupCrawler:
    """抓取球队阵容页，解析出球员名单（姓名/号码/位置/国籍/身高等）。

    参数：
    - http: 统一 HTTP 客户端；不传则默认带 1 秒请求间隔
    """

    def __init__(self, http: HttpClient | None = None) -> None:
        self._http = http or HttpClient(min_interval=1.0)

    def fetch_players(self, team_id: str, team_name: str = "") -> list[Player]:
        """抓取并解析一支球队的球员名单。

        参数：
        - team_id: 球队 ID
        - team_name: 球队名（用于关联展示，可空）

        返回：该队球员列表
        """
        html = self._fetch_lineup(team_id)
        return self._parse_players(html, team_id, team_name)

    # ── 抓取 ──

    def _fetch_lineup(self, team_id: str) -> str:
        """抓取阵容页并按 GB18030 解码。"""
        url = _LINEUP_URL.format(team_id=team_id)
        return self._http.get_text(url, headers={"User-Agent": _USER_AGENT}, encoding=_ENCODING)

    # ── 解析 ──

    @staticmethod
    def _grab(pattern: str, text: str, default: str = "") -> str:
        """正则提取第一个分组，失败返回 default。"""
        m = re.search(pattern, text, re.S)
        return m.group(1).strip() if m else default

    @staticmethod
    def _cell_text(row: str, cls: str) -> str:
        """提取某 class 单元格内的纯文本（去掉嵌套标签）。"""
        m = re.search(rf'class="{cls}"[^>]*>(.*?)</td>', row, re.S)
        if not m:
            return ""
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()

    @staticmethod
    def _stat_cells(row: str) -> list[str]:
        """提取球员名单元格之后的所有统计单元格文本。

        顺序：位置 / 年龄 / 身高 / 体重 / 出场次数 / 出场时间 / 进球 / 助攻 / 黄牌 / 红牌 / 身价
        """
        after = row.split("td_qiuy", 1)[1] if "td_qiuy" in row else ""
        cells = re.findall(r'<td[^>]*>(.*?)</td>', after, re.S)
        return [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

    def _parse_players(self, html: str, team_id: str, team_name: str) -> list[Player]:
        """解析阵容页中所有球员行。

        页面按位置分表（lqiuy_list_*），每个表内 td_pos 单元格标注位置；
        球员行含 td_qiuy（姓名）单元格，据此识别。
        """
        players: list[Player] = []
        for table in re.findall(r'<table[^>]*lqiuy_list[^>]*>.*?</table>', html, re.S):
            # 该表对应的位置（如「前锋」）
            position = self._grab(r'class="td_pos"[^>]*>\s*([^<]+)', table)
            for row in re.findall(r'<tr>(.*?)</tr>', table, re.S):
                if "td_qiuy" not in row:
                    continue
                name = self._cell_text(row, "td_qiuy")
                if not name:
                    continue
                # 号码 = 姓名前的第一个纯数字单元格
                number = self._grab(r'<td[^>]*>\s*(\d{1,2})\s*</td>', row)
                # 姓名之后的统计列：位置/年龄/身高/体重/出场/时间/进球/助攻/黄牌/红牌/身价
                stats = self._stat_cells(row)
                players.append(Player(
                    team_id=team_id,
                    team_name=team_name,
                    name=name,
                    number=number or None,
                    position=position or None,
                    nationality=self._grab(r'title="([^"]+)"', row) or None,
                    age=stats[1] or None if len(stats) > 1 else None,
                    height=self._grab(r'(\d+cm)', row) or None,
                    weight=self._grab(r'(\d+kg)', row) or None,
                    appearances=stats[4] or None if len(stats) > 4 else None,
                    goals=stats[6] or None if len(stats) > 6 else None,
                    assists=stats[7] or None if len(stats) > 7 else None,
                    market_value=self._grab(r'(?:€|&euro;)\s*([^<\s]+)', row) or None,
                ))
        return players
