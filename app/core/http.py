"""统一 HTTP 客户端 —— 爬虫与 LLM 共用，内置超时/重试/限流，避免各处重复造轮子。"""
from __future__ import annotations

import time
from typing import Any

import httpx


class HttpClient:
    """轻量 HTTP 客户端：带超时、指数退避重试与请求间隔限流。

    参数：
    - timeout: 单次请求超时秒数
    - max_retries: 失败后最大重试次数（仅对 5xx / 网络错误重试）
    - backoff: 重试间隔基数（指数退避：backoff * 2^n 秒）
    - min_interval: 两次请求最小间隔秒数（限流用，默认 0 不限）
    """

    def __init__(
        self,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 1.0,
        min_interval: float = 0.0,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = backoff
        self._min_interval = min_interval
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        """限流：确保与上一次请求的间隔不小于 min_interval。"""
        if self._min_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """带重试的核心请求逻辑（内部复用，各公开方法都走这里）。"""
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._throttle()
            self._last_request_at = time.monotonic()
            try:
                resp = httpx.request(method, url, timeout=self._timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                # 4xx 属于请求本身错误，重试无意义，直接抛出
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                if attempt < self._max_retries:
                    time.sleep(self._backoff * (2 ** attempt))
        raise last_exc if last_exc is not None else RuntimeError("HTTP 请求失败")

    def get_json(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> dict:
        """GET 并解析 JSON 响应为 dict。"""
        return self._request("GET", url, params=params, headers=headers).json()

    def post_json(self, url: str, *, json: Any = None, headers: dict | None = None) -> dict:
        """POST JSON 并解析响应为 dict。"""
        return self._request("POST", url, json=json, headers=headers).json()

    def get_text(self, url: str, *, params: dict | None = None, headers: dict | None = None) -> str:
        """GET 并返回纯文本响应（用于抓取 HTML 页面）。"""
        return self._request("GET", url, params=params, headers=headers).text