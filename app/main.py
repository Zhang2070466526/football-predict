"""FastAPI 入口 —— 装配路由并启动服务。业务逻辑在 api/router 与各业务模块中。"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.router import router

app = FastAPI(title="football-predict", version="0.1.0")
app.include_router(router)


def main() -> None:
    """命令行入口：启动 uvicorn 服务（供 pyproject 的 script 使用）。"""
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
