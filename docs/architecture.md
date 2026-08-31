# 架构设计

## 总体

```
Streamlit 前端 ──HTTP──> FastAPI 后端 ──> 预测 / 分析 / RAG
                                │
        ┌───────────────────────┼────────────────────────┐
     爬虫(crawler)          存储(storage)          ChromaDB(向量库)
    抓取比赛/赔率     ──落库──> SQLite(比赛/赔率) <──读取──  文本知识(RAG)
```

四层：**接入层**（api + web）、**采集层**（crawler）、**存储层**（storage：SQLite + ChromaDB）、**业务层**（predict / analysis / rag）。

> 数据职责划分：结构化比赛/赔率存 **SQLite**（需按球队/日期/赔率做关系查询与聚合），
> 文本知识存 **ChromaDB**（需语义相似检索）。两者各司其职，不混用。

## 模块与文件对照

| 文件 | 类 / 函数 | 职责 |
|---|---|---|
| `main.py` | `app` / `main()` | FastAPI 装配与启动入口 |
| `core/config.py` | `Settings` / `get_settings()` | 配置单例，读环境变量 |
| `core/http.py` | `HttpClient` | 统一 HTTP 客户端（超时/重试/限流，爬虫与 LLM 复用） |
| `core/logging.py` | `setup_logging()` | 日志配置 |
| `api/schemas.py` | `ChatRequest` 等 | Pydantic 请求模型 |
| `api/router.py` | 路由函数 | 8 个端点，解析请求并转发业务 |
| `models/match.py` | `Match` | 比赛数据模型 |
| `models/odds.py` | `Odds` | 赔率数据模型（欧赔/亚盘/大小球） |
| `crawler/base.py` | `BaseCrawler` | 采集接口 `fetch_matches()` |
| `crawler/mock_crawler.py` | `MockCrawler` | 模拟数据源（验证链路） |
| `storage/match_repository.py` | `MatchRepository` | SQLite 仓库：存/取比赛与赔率 |
| `predict/base.py` | `Predictor` | 预测接口（多模型可插拔） |
| `predict/heuristic.py` | `HeuristicPredictor` | 启发式预测 |
| `analysis/analyzer.py` | `Analyzer` | 球队统计 / 积分榜 |
| `rag/embeddings.py` | `get_embeddings()` | DashScope 文本嵌入 |
| `rag/vector_store.py` | `VectorStore` | ChromaDB 封装 |
| `rag/llm.py` | `chat()` | LLM 调用（OpenAI 兼容） |
| `rag/md5_utils.py` | MD5 工具函数 | 去重记录 |
| `rag/rag_service.py` | `RagService` | RAG 问答 + 导入 |
| `web/app.py` | Streamlit 页面 | 前端三 Tab |

## 数据采集与存储（`app/crawler/` + `app/storage/`）

**采集**：`BaseCrawler`（`crawler/base.py`）定义统一接口 `fetch_matches()`，各数据源继承实现；
真实来源待确定后放入 `crawler/sources/`，当前以 `MockCrawler` 跑通链路。

**存储**：`MatchRepository`（`storage/match_repository.py`）是结构化数据的唯一入口，
预测/统计通过 `load_matches()` 读取，爬虫通过 `save_matches()` / `save_odds()` 落库。

**链路**：`爬虫 fetch → 存储 save → 业务 load → 预测/统计`，各层职责单一、可替换。

## RAG 链路（`app/rag/`）

**写入**：文本 → DashScope 嵌入 → ChromaDB 持久化

**查询**：

```
question
  → VectorStore.search() 检索 top-k 相似片段
  → 拼接成上下文
  → LLM（DashScope OpenAI 兼容接口）基于上下文生成回答
  → 返回 {answer, sources}
```

| 模块 | 职责 |
|---|---|
| `embeddings.py` | DashScope 文本嵌入 |
| `vector_store.py` | ChromaDB 封装（添加 / 检索 / 计数） |
| `llm.py` | LLM 调用（OpenAI 兼容 `/chat/completions`） |
| `rag_service.py` | `RagService`：检索 + 上下文 + 生成，对外统一入口 |

## 比赛预测（`app/predict/`）

**当前实现**：基于历史战绩的启发式（主队历史胜率 vs 客队历史失利率，粗略估算三类概率）。

**后续扩展方向**（`base.py` 已留接口）：
- 泊松模型（进球数建模）
- 逻辑回归 / 梯度提升（特征：近期状态、主客场、历史交锋）
- 引入 Elo 评分 / 球员伤停等特征

## 统计分析（`app/analysis/`）

**当前实现**：球队基础统计（场次 / 胜场 / 进球 / 失球 / 净胜球）。

**后续扩展方向**：
- 联赛积分榜（`league_table` 已留占位）
- 进球效率、趋势、主客场对比

## 配置（`app/core/config.py`）

所有环境变量收敛到 `Settings` dataclass（frozen + lru_cache 单例），`.env` 通过 `python-dotenv` 加载。

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `DASHSCOPE_API_KEY` | — | DashScope key（必填） |
| `EMBEDDING_MODEL` | `text-embedding-v2` | 嵌入模型 |
| `LLM_MODEL` | `qwen-plus` | LLM 模型 |
| `CHROMA_DIR` | `./chroma_data` | 向量库持久化目录 |
| `DATA_DIR` | `./data` | 数据目录 |
| `DB_PATH` | `./data/football.db` | SQLite 结构化数据（比赛/赔率）落地路径 |
