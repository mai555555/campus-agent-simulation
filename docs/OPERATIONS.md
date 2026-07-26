# 运维与部署

## 环境变量

`.env.example`:

```dotenv
LLM_API_KEY=你的API_KEY
LLM_API_URL=https://api.tourmaster.ch/v1beta/models/gemini-3.1-flash-lite:generateContent
DATABASE_URL=
ADMIN_TOKEN=本地_admin_token
```

变量说明：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | AI 决策必填 | LLM API Key |
| `LLM_API_URL` | AI 决策必填 | LLM generateContent 风格接口 |
| `DATABASE_URL` | 否 | 设置后使用 PostgreSQL；不设置则使用 SQLite |
| `DB_PATH` | 否 | SQLite 文件路径，默认 `data/city.db` |
| `ADMIN_TOKEN` | 推荐 | World Runtime admin 接口 Bearer token；未设置时本地开发会放行并写 warning |
| `PORT` | 部署时常用 | Uvicorn 监听端口 |

## 初始化策略

项目有两个校园初始化脚本，区别很重要：

| 脚本 | 行为 | 适用场景 |
| --- | --- | --- |
| `python scripts/init_campus_safe.py` | 如果已初始化或已有居民，则跳过种子数据 | 本地日常、持久化数据库、线上启动 |
| `python scripts/init_campus.py` | 清空并重建校园核心数据 | 开发重置、演示环境从零复现 |

`scripts/init_db.py` 是旧城市示例初始化脚本，会写入“虚拟成都”示例居民；当前校园主线通常不应使用它。

## 本地运行

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_campus_safe.py
uvicorn app.main:app --reload
```

默认 SQLite 数据库会创建在 `data/city.db`。`data/` 目录不需要手动创建。

## World Runtime v1

World Runtime v1 让校园世界从“点击模拟一天”升级为后台 tick 驱动。普通用户默认只观察；admin 可以启动、暂停、手动推进 tick 和注入事件。

常用接口：

- `GET /api/world/runtime`：运行状态、世界时间、最新 tick、模型预算。
- `GET /api/world/events?after_id=0&limit=20`：统一实时事件流。
- `POST /api/world/observer-sessions`：记录观察者关注的 Agent 或地点。
- `POST /api/admin/world/start`：启动后台运行。
- `POST /api/admin/world/pause`：暂停后台运行。
- `POST /api/admin/world/tick`：手动推进一个 tick。
- `POST /api/admin/events/trigger`：注入 admin 世界事件。

启动后台运行：

```bash
curl -X POST http://127.0.0.1:8000/api/admin/world/start \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

手动推进一个 tick：

```bash
curl -X POST http://127.0.0.1:8000/api/admin/world/tick \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

前端 admin 控件依赖浏览器本地 token：

```js
localStorage.setItem("ADMIN_TOKEN", "你的_ADMIN_TOKEN")
```

刷新页面后会显示启动、暂停、推进 tick 和旧“模拟一天”调试入口。

v1 的 8 小时行动计划默认使用规则生成，写入 `agent_action_plans`，模型预算和 `model_call_logs` 已接好。后续可以把 planner 从 `rule-based-v1` 替换为批量 LLM planner。

## 重置本地世界

确认需要丢弃当前模拟进度后运行：

```bash
python scripts/init_campus.py
```

该脚本会删除并重建 residents、agent_profiles、relationships、memories、inventory、policies、transactions、city_events、campus_state 等核心数据。

## PostgreSQL

设置 `DATABASE_URL` 后，`app/db.py` 会使用 `psycopg` 连接 PostgreSQL。

示例：

```dotenv
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

如果使用 Supabase，可以直接执行 [`supabase_schema.sql`](supabase_schema.sql) 建表；完整流程见 [`SUPABASE.md`](SUPABASE.md)。

已有 Supabase 项目升级到 World Runtime v1 时，重新执行最新的 [`supabase_schema.sql`](supabase_schema.sql) 即可。所有新增表都使用 `create table if not exists` 和 `create index if not exists`，不会清空已有数据。

项目内的 PostgreSQL 兼容层会处理：

- `?` 参数替换为 `%s`
- `INSERT OR IGNORE` 转为 `ON CONFLICT DO NOTHING`
- `simulation_state` 的 `INSERT OR REPLACE` 转为 upsert
- `PRAGMA table_info(...)` 转为查询 `information_schema.columns`
- `INTEGER PRIMARY KEY AUTOINCREMENT` 转为 `SERIAL PRIMARY KEY`

注意：兼容层覆盖的是当前项目已用 SQL 写法，不等同于完整 SQLite 方言转换器。新增复杂 SQL 时请同时在 SQLite 和 PostgreSQL 下验证。

## Docker

构建：

```bash
docker build -t campus-agent-simulation .
```

运行：

```bash
docker run --rm -p 8000:8000 \
  -e LLM_API_KEY=你的API_KEY \
  -e LLM_API_URL=你的模型接口 \
  campus-agent-simulation
```

当前 Dockerfile 在 build 阶段执行：

```bash
python scripts/init_campus.py
```

这会生成一个全新的校园世界。若要容器启动时连接持久化 PostgreSQL，并避免每次构建重置线上数据，建议将初始化改为启动阶段的 `scripts/init_campus_safe.py`，或由部署平台单独运行一次安全初始化。

## Render

`render.yaml` 当前配置：

```yaml
buildCommand: pip install -r requirements.txt && python scripts/init_campus_safe.py
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

安全初始化会保留已有校园数据，适合当前的持久化部署。首次部署会写入种子数据，后续构建会跳过初始化。

需要配置的环境变量：

- `LLM_API_KEY`
- `LLM_API_URL`
- `DATABASE_URL`，如果使用 Render PostgreSQL

## 外部网络依赖

以下功能依赖外网：

- `/api/campus/environment/sync-real-weather`：Open-Meteo，失败后尝试 Met.no fallback。
- `/api/external-information/sync`：Google News RSS / Bing News RSS。
- 所有 LLM 决策和 AI 日报接口：`LLM_API_URL`。

如果外部天气失败，`auto_update_environment()` 会 fallback 到模拟天气。外部资讯同步失败时接口返回 502。

## 数据表分组

基础世界：

- `residents`
- `agent_profiles`
- `inventory`
- `transactions`
- `relationships`
- `policies`
- `city_events`
- `memories`
- `simulation_state`

校园环境：

- `campus_state`
- `campus_spaces`
- `campus_events`

学习、社交与目标：

- `agent_learning`
- `relationship_dynamics`
- `long_term_goals`
- `group_goals`
- `collaborations`
- `competitions`
- `campus_organizations`
- `organization_members`
- `simulation_action_logs`

日报与资讯：

- `agent_news_posts`
- `external_information`
- `agent_information`

World Runtime：

- `world_runtime`
- `world_ticks`
- `world_event_stream`
- `agent_action_plans`
- `observer_sessions`
- `participant_actions`
- `model_call_logs`

## 常见问题

### `RuntimeError: 缺少 LLM_API_KEY`

`.env` 没有配置 `LLM_API_KEY`。状态查询和手动动作仍可用，但 AI 决策、AI 日报和日记生成需要 LLM。

### 前端显示连接失败

确认后端服务在运行：

```bash
curl http://127.0.0.1:8000/api/state
```

如果 `/api/state` 报数据库表不存在，运行：

```bash
python scripts/init_campus_safe.py
```

### Agent 行动失败

常见原因：

- 精力不足。
- 今日时间预算不足。
- 目标空间关闭、维护中、暂停开放或满员。
- 交易时买方余额不足或卖方库存不足。
- LLM 返回了不符合格式的 JSON。

失败会写入 `city_events`、`memories` 和 `simulation_action_logs`，并消耗失败动作成本。

### PostgreSQL 下某个接口事务异常

PostgreSQL 在单条语句失败后会让当前事务进入 aborted 状态。项目中关键执行路径已经在失败时 `rollback()`，但新增代码如果捕获异常后继续写数据库，也需要先回滚。
