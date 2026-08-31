"""LLM 调用封装（DashScope OpenAI 兼容接口），复用统一 HTTP 客户端。"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.http import HttpClient

_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """调用 LLM 返回文本回答。

    参数：
    - messages: [{"role": "system"/"user"/"assistant", "content": "..."}, ...]
    - temperature: 采样温度，越低越确定

    返回：助手回复文本
    """
    s = get_settings()
    if not s.dashscope_api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，请在 .env 中填写")

    headers = {"Authorization": f"Bearer {s.dashscope_api_key}"}
    payload = {"model": s.llm_model, "messages": messages, "temperature": temperature}
    data = HttpClient().post_json(_ENDPOINT, json=payload, headers=headers)
    return data["choices"][0]["message"]["content"]
