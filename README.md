# football-predict

足球数据 **RAG 知识库 + 比赛预测 + 统计分析** 的 Web 服务。

## 功能

| 模块 | 说明 |
|---|---|
| **RAG 问答** | 用自然语言查询球队/球员/历史数据，检索增强生成回答 |
| **比赛预测** | 基于历史数据预测胜平负 / 比分 / 进球数 |
| **统计分析** | 球队/联赛的统计指标与报表 |

## 技术栈

- **Web**：FastAPI（后端 API）+ Streamlit（前端界面）
- **RAG**：ChromaDB（向量库）+ DashScope 嵌入 + OpenAI 兼容 LLM
- **数据**：pandas / numpy / scikit-learn；结构化数据（比赛/赔率）落 SQLite，文本知识落 ChromaDB

## 目录结构

```
football-predict/
├── app/
│   ├── __init__.py             # 包说明
│   ├── main.py                 # FastAPI 入口：装配路由 + main() 启动命令
│   ├── core/                   # 复用基础设施（跨模块共享）
│   │   ├── config.py           #   Settings 配置单例（读环境变量 / .env）
│   │   ├── http.py             #   HttpClient 统一 HTTP 客户端（超时/重试/限流）
│   │   └── logging.py          #   setup_logging 日志配置
│   ├── api/                    # Web 接入层（FastAPI）
│   │   ├── schemas.py          #   Pydantic 请求模型（Chat/Predict/Ingest）
│   │   └── router.py           #   路由：8 个端点，解析请求并转发业务
│   ├── models/                 # 领域数据模型（爬虫/存储/预测共用）
│   │   ├── match.py            #   Match 比赛记录
│   │   └── odds.py             #   Odds 赔率（欧赔/亚盘/大小球）
│   ├── crawler/                # 数据采集层（最高优先级）
│   │   ├── base.py             #   BaseCrawler 采集接口（fetch_matches）
│   │   └── mock_crawler.py     #   MockCrawler 模拟源（验证链路用）
│   ├── storage/                # 数据持久化层
│   │   └── match_repository.py #   MatchRepository SQLite 仓库（存/取比赛与赔率）
│   ├── predict/                # 比赛预测
│   │   ├── base.py             #   Predictor 预测接口（多模型可插拔）
│   │   └── heuristic.py        #   HeuristicPredictor 启发式预测
│   ├── analysis/               # 统计分析与报表
│   │   └── analyzer.py         #   Analyzer 球队统计（team_stats / league_table）
│   ├── rag/                    # RAG 知识库问答
│   │   ├── embeddings.py       #   DashScope 文本嵌入
│   │   ├── vector_store.py     #   VectorStore ChromaDB 封装
│   │   ├── llm.py              #   chat() LLM 调用（OpenAI 兼容）
│   │   ├── md5_utils.py        #   MD5 去重工具
│   │   └── rag_service.py      #   RagService 问答 + 导入
│   └── web/                    # Streamlit 前端
│       └── app.py              #   三个 Tab：问答 / 预测 / 统计
├── scripts/
│   └── seed_demo.py            # 演示脚本：跑通「抓取→落库→预测→统计」
├── data/                       # 数据目录（运行时生成 football.db）
├── docs/                       # 文档
├── tests/
│   └── test_chain.py           # 全链路冒烟测试
├── pyproject.toml              # 项目配置与依赖（uv）
└── uv.lock                     # 依赖锁文件
```

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量（复制模板并填写 DashScope key）
cp .env.example .env

# 3. 启动后端 API
uv run uvicorn app.main:app --reload --port 8000

# 4. 启动前端界面
uv run streamlit run app/web/app.py
```

## 数据接入（后补）

两条数据链路（来源待定，当前以 MockCrawler 演示）：
1. **结构化比赛/赔率** → 爬虫抓取 → `MatchRepository` 落 SQLite → 预测/统计读取
2. **文本知识** → `/api/ingest` 导入 → ChromaDB 向量库 → RAG 问答

> 数据格式约定（比赛记录列名、知识库文本格式）见 [docs/data-format.md](docs/data-format.md)。

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/api/chat` | RAG 问答 |
| POST | `/api/predict` | 比赛预测 |
| POST | `/api/ingest` | 导入文本到向量库（自动分块 + MD5 去重） |
| GET | `/api/stats` | 球队统计 |
| GET | `/api/docs` | 向量库文档数 |
| GET | `/api/sources` | 已导入的文档来源 |
| DELETE | `/api/clear` | 清空向量库 |

**示例**：

```bash
# RAG 问答
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "上赛季谁夺冠了？"}'

# 比赛预测
curl -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "曼城", "away_team": "阿森纳"}'
```

## 文档

| 文档 | 功能 |
|---|---|
| [README.md](README.md) | 项目总览：功能、技术栈、目录结构、快速开始、API 速览 |
| [docs/requirements.md](docs/requirements.md) | 需求文档：项目目标、功能/非功能需求、数据需求、里程碑 |
| [docs/data-format.md](docs/data-format.md) | 数据格式约定：比赛记录列名、知识库文本格式、接入流程 |
| [docs/architecture.md](docs/architecture.md) | 架构设计：分层、模块与文件对照、RAG/预测/统计现状与扩展 |
| [docs/api.md](docs/api.md) | API 文档：全部端点请求/响应示例 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录：版本演进与实现记录 |
