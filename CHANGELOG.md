# Changelog

本文件记录项目的版本演进与每次实现的改动。

## 0.3.0（2026-08-31）—— 预测模型 + 对话式 agent

### 预测模型（`app/predict/`）
- `poisson.py`：`PoissonPredictor` 泊松 Dixon-Coles 模型（攻防强度 → 期望进球 → 比分矩阵 → 胜平负/最可能比分/大小球）
- 赔率融合：欧赔隐含概率与泊松概率加权平均
- 让球胜平负：`handicap` 参数，从比分矩阵算让球盘结果

### 对话式 agent（`app/agent/`）
- `llm.py`：DeepSeek OpenAI 兼容客户端（函数调用）
- `agent.py`：`PredictAgent` 工具调用编排（查赛事/统计/交锋/阵容/预测），支持多轮追问

### 数据扩展
- 未来赛事（未开赛 status=0）、半场比分、总进球、场均进球/失球
- 球队名规范化（`TeamNameResolver` ID→全名）+ 别名映射（`team_alias.py`）
- 球员阵容采集（`TeamLineupCrawler`）+ 出场/进球/助攻
- 排除国家队/世界杯联赛（`NATIONAL_LEAGUES`）

### 精简
- 移除 RAG 模块、`HeuristicPredictor`、`MockCrawler`、`logging.py`（冗余/被取代）
- 前端 4 Tab（数据总览 / 智能预测 / 球员阵容 / 统计分析），聊天界面

### 修复
- 比分列改为整型（可空 Int64）

## 0.2.0（2026-08-31）—— 数据源接入：500 彩票网足彩爬虫

### 数据源
- 确定数据源：500 彩票网足彩比分直播 `live.500.com/zucai.php?e={期号}`（静态服务端渲染 HTML，GBK 编码，普通 GET 即可）
- 覆盖欧洲五大联赛，每场含胜平负赔率（欧赔 1X2）

### 爬虫模块（`app/crawler/`）
- `zucai_500.py`：`Zucai500Crawler` —— 抓取期号页、GB18030 解码、解析对阵/全场/半场比分/赔率，映射为 `Match` + `Odds`
- `base.py`：`fetch_matches` 增加 `period` 参数（对齐期号型数据源）
- `core/http.py`：`get_text` 增加 `encoding` 参数（支持 GBK 等中文编码）

### 脚本与测试
- `scripts/crawl_500.py`：按期号抓取并落库 SQLite
- `tests/test_zucai_500.py`：解析器离线测试（内联 HTML，不依赖网络）

### 已知待办
- 球队名被站点截断（如「布伦特」= 布伦特福德），`yy` 属性含繁体全名、球队 ID 已提取，待做名字规范化
- 亚盘/大小球在二级页（`odds.500.com/fenxi/yazhi-{fid}.shtml`），待抓取

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
