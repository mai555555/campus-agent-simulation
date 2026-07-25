# Supabase 复原数据库

可以。项目现在有一份 Supabase/PostgreSQL 专用结构脚本：

- [`docs/supabase_schema.sql`](supabase_schema.sql)

这份 SQL 覆盖当前代码使用的全部表，并额外写入了 `simulation_state` 初始键和 7 个校园空间。20 个 Agent、初始关系、初始记忆和库存建议继续用项目初始化脚本写入，这样能和代码里的种子数据保持一致。

## 方式一：Supabase SQL Editor 建表

1. 打开 Supabase 项目。
2. 进入 `SQL Editor`。
3. 粘贴并执行 [`docs/supabase_schema.sql`](supabase_schema.sql)。
4. 在本地 `.env` 配置 Supabase 连接串：

```dotenv
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

5. 运行安全初始化，写入 20 个校园 Agent 和初始世界数据：

```bash
python scripts/init_campus_safe.py
```

如果你希望强制重建种子数据，运行：

```bash
python scripts/init_campus.py
```

注意：`init_campus.py` 会清空并重建核心模拟数据。

## 方式二：只配置 DATABASE_URL，让项目初始化

也可以不手动执行 SQL，直接配置 `DATABASE_URL` 后运行：

```bash
python scripts/init_campus_safe.py
```

项目的 PostgreSQL 兼容层会把当前 SQLite 风格 DDL 转成 PostgreSQL 可执行语句。不过如果目标是生产或可审计部署，更推荐先执行 `docs/supabase_schema.sql`，因为它是一份明确、可版本化的 Supabase 结构脚本。

## 为什么 JSON 字段不用 jsonb

当前代码把 `skills`、`strategy`、`schedule`、`perception`、`member_ids`、`effects` 等字段当作 JSON 字符串读写：

```python
json.dumps(...)
json.loads(...)
```

如果在 Supabase 中改成 `jsonb`，`psycopg` 可能直接返回 Python dict/list，部分现有 `json.loads(...)` 调用会收到非字符串对象并报错。因此当前 SQL 保持这些列为 `text`。

## 表结构来源

完整结构来自：

- `app/models.py`：基础世界、居民、记忆、库存、关系、政策、学习、协作和竞争。
- `app/schema.py`：校园环境、空间、校园事件、日报、外部资讯、关系动态、长期目标、群体目标、组织和生命周期日志。

## 当前表清单

- `residents`
- `agent_profiles`
- `inventory`
- `transactions`
- `relationships`
- `policies`
- `city_events`
- `memories`
- `simulation_state`
- `agent_learning`
- `collaborations`
- `competitions`
- `campus_state`
- `campus_spaces`
- `campus_events`
- `agent_news_posts`
- `external_information`
- `agent_information`
- `relationship_dynamics`
- `long_term_goals`
- `group_goals`
- `campus_organizations`
- `organization_members`
- `simulation_action_logs`
