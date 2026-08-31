# 架构设计

## 总体

```
Streamlit 前端 ──HTTP──> FastAPI 后端 ──> 预测 / 统计 / agent
                                │
                     ┌──────────┼─────────────┐
                  爬虫(crawler)  存储(storage)    LLM(DeepSeek)
               抓取比赛/赔率/球员 ──落库──> SQLite <──读取──
```

分层：**接入层**（api + web）、**采集层**（crawler）、**存储层**（storage：SQLite）、**业务层**（predict / analysis / agent）。

## 模块与文件对照

| 文件 | 类 / 函数 | 职责 |
|---|---|---|
| `main.py` | `app` / `main()` | FastAPI 装配与启动入口 |
| `core/config.py` | `Settings` / `get_settings()` | 配置单例，读环境变量 |
| `core/http.py` | `HttpClient` | 统一 HTTP 客户端（超时/重试/限流，爬虫与 LLM 复用） |
| `api/schemas.py` | `PredictRequest` 等 | Pydantic 请求模型 |
| `api/router.py` | 路由函数 | 8 个端点，解析请求并转发业务 |
| `models/match.py` | `Match` | 比赛数据模型（含状态/半场比分） |
| `models/odds.py` | `Odds` | 赔率数据模型（欧赔/亚盘/大小球） |
| `models/player.py` | `Player` | 球员数据模型（含出场/进球/助攻） |
| `models/team_alias.py` | `resolve_team()` | 球队别名映射（全名/简称统一） |
| `crawler/base.py` | `BaseCrawler` | 采集接口 `fetch_matches()` |
| `crawler/zucai_500.py` | `Zucai500Crawler` | 足彩期号爬虫（比赛/比分/赔率） |
| `crawler/team_resolver.py` | `TeamNameResolver` | 球队名解析（ID → 完整名，带缓存） |
| `crawler/team_lineup.py` | `TeamLineupCrawler` | 阵容爬虫（球员名单 + 赛季数据） |
| `storage/match_repository.py` | `MatchRepository` | SQLite 仓库：比赛/赔率/球员 |
| `predict/base.py` | `Predictor` | 预测接口（多模型可插拔） |
| `predict/poisson.py` | `PoissonPredictor` | 泊松 Dixon-Coles 模型 + 赔率融合 + 让球 |
| `analysis/analyzer.py` | `Analyzer` | 球队统计 / 积分榜 |
| `agent/llm.py` | `chat()` | DeepSeek LLM 客户端（函数调用） |
| `agent/agent.py` | `PredictAgent` | 对话式预测 agent（工具调用编排） |
| `web/app.py` | Streamlit 页面 | 前端 4 Tab |

## 数据采集与存储

- **比赛/赔率**：`Zucai500Crawler` 按期号抓取 `live.500.com/zucai.php`，解析对阵、全场/半场比分、胜平负赔率、状态，映射为 `Match` + `Odds`。
- **球队名**：`TeamNameResolver` 按球队 ID 抓球队页取完整简体名（缓存 `data/team_names.json`）；`team_alias` 再做简称/全名归一。
- **球员**：`TeamLineupCrawler` 抓球队阵容页，解析球员名单（姓名/号码/位置/国籍/年龄/身高/体重/身价 + 出场/进球/助攻）。
- **存储**：`MatchRepository` 是唯一入口，`load_matches()` 默认排除国家队/世界杯联赛。

## 比赛预测（`app/predict/`）

**当前实现**：`PoissonPredictor`（泊松 Dixon-Coles 模型）——
1. 从历史比赛计算每队攻防强度（场均进球/失球相对联赛均值）；
2. 估计两队期望进球，按泊松分布展开比分概率矩阵（含 Dixon-Coles 低比分修正）；
3. 汇总胜平负概率、期望进球、最可能比分、大小球概率；
4. 支持**赔率融合**（欧赔隐含概率与泊松概率加权）与**让球胜平负**（给定让球数）。

## 对话式 agent（`app/agent/`）

`PredictAgent` 用 DeepSeek 函数调用，把「查数据 + 跑模型」串起来，支持多轮追问。

工具：`list_upcoming_matches`（未来赛事+赔率）、`get_team_stats`（球队统计）、`get_head_to_head`（历史交锋）、`get_team_players`（阵容）、`predict_match`（泊松预测，可带让球/赔率）。

## 统计分析（`app/analysis/`）

`Analyzer` 提供 `team_stats`（场次/胜平负/进球/失球/场均）与 `league_table`（积分榜，含联赛维度、按积分/净胜球排序）。

## 配置（`app/core/config.py`）

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_API_KEY` | — | DeepSeek key（agent 用） |
| `LLM_BASE_URL` | `https://api.deepseek.com` | DeepSeek OpenAI 兼容接口 |
| `LLM_MODEL` | `deepseek-v4-pro` | LLM 模型名 |
| `DATA_DIR` | `./data` | 数据目录 |
| `DB_PATH` | `./data/football.db` | SQLite 落地路径 |
