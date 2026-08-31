"""爬虫基类 —— 定义统一的采集接口，各数据源继承实现。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.http import HttpClient
from app.models.match import Match


class BaseCrawler(ABC):
    """爬虫抽象基类：所有数据源实现统一接口，便于存储/预测层无差别调用。

    参数：
    - http: 统一 HTTP 客户端（复用超时/重试/限流）
    - name: 数据源名称，用于日志与来源标注
    """

    def __init__(self, http: HttpClient, name: str) -> None:
        self._http = http
        self.name = name

    @abstractmethod
    def fetch_matches(
        self,
        period: str | None = None,
        league: str | None = None,
        season: str | None = None,
    ) -> list[Match]:
        """抓取比赛记录。

        参数（各数据源按需使用，含义见具体实现）：
        - period: 期号（如 500 彩票网足彩期号）
        - league: 联赛名过滤，None 表示全部
        - season: 赛季过滤，None 表示全部

        返回：比赛记录列表
        """
        raise NotImplementedError
