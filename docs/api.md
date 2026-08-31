# API 文档

FastAPI 后端默认运行在 `http://127.0.0.1:8000`。

## 1. 健康检查

`GET /health`

```json
{"status": "ok"}
```

## 2. RAG 问答

`POST /api/chat`

请求：

```json
{"question": "上赛季谁夺冠了？", "k": 4}
```

响应：

```json
{
  "answer": "根据检索上下文，曼城夺得 2023-2024 赛季英超冠军。",
  "sources": [
    {"content": "曼城在 2023-2024 赛季...", "metadata": {"source": "曼城"}, "score": 0.42}
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `question` | str | 用户问题（必填） |
| `k` | int | 检索片段数，默认 4 |

## 3. 比赛预测

`POST /api/predict`

请求：

```json
{"home_team": "曼城", "away_team": "阿森纳"}
```

响应：

```json
{
  "home_team": "曼城",
  "away_team": "阿森纳",
  "home_win_prob": 0.6,
  "draw_prob": 0.24,
  "away_win_prob": 0.16,
  "prediction": "主队胜"
}
```

## 4. 数据导入

`POST /api/ingest`

请求：

```json
{"text": "曼城上赛季 28 胜 7 平 3 负...", "source": "曼城"}
```

响应：

```json
{"success": true, "chunks_count": 3, "message": "已导入 \"曼城\"，3 个分块"}
```

- 文本会自动分块 + MD5 去重；重复导入返回 `success: false`。

## 5. 球队统计

`GET /api/stats?team=曼城`

响应：

```json
{
  "team": "曼城",
  "stats": {"played": 38, "wins": 28, "scored": 96, "conceded": 34, "goal_diff": 62}
}
```

## 6. 向量库信息

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/docs` | 返回 `{"documents": N}`（文档数） |
| GET | `/api/sources` | 返回 `{"sources": [...]}`（已导入来源） |
| DELETE | `/api/clear` | 清空向量库，返回 `{"success": true}` |
