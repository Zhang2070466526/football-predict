"""LLM 调用封装（DeepSeek OpenAI 兼容接口），支持函数调用。"""
from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.http import HttpClient


def chat(messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.3) -> dict[str, Any]:
    """调用 LLM，返回完整响应 dict。

    参数：
    - messages: 对话消息列表 [{"role": ..., "content": ...}]
    - tools: 函数调用工具定义（OpenAI 格式），None 表示纯对话
    - temperature: 采样温度

    返回：完整响应，含 choices[0].message 的 content 与 tool_calls
    """
    s = get_settings()
    if not s.llm_api_key:
        raise RuntimeError("未配置 LLM_API_KEY，请在 .env 中填写")

    url = f"{s.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {s.llm_api_key}"}
    payload = {"model": s.llm_model, "messages": messages, "temperature": temperature}
    if tools:
        payload["tools"] = tools
    return HttpClient().post_json(url, json=payload, headers=headers)
