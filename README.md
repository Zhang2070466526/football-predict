# football-predict

足球比赛数据 **采集 + 预测 + 统计分析 + 对话式 agent** 的 Web 服务。

## 功能

| 模块 | 说明 |
|---|---|
| **数据采集** | 爬取 500 彩票网足彩数据：比赛、比分（全场/半场）、胜平负赔率、球队名、球员阵容（含进球/助攻） |
| **比赛预测** | 泊松 Dixon-Coles 模型预测胜平负 / 最可能比分 / 期望进球 / 大小球，支持赔率融合与让球盘 |
| **对话式 agent** | 用自然语言问「谁赢 / 比分」，agent 自动查数据 + 跑模型给出分析（DeepSeek），支持多轮追问 |
| **统计分析** | 积分榜（联赛维度 + 场均进球/失球）、球队统计 |

## 技术栈

- **Web**：FastAPI（后端 API）+ Streamlit（前端界面）
- **预测**：泊松 Dixon-Coles 模型（scipy / numpy）
- **数据**：pandas / numpy / scikit-learn；结构化数据（比赛/赔率/球员）落 SQLite
- **LLM**：DeepSeek（OpenAI 兼容，函数调用）

## 目录结构

```
football-predict/
├── app/
│   ├── main.py                 # FastAPI 入口：装配路由 + main() 启动命令
│   ├── core/                   # 复用基础设施
│   │   ├── config.py           #   Settings 配置单例（读环境变量 / .env）
│   │   └── http.py             #   HttpClient 统一 HTTP 客户端（超时/重试/限流）
│   ├── api/                    # Web 接入层（FastAPI）
│   │   ├── schemas.py          #   Pydantic 请求模型
│   │   └── router.py           #   路由：解析请求并转发业务
│   ├── models/                 # 领域数据模型（爬虫/存储/预测共用）
│   │   ├── match.py            #   Match 比赛记录
│   │   ├── odds.py             #   Odds 赔率（欧赔/亚盘/大小球）
│   │   ├── player.py           #   Player 球员
│   │   └── team_alias.py       #   球队别名映射（简称/全名统一）
│   ├── crawler/                # 数据采集层
│   │   ├── base.py             #   BaseCrawler 采集接口
│   │   ├── zucai_500.py        #   Zucai500Crawler 足彩期号爬虫
│   │   ├── team_resolver.py    #   TeamNameResolver 球队名解析（ID→全名）
│   │   └── team_lineup.py      #   TeamLineupCrawler 阵容爬虫
│   ├── storage/
│   │   └── match_repository.py #   SQLite 仓库（比赛/赔率/球员）
│   ├── predict/                # 比赛预测
│   │   ├── base.py             #   Predictor 预测接口
│   │   └── poisson.py          #   PoissonPredictor 泊松 Dixon-Coles
│   ├── analysis/
│   │   └── analyzer.py         #   Analyzer 球队统计 / 积分榜
│   ├── agent/                  # 对话式预测 agent
│   │   ├── llm.py              #   DeepSeek LLM 客户端（函数调用）
│   │   └── agent.py            #   PredictAgent 工具调用编排
│   └── web/
│       └── app.py              #   Streamlit 前端（4 个 Tab）
├── scripts/
│   ├── crawl_500.py            # 采集比赛数据（按期号）
│   └── crawl_players.py        # 采集球员名单
├── data/                       # 数据目录（运行时生成 football.db）
├── docs/                       # 文档
├── tests/
│   └── test_zucai_500.py       # 解析器离线测试
├── pyproject.toml              # 项目配置与依赖（uv）
└── uv.lock                     # 依赖锁文件
```

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量（复制模板并填写 DeepSeek key）
cp .env.example .env

# 3. 采集数据（足彩期号）
PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_500.py 26114

# 4. 启动后端 API
uv run uvicorn app.main:app --reload --port 8000

# 5. 启动前端界面
uv run streamlit run app/web/app.py
```

## 数据链路

```
500 彩票网足彩页 ──抓取──> SQLite（比赛/赔率/球员）──> 泊松预测 / 统计 / agent
```

- **比赛/赔率**：`Zucai500Crawler` 按期号抓取 → `MatchRepository` 落 SQLite
- **球队名**：`TeamNameResolver` 按球队 ID 抓球队页取全名（缓存 `data/team_names.json`）
- **球员**：`TeamLineupCrawler` 抓各队阵容
- **预测**：`PoissonPredictor` 用历史进球建模，`PredictAgent` 用 DeepSeek 函数调用串起查询+预测

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/api/predict` | 比赛预测（泊松模型） |
| POST | `/api/agent` | 对话式预测 agent |
| GET | `/api/stats?team=X` | 球队统计 |
| GET | `/api/matches` | 全部比赛（含赔率） |
| GET | `/api/table` | 球队积分榜 |
| GET | `/api/players?team=X` | 球员名单 |
| GET | `/api/teams` | 全部球队名 |

**示例**：

```bash
# 比赛预测
curl -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "皇马", "away_team": "巴萨"}'

# 对话式预测
curl -X POST http://127.0.0.1:8000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "预测皇马对巴萨谁赢？"}'
```

## 文档

| 文档 | 功能 |
|---|---|
| [README.md](README.md) | 项目总览：功能、技术栈、目录结构、快速开始、API 速览 |
| [docs/requirements.md](docs/requirements.md) | 需求文档：项目目标、功能/非功能需求、数据需求、里程碑 |
| [docs/data-format.md](docs/data-format.md) | 数据格式约定：比赛记录列名、接入流程 |
| [docs/architecture.md](docs/architecture.md) | 架构设计：分层、模块与文件对照 |
| [docs/api.md](docs/api.md) | API 文档：全部端点请求/响应示例 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录：版本演进与实现记录 |
