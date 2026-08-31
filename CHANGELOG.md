# Changelog

本文件记录项目的版本演进与每次实现的改动。

## 0.1.0（2026-08-31）—— 项目初始化

### 项目骨架
- 建立项目目录结构（`app/` 分包：rag / predict / analysis / web）
- 配置 `pyproject.toml`（uv 管理，FastAPI + Streamlit + ChromaDB + langchain + DashScope 依赖）
- 环境变量模板 `.env.example`、`.gitignore`

### RAG 模块（`app/rag/`）
- `embeddings.py`：DashScope 文本嵌入
- `vector_store.py`：ChromaDB 封装（增 / 查 / 删 / 清空 / 列来源）
- `llm.py`：LLM 调用（OpenAI 兼容接口）
- `service.py`：查询重写 + 检索 + 上下文 + LLM 生成
- `md5_utils.py`：MD5 去重

### 预测与分析（`app/predict/`、`app/analysis/`）
- `Predictor`：基于历史战绩的启发式预测（留 ML 扩展接口）
- `Analyzer`：球队基础统计（场次 / 胜场 / 进球 / 失球）

### Web 服务
- `main.py`：FastAPI 入口（/health、/api/chat、/api/predict、/api/ingest、/api/stats、/api/docs、/api/sources、/api/clear）
- `web/app.py`：Streamlit 前端（RAG 问答 / 预测 / 统计三个 Tab）

### 文档
- `README.md`、`docs/data-format.md`、`docs/architecture.md`、`docs/requirements.md`

### 复用来源
- 从 `mcp-grpc` 项目的 `servers/knowledge` 模块提炼：文本分块（中文标点分隔符）、查询重写、MD5 去重、向量库管理
