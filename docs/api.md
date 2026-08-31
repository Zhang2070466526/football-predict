# API 文档

FastAPI 后端默认运行在 `http://127.0.0.1:8000`。

## 1. 健康检查

`GET /health`

```json
{"status": "ok"}
```

## 2. 比赛预测

`POST /api/predict`

请求：

```json
{"home_team": "皇马", "away_team": "巴萨", "handicap": 1.0}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `home_team` / `away_team` | str | 主 / 客队名（支持简称，自动归一） |
| `handicap` | float | 让球数（主队让几球），可选 |
| `odds` | [float, float, float] | 欧赔 [主胜, 平, 客胜]，可选，用于赔率融合 |

响应：

```json
{
  "home_team": "皇马", "away_team": "巴萨",
  "home_win_prob": 0.33, "draw_prob": 0.271, "away_win_prob": 0.399,
  "expected_home_goals": 1.23, "expected_away_goals": 1.66,
  "most_likely_score": "1-1", "over_2_5_prob": 0.551,
  "prediction": "客队胜",
  "handicap": 1.0,
  "handicap_home_win": 0.117, "handicap_draw": 0.158, "handicap_away_win": 0.725,
  "handicap_prediction": "客队胜"
}
```

## 3. 对话式预测 agent

`POST /api/agent`

请求：

```json
{"question": "预测皇马 vs 巴萨谁赢？", "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `question` | str | 当前问题 |
| `history` | list[dict] | 历史对话，用于多轮追问，可选 |

响应：

```json
{"answer": "皇马胜 44% / 平 27% / 巴萨胜 29%，最可能比分 1-1 …"}
```

## 4. 球队统计

`GET /api/stats?team=皇马`

```json
{"team": "皇马", "stats": {"played": 11, "wins": 6, "scored": 22, "conceded": 10, "goal_diff": 12, "avg_scored": 2.0, "avg_conceded": 0.91}}
```

## 5. 数据列表

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/matches` | 全部比赛（含赔率、半场比分、状态） |
| GET | `/api/table` | 球队积分榜（含联赛维度、场均进球/失球） |
| GET | `/api/players?team=X` | 球员名单（含进球/助攻/出场） |
| GET | `/api/teams` | 全部球队名 |
