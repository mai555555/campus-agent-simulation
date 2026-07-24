# 运维与部署

## 环境变量

`.env.example`:

```dotenv
LLM_API_KEY=你的API_KEY
LLM_API_URL=https://api.tourmaster.ch/v1beta/models/gemini-3.1-flash-lite:generateContent
DATABASE_URL=
```

变量说明：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | AI 决策必填 | LLM API Key |
| `LLM_API_URL` | AI 决策必填 | LLM generateContent 风格接口 |
| `DATABASE_URL` | 否 | 设置后使用 PostgreSQL；不设置则使用 SQLite |
| `DB_PATH` | 否 | SQLite 文件路径，默认 `data/city.db` |
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
buildCommand: pip install -r requirements.txt && python scripts/init_campus.py
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

这适合每次构建获得干净演示数据。若使用持久化 PostgreSQL，建议把 buildCommand 调整为只安装依赖，并在首次部署或 release 阶段运行安全初始化。

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
