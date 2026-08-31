# 数据格式约定

数据放入 `data/` 目录，本项目约定两种数据：**比赛记录**（供预测/统计）和**知识库文本**（供 RAG 问答）。

## 1. 比赛记录（CSV）

用于 `Predictor`（预测）和 `Analyzer`（统计），列名固定如下：

| 列名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `match_id` | int/str | 否 | 比赛唯一 ID |
| `date` | str | 否 | 比赛日期，如 `2024-05-01` |
| `league` | str | 否 | 联赛名，如 `英超` |
| `home_team` | str | 是 | 主队名 |
| `away_team` | str | 是 | 客队名 |
| `home_goals` | int | 是 | 主队进球数 |
| `away_goals` | int | 是 | 客队进球数 |

**样例**（`data/matches.csv`）：

```csv
match_id,date,league,home_team,away_team,home_goals,away_goals
1,2024-05-01,英超,曼城,阿森纳,2,1
2,2024-05-02,英超,利物浦,切尔西,3,1
3,2024-05-03,英超,曼联,热刺,1,1
```

> 预测和统计的 `matches` DataFrame 都依赖这 4 个核心列：
> `home_team / away_team / home_goals / away_goals`。

## 2. 知识库文本（RAG）

导入向量库的文本，可以是任意描述性文本，建议以自然语言段落组织，方便检索。例如：

```text
曼城在 2023-2024 赛季夺得英超冠军，38 轮取得 28 胜 7 平 3 负。
核心球员哈兰德当赛季打进 27 球。
```

也可以是结构化文本：

```text
球队：曼城
联赛：英超
上赛季排名：第 1
主场胜率：78%
```

导入方式：通过 `POST /api/ingest`（`text` 单段文本 + 可选 `source`，自动分块 + MD5 去重），或 Streamlit 页面。

## 3. 数据接入流程

1. 把数据文件放入 `data/` 目录
2. 写一个导入脚本（或调 `/api/ingest`），把数据加载成 `pandas.DataFrame` / 文本列表
3. 文本数据导入向量库 → RAG 问答可用
4. 比赛记录交给 `Predictor` / `Analyzer` → 预测 / 统计可用
