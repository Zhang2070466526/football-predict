"""球队名解析器 —— 按球队 ID 抓取球队页，把截断队名补全为完整简体名。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.core.http import HttpClient

_TEAM_URL = "https://liansai.500.com/team/{team_id}/"
_ENCODING = "gb18030"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class TeamNameResolver:
    """按球队 ID 解析完整队名，结果缓存到本地 JSON，避免重复抓取。

    参数：
    - http: 统一 HTTP 客户端（复用超时/限流）
    - cache_path: 缓存文件路径，内容为 {team_id: 完整队名}
    """

    def __init__(self, http: HttpClient, cache_path: str) -> None:
        self._http = http
        self._cache_path = cache_path
        self._cache = self._load_cache()

    def resolve(self, team_id: str) -> str | None:
        """返回 team_id 对应的完整队名；缓存命中直接返回，否则抓取球队页。

        参数：
        - team_id: 球队 ID（如 "1361"）

        返回：完整队名；抓取失败返回 None（调用方回退到原始显示名）
        """
        if not team_id:
            return None
        if team_id in self._cache:
            return self._cache[team_id]
        name = self._fetch_full_name(team_id)
        if name:
            self._cache[team_id] = name
            self._save_cache()
        return name

    # ── 缓存读写 ──

    def _load_cache(self) -> dict[str, str]:
        """从本地 JSON 读取缓存；不存在或损坏则返回空 dict。"""
        try:
            return json.loads(Path(self._cache_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_cache(self) -> None:
        """把缓存写回本地 JSON。"""
        path = Path(self._cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── 抓取 ──

    def _fetch_full_name(self, team_id: str) -> str | None:
        """抓取球队页，从 <title> 提取完整队名。

        例：<title>布伦特福德赛程_布伦特福德阵容_...</title> → "布伦特福德"
        """
        url = _TEAM_URL.format(team_id=team_id)
        try:
            html = self._http.get_text(url, headers={"User-Agent": _USER_AGENT}, encoding=_ENCODING)
            m = re.search(r'<title>([^_<]+)', html)
            name = m.group(1).strip() if m else None
            # <title> 形如「布伦特福德赛程_布伦特福德阵容_...」，去掉末尾的「赛程」
            return name.removesuffix("赛程") if name else None
        except Exception:
            return None
