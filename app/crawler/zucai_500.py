"""500 彩票网足彩爬虫 —— 抓取足彩期号页，解析对阵与胜平负赔率。"""
from __future__ import annotations

import re
from typing import Any

from app.core.http import HttpClient
from app.crawler.base import BaseCrawler
from app.models.match import Match
from app.models.odds import Odds

_BASE_URL = "https://live.500.com/zucai.php"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
# 页面声明 charset=gb2312，但实际含 GBK/GB18030 字符，用 gb18030 最稳妥
_ENCODING = "gb18030"
# 比赛状态码 → 中文标签（0=未开赛，4=完场，1/2/3=进行中）
_STATUS_LABELS = {"0": "未开赛", "4": "完场"}


class Zucai500Crawler(BaseCrawler):
    """500 彩票网足彩爬虫。

    抓取 `https://live.500.com/zucai.php?e={期号}` 的静态 HTML（服务端渲染，
    无需 JS 渲染），解析出该期全部比赛的联赛、主客队、全场/半场比分、
    胜平负赔率等信息。

    参数：
    - http: 统一 HTTP 客户端；不传则默认带 1 秒请求间隔（对目标站友好）
    """

    def __init__(self, http: HttpClient | None = None, min_interval: float = 1.0) -> None:
        super().__init__(http or HttpClient(min_interval=min_interval), name="500-zucai")

    # ── 对外接口 ──

    def fetch_period(self, period: str) -> list[dict[str, Any]]:
        """抓取并解析一期，返回该期全部比赛的原始字段字典列表。

        参数：
        - period: 足彩期号，如 "26114"

        返回：每场一个 dict，字段见 _parse_row 的文档
        """
        html = self._fetch_html(period)
        return self._parse_rows(html, period)

    def fetch_matches(
        self,
        period: str | None = None,
        league: str | None = None,
        season: str | None = None,
    ) -> list[Match]:
        """抓取一期并映射为 Match 列表（实现 BaseCrawler 接口）。

        参数：
        - period: 足彩期号（本数据源必填）
        - league / season: 本数据源暂不使用，保留以对齐接口
        """
        rows = self.fetch_period(period or "")
        return self.to_matches(rows)

    def fetch_odds(self, period: str) -> list[Odds]:
        """抓取一期并映射为 Odds 列表（胜平负赔率）。

        参数：
        - period: 足彩期号
        """
        return self.to_odds(self.fetch_period(period))

    # ── 映射（解析行 → 领域模型） ──

    def to_matches(self, rows: list[dict[str, Any]]) -> list[Match]:
        """把解析行映射为 Match 列表，跳过缺失主客队的行。

        参数：
        - rows: fetch_period 返回的原始行列表
        """
        matches: list[Match] = []
        for r in rows:
            if not r.get("home_team") or not r.get("away_team"):
                continue
            matches.append(Match(
                match_id=r.get("match_id"),
                date=r.get("date"),
                league=r.get("league"),
                home_team=r["home_team"],
                away_team=r["away_team"],
                home_goals=r.get("home_goals"),
                away_goals=r.get("away_goals"),
                home_halftime_goals=r.get("half_home"),
                away_halftime_goals=r.get("half_away"),
                status=self._status_label(r.get("status")),
            ))
        return matches

    def to_odds(self, rows: list[dict[str, Any]]) -> list[Odds]:
        """把解析行映射为 Odds 列表，跳过无完整胜平负赔率的行。

        参数：
        - rows: fetch_period 返回的原始行列表
        """
        odds: list[Odds] = []
        for r in rows:
            o = r.get("odds") or []
            if len(o) < 3 or not r.get("match_id"):
                continue
            odds.append(Odds(
                match_id=r["match_id"],
                home_win=o[0],
                draw=o[1],
                away_win=o[2],
            ))
        return odds

    # ── 抓取 ──

    def _build_url(self, period: str) -> str:
        """根据期号构造页面 URL。"""
        return f"{_BASE_URL}?e={period}"

    def _fetch_html(self, period: str) -> str:
        """抓取期号页并按 GB18030 解码为文本。

        参数：
        - period: 足彩期号
        """
        url = self._build_url(period)
        return self._http.get_text(url, headers={"User-Agent": _USER_AGENT}, encoding=_ENCODING)

    # ── 解析 ──

    @staticmethod
    def _grab(pattern: str, text: str, default: str = "") -> str:
        """正则提取第一个分组，失败返回 default。"""
        m = re.search(pattern, text, re.S)
        return m.group(1).strip() if m else default

    @staticmethod
    def _status_label(code: str | None) -> str:
        """状态码转中文标签。"""
        if not code:
            return ""
        return _STATUS_LABELS.get(code, "进行中")

    @staticmethod
    def _grab_int(pattern: str, text: str, default: int | None = None) -> int | None:
        """正则提取第一个分组并转 int，失败返回 default。"""
        m = re.search(pattern, text, re.S)
        if not m:
            return default
        try:
            return int(m.group(1))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _infer_year(period: str) -> int | None:
        """从期号前两位推断年份（如 "26114" -> 2026），失败返回 None。

        500 彩票网足彩期号形如 YYNNN，前两位为年份后两位。
        """
        try:
            return 2000 + int(period[:2])
        except (ValueError, TypeError):
            return None

    def _parse_rows(self, html: str, period: str) -> list[dict[str, Any]]:
        """解析页面中所有比赛行。

        参数：
        - html: 已解码的页面文本
        - period: 期号（用于补齐日期年份）
        """
        rows: list[dict[str, Any]] = []
        # 比赛行的 <tr> 以 id="a{fid}" 标识，据此过滤掉表头等无关行
        for tr in re.findall(r'<tr\s+id="a\d+"[^>]*>.*?</tr>', html, re.S):
            row = self._parse_row(tr, period)
            if row is not None:
                rows.append(row)
        return rows

    def _parse_row(self, tr: str, period: str) -> dict[str, Any] | None:
        """解析单个比赛行。

        返回字段：
        - match_id/league_id/season_id: 赛事/联赛/赛季 ID
        - league: 联赛名
        - home_team/away_team: 主/客队显示名（简体，可能被站点截断）
        - home_team_id/away_team_id: 主/客队 ID（用于后续名字规范化）
        - home_goals/away_goals: 全场比分
        - half_home/half_away: 半场比分
        - date: 比赛日期时间（含推断年份，如 "2026-08-30 21:00"）
        - odds: 胜平负赔率 [主胜, 平, 客胜]，无则 []
        - gy/yy: 原始名称属性（简体/繁体全名），供名字规范化使用
        """
        # 从 <tr> 标签属性取 ID 与名称信息
        fid = self._grab(r'fid="(\d+)"', tr)
        if not fid:
            return None
        lid = self._grab(r'lid="(\d+)"', tr)
        sid = self._grab(r'sid="(\d+)"', tr)
        status = self._grab(r'status="(\d+)"', tr)
        gy = self._grab(r'gy="([^"]*)"', tr)
        yy = self._grab(r'yy="([^"]*)"', tr)

        league = self._grab(r'class="ssbox_01"[^>]*>\s*<a[^>]*>([^<]+)</a>', tr)

        # 主队（align=right 的 p_lr01 单元格）与客队（align=left）
        home_m = re.search(r'align="right"[^>]*class="p_lr01"[^>]*>.*?team/(\d+)/[^"]*"[^>]*>([^<]+)</a>', tr, re.S)
        away_m = re.search(r'align="left"[^>]*class="p_lr01"[^>]*>.*?team/(\d+)/[^"]*"[^>]*>([^<]+)</a>', tr, re.S)
        home_team = home_m.group(2).strip() if home_m else ""
        away_team = away_m.group(2).strip() if away_m else ""
        home_team_id = home_m.group(1) if home_m else ""
        away_team_id = away_m.group(1) if away_m else ""

        # 全场比分在 pk 块内（clt1 = 主，clt3 = 客）；半场比分在 class=red 的 td
        home_goals = self._grab_int(r'class="clt1"[^>]*>\s*(\d+)</a>', tr)
        away_goals = self._grab_int(r'class="clt3"[^>]*>\s*(\d+)</a>', tr)
        half_m = re.search(r'class="red">\s*(\d+)\s*-\s*(\d+)\s*</td>', tr)
        half_home = int(half_m.group(1)) if half_m else None
        half_away = int(half_m.group(2)) if half_m else None

        # 日期：页面只给 "MM-DD HH:MM"，用期号前两位补年份
        date = self._grab(r'<td align="center">(\d{2}-\d{2}\s+\d{2}:\d{2})</td>', tr)
        if date:
            year = self._infer_year(period)
            date = f"{year}-{date}" if year else date

        # 胜平负赔率（部分场次可能缺赔率，容错为空）
        odds: list[float] = []
        odds_m = re.search(
            r'class="bf_op[^"]*">\s*<span>([^<]+)</span>\s*<span>([^<]+)</span>\s*<span>([^<]+)</span>',
            tr,
        )
        if odds_m:
            try:
                odds = [float(x) for x in odds_m.groups()]
            except ValueError:
                odds = []

        return {
            "match_id": fid,
            "league_id": lid,
            "season_id": sid,
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "half_home": half_home,
            "half_away": half_away,
            "date": date,
            "odds": odds,
            "status": status,
            "gy": gy,
            "yy": yy,
        }
