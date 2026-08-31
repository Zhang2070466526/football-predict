"""500 彩票网足彩解析器测试 —— 用内联 HTML 片段离线验证，不依赖网络。"""
from __future__ import annotations

from app.core.http import HttpClient
from app.crawler.zucai_500 import Zucai500Crawler

# 从真实页面结构截取的两行比赛（一行有赔率、一行无赔率），用于离线测试
_HTML_FIXTURE = """
<table>
  <tr id="a1420362" status="4" gy="英超,利兹联,布伦特" yy="英超,列斯聯,賓福特" lid="106" fid="1420362" sid="19906">
    <td align="center" class="ssbox_01"><a href="//liansai.500.com/zuqiu-19906/">英超</a></td>
    <td align="center">08-30 21:00</td>
    <td align="right" class="p_lr01"><span class="gray">[10]</span><a target="_blank" href="//liansai.500.com/team/1015/">利兹联</a></td>
    <td align="center"><div class="pk"><a class="clt1">1</a><span>-</span><a class="clt3">1</a></div></td>
    <td align="left" class="p_lr01"><a target="_blank" href="//liansai.500.com/team/1361/">布伦特</a><span class="gray">[06]</span></td>
    <td align="center" class="red">0 - 1</td>
    <td align="center" class="bf_op "><span>2.30</span> <span>3.20</span> <span>2.62</span></td>
  </tr>
  <tr id="a1428463" status="4" gy="德甲,弗赖堡,不来梅" yy="德甲,費雷堡,雲達不萊梅" lid="58" fid="1428463" sid="19951">
    <td align="center" class="ssbox_01"><a href="//liansai.500.com/zuqiu-19951/">德甲</a></td>
    <td align="center">08-31 02:30</td>
    <td align="right" class="p_lr01"><span class="gray">[1]</span><a target="_blank" href="//liansai.500.com/team/2001/">弗赖堡</a></td>
    <td align="center"><div class="pk"><a class="clt1">4</a><span>-</span><a class="clt3">1</a></div></td>
    <td align="left" class="p_lr01"><a target="_blank" href="//liansai.500.com/team/2002/">不来梅</a><span class="gray">[2]</span></td>
    <td align="center" class="red">2 - 0</td>
    <td align="center"></td>
  </tr>
</table>
"""


def _crawler() -> Zucai500Crawler:
    """构造一个不发起真实请求的爬虫实例。"""
    return Zucai500Crawler(HttpClient())


def test_parse_rows_extracts_fields():
    """解析出行数与关键字段。"""
    crawler = _crawler()
    rows = crawler._parse_rows(_HTML_FIXTURE, "26114")
    assert len(rows) == 2

    r = rows[0]
    assert r["match_id"] == "1420362"
    assert r["league"] == "英超"
    assert r["home_team"] == "利兹联"
    assert r["away_team"] == "布伦特"
    assert r["home_team_id"] == "1015"
    assert r["home_goals"] == 1
    assert r["away_goals"] == 1
    assert r["half_home"] == 0
    assert r["half_away"] == 1
    assert r["date"] == "2026-08-30 21:00"  # 期号 26114 -> 2026 年
    assert r["odds"] == [2.30, 3.20, 2.62]


def test_parse_row_without_odds():
    """无赔率的行解析为 odds == []，不抛异常。"""
    crawler = _crawler()
    rows = crawler._parse_rows(_HTML_FIXTURE, "26114")
    assert rows[1]["odds"] == []
    assert rows[1]["home_goals"] == 4
    assert rows[1]["away_goals"] == 1


def test_to_matches_and_odds():
    """解析行正确映射为 Match 与 Odds。"""
    crawler = _crawler()
    rows = crawler._parse_rows(_HTML_FIXTURE, "26114")

    matches = crawler.to_matches(rows)
    assert len(matches) == 2
    assert matches[0].match_id == "1420362"
    assert matches[0].home_team == "利兹联"
    assert matches[0].home_goals == 1

    odds = crawler.to_odds(rows)
    assert len(odds) == 1  # 第二行无赔率，被跳过
    assert odds[0].match_id == "1420362"
    assert odds[0].home_win == 2.30
    assert odds[0].draw == 3.20
    assert odds[0].away_win == 2.62
