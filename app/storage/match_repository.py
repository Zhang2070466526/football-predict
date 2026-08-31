"""比赛与赔率的 SQLite 持久化仓库 —— 爬虫落库、预测/统计读取的唯一入口。"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd

from app.models.match import Match
from app.models.odds import Odds
from app.models.player import Player

# 国家队/世界杯相关联赛，默认从分析、预测、统计中排除（只保留俱乐部比赛）
NATIONAL_LEAGUES = {"世界杯", "友谊赛", "世外欧洲", "世界杯附"}


class MatchRepository:
    """封装比赛与赔率的 SQLite 存取，对上层隐藏 SQL 细节。

    参数：
    - db_path: SQLite 数据库文件路径；父目录不存在时自动创建
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    # ── 建表 / 连接 ──

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """数据库连接上下文管理器：写入自动 commit、异常回滚、退出必 close。"""
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """建表（幂等）：matches 存比赛、odds 存赔率。"""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    match_id       TEXT PRIMARY KEY,
                    date           TEXT,
                    league         TEXT,
                    home_team      TEXT NOT NULL,
                    away_team      TEXT NOT NULL,
                    home_goals     INTEGER,
                    away_goals     INTEGER,
                    home_halftime  INTEGER,
                    away_halftime  INTEGER,
                    status         TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS odds (
                    match_id        TEXT PRIMARY KEY,
                    home_win        REAL,
                    draw            REAL,
                    away_win        REAL,
                    over_under      REAL,
                    asian_handicap  REAL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    team_id       TEXT NOT NULL,
                    team_name     TEXT NOT NULL,
                    name          TEXT NOT NULL,
                    number        TEXT,
                    position      TEXT,
                    nationality   TEXT,
                    age           TEXT,
                    height        TEXT,
                    weight        TEXT,
                    market_value  TEXT,
                    appearances   TEXT,
                    goals         TEXT,
                    assists       TEXT,
                    PRIMARY KEY (team_id, name)
                )
                """
            )
            # 老库补列（幂等）
            for col in ("appearances", "goals", "assists"):
                try:
                    conn.execute(f"ALTER TABLE players ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    pass

    @staticmethod
    def _ensure_id(match: Match) -> str:
        """为缺失 match_id 的比赛生成稳定 ID（按日期+对阵去重，重复抓取不产生冗余）。"""
        if match.match_id:
            return match.match_id
        key = f"{match.date}|{match.home_team}|{match.away_team}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()[:16]

    # ── 写入 ──

    def save_matches(self, matches: list[Match]) -> int:
        """批量写入比赛（按 match_id 去重，已存在则覆盖）。

        参数：
        - matches: 比赛记录列表

        返回：写入条数
        """
        rows = [
            (self._ensure_id(m), m.date, m.league, m.home_team, m.away_team,
             m.home_goals, m.away_goals, m.home_halftime_goals, m.away_halftime_goals, m.status)
            for m in matches
        ]
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO matches
                    (match_id, date, league, home_team, away_team, home_goals, away_goals,
                     home_halftime, away_halftime, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def save_odds(self, odds: list[Odds]) -> int:
        """批量写入赔率（按 match_id 去重，已存在则覆盖）。

        参数：
        - odds: 赔率记录列表

        返回：写入条数
        """
        rows = [
            (o.match_id, o.home_win, o.draw, o.away_win, o.over_under, o.asian_handicap)
            for o in odds
        ]
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO odds
                    (match_id, home_win, draw, away_win, over_under, asian_handicap)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    # ── 读取 ──

    def load_matches(
        self,
        team: str | None = None,
        limit: int | None = None,
        exclude_national: bool = True,
    ) -> pd.DataFrame:
        """加载比赛为 DataFrame（列与 data-format.md 约定一致）。

        参数：
        - team: 只加载该球队参加的比赛（主或客），None 表示全部
        - limit: 最多返回条数（按 date 倒序取最近），None 表示全部
        - exclude_national: 是否排除国家队/世界杯联赛（默认排除）

        返回：列含 match_id/date/league/home_team/away_team/home_goals/away_goals 等
        """
        sql = (
            "SELECT match_id, date, league, home_team, away_team, home_goals, away_goals, "
            "home_halftime, away_halftime, status FROM matches"
        )
        where: list[str] = []
        params: list = []
        if team:
            where.append("(home_team = ? OR away_team = ?)")
            params += [team, team]
        if exclude_national and NATIONAL_LEAGUES:
            placeholders = ",".join("?" * len(NATIONAL_LEAGUES))
            where.append(f"league NOT IN ({placeholders})")
            params += list(NATIONAL_LEAGUES)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY date DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        with self._conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        # 比分列按整型返回（可空 Int64，未开赛为 None），避免 float 如 5.0
        for col in ("home_goals", "away_goals", "home_halftime", "away_halftime"):
            if col in df.columns:
                df[col] = df[col].astype("Int64")
        return df

    def load_odds(self, match_id: str | None = None) -> pd.DataFrame:
        """加载赔率为 DataFrame。

        参数：
        - match_id: 只加载该场比赛的赔率，None 表示全部
        """
        sql = "SELECT match_id, home_win, draw, away_win, over_under, asian_handicap FROM odds"
        params: list = []
        if match_id:
            sql += " WHERE match_id = ?"
            params.append(match_id)
        with self._conn() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def count(self) -> int:
        """返回已入库的比赛条数。"""
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

    # ── 球员 ──

    def save_players(self, players: list[Player]) -> int:
        """批量写入球员（按 team_id + name 去重，已存在则覆盖）。

        参数：
        - players: 球员列表

        返回：写入条数
        """
        rows = [
            (p.team_id, p.team_name, p.name, p.number, p.position,
             p.nationality, p.age, p.height, p.weight, p.market_value,
             p.appearances, p.goals, p.assists)
            for p in players
        ]
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO players
                    (team_id, team_name, name, number, position,
                     nationality, age, height, weight, market_value, appearances, goals, assists)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def load_players(self, team_name: str | None = None) -> pd.DataFrame:
        """加载球员为 DataFrame。

        参数：
        - team_name: 只加载该队球员，None 表示全部

        返回：列含 team_id/team_name/name/number/position/nationality/age/height/weight/market_value
        """
        sql = (
            "SELECT team_id, team_name, name, number, position, nationality, "
            "age, height, weight, market_value, appearances, goals, assists FROM players"
        )
        params: list = []
        if team_name:
            sql += " WHERE team_name = ?"
            params.append(team_name)
        with self._conn() as conn:
            return pd.read_sql_query(sql, conn, params=params)
