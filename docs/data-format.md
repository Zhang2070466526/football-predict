# 数据格式约定

数据通过爬虫采集后落 **SQLite**（`data/football.db`），共三张表：比赛、赔率、球员。数据源为 500 彩票网足彩页（`live.500.com/zucai.php?e={期号}`）。

## 1. 比赛表（matches）

| 列名 | 类型 | 说明 |
|---|---|---|
| `match_id` | TEXT | 赛事 ID（500 彩票网 fid，主键） |
| `date` | TEXT | 比赛日期时间，如 `2026-08-30 21:00` |
| `league` | TEXT | 联赛名（如「英超」） |
| `home_team` / `away_team` | TEXT | 主 / 客队名（完整简体名） |
| `home_goals` / `away_goals` | INTEGER | 全场比分（未开赛为 NULL） |
| `home_halftime` / `away_halftime` | INTEGER | 半场比分（可空） |
| `status` | TEXT | 比赛状态（「完场」/「未开赛」/「进行中」） |

> 默认排除国家队/世界杯联赛（世界杯、友谊赛、世外欧洲、世界杯附），只保留俱乐部比赛。

## 2. 赔率表（odds）

| 列名 | 类型 | 说明 |
|---|---|---|
| `match_id` | TEXT | 关联比赛 ID（主键） |
| `home_win` / `draw` / `away_win` | REAL | 欧赔 1X2（主胜 / 平 / 客胜） |
| `over_under` / `asian_handicap` | REAL | 大小球 / 亚盘（预留，暂未采集） |

## 3. 球员表（players）

| 列名 | 类型 | 说明 |
|---|---|---|
| `team_id` / `team_name` | TEXT | 所属球队 ID / 名 |
| `name` | TEXT | 球员姓名 |
| `number` / `position` / `nationality` | TEXT | 号码 / 位置 / 国籍 |
| `age` / `height` / `weight` | TEXT | 年龄 / 身高 / 体重 |
| `market_value` | TEXT | 身价，如「50万」 |
| `appearances` / `goals` / `assists` | TEXT | 出场次数 / 进球 / 助攻 |

## 4. 数据接入流程

1. 采集比赛/赔率：`PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_500.py {期号}`
2. 采集球员：`PYTHONPATH=. ./.venv/Scripts/python.exe scripts/crawl_players.py`
3. 球队名缓存：`data/team_names.json`（team_id → 完整名，`TeamNameResolver` 维护）
