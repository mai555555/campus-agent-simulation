# API 速查

默认服务地址：`http://127.0.0.1:8000`

完整交互式文档可打开 `/docs`。本文只记录维护和调试最常用的接口。

## 页面与健康检查

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/` | 返回静态前端页面 |
| GET | `/api/ai/test` | 调用一次 LLM，验证 `LLM_API_KEY` 和 `LLM_API_URL` |

## 世界状态

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/state` | 世界总快照：天数、环境、空间、Agent、事件、六模块状态 |
| GET | `/api/agents` | Agent 列表 |
| GET | `/api/residents` | 同 `/api/agents` |
| GET | `/api/agents/modules` | 所有 Agent 六模块状态 |
| GET | `/api/agents/{resident_id}/modules` | 单个 Agent 六模块状态 |
| GET | `/api/inventory` | 全部库存 |

## 校园环境与空间

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/campus/environment/today` | 今日校园环境 |
| POST | `/api/campus/environment/set` | 手动更新今日环境字段 |
| POST | `/api/campus/environment/sync-real-time` | 根据系统时间更新学期、时段和人流 |
| POST | `/api/campus/environment/sync-real-weather` | 调用天气 API 并更新校园环境 |
| GET | `/api/campus/spaces` | 校园空间快照 |
| POST | `/api/campus/spaces/{location}/status` | 手动调整空间状态 |
| POST | `/api/campus/events/trigger` | 触发校园事件 |
| POST | `/api/campus/events/{event_id}/resolve` | 结束校园事件 |

示例：设置环境。

```bash
curl -X POST http://127.0.0.1:8000/api/campus/environment/set \
  -H 'Content-Type: application/json' \
  -d '{"weather":"小雨","rainfall":45,"exam_pressure":70,"campus_mood":"紧张"}'
```

示例：触发空间事件。

```bash
curl -X POST http://127.0.0.1:8000/api/campus/events/trigger \
  -H 'Content-Type: application/json' \
  -d '{"title":"图书馆设备检修","event_type":"设施故障","intensity":60,"target_spaces":["图书馆"]}'
```

## 手动行动工具

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/api/tools/move` | 移动 Agent |
| POST | `/api/tools/chat` | 让两个 Agent 聊天 |
| POST | `/api/tools/buy-sell` | 完成交易 |
| POST | `/api/tools/submit-policy` | 提交校园政策 |
| POST | `/api/tools/vote-policy` | 对政策投票 |
| POST | `/api/tools/close-policy/{policy_id}` | 结算政策 |
| POST | `/api/tools/daily-reflect` | 让所有 Agent 写一句当天总结 |

示例：移动。

```bash
curl -X POST http://127.0.0.1:8000/api/tools/move \
  -H 'Content-Type: application/json' \
  -d '{"resident_id":1,"destination":"图书馆"}'
```

示例：聊天。

```bash
curl -X POST http://127.0.0.1:8000/api/tools/chat \
  -H 'Content-Type: application/json' \
  -d '{"speaker_id":1,"listener_id":11,"message":"今天一起去社团招新看看吗？"}'
```

示例：交易。

```bash
curl -X POST http://127.0.0.1:8000/api/tools/buy-sell \
  -H 'Content-Type: application/json' \
  -d '{"buyer_id":1,"seller_id":5,"item_name":"套餐饭","quantity":1,"unit_price":12}'
```

## 自主模拟

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/api/agent/decide/{resident_id}` | 只生成单个 Agent 决策 |
| POST | `/api/agent/act/{resident_id}` | 决策并执行单个 Agent 行动 |
| POST | `/api/agent/act-all` | 所有 Agent 轮流决策并执行 |
| POST | `/api/simulate/lifecycle-step/{resident_id}` | 单个 Agent 完整生命周期 |
| POST | `/api/simulate/lifecycle-round` | 所有 Agent 完整生命周期，不推进天数 |
| POST | `/api/simulate/ai-day` | 推进到下一天，更新环境，所有 Agent 行动，发布日报 |

最常用的是：

```bash
curl -X POST http://127.0.0.1:8000/api/simulate/ai-day
```

## 社交、目标与组织

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/social/hierarchy` | 按层级查看 Agent |
| POST | `/api/social/communicate` | 社交沟通，底层等价于聊天并记录学习 |
| POST | `/api/social/negotiate` | 协商 |
| POST | `/api/social/collaborate` | 发起协作 |
| POST | `/api/social/compete` | 发起竞争 |
| GET | `/api/social/relationships/{resident_id}` | 关系列表与关系动态 |
| GET | `/api/agents/{resident_id}/social-graph` | 前端人物页使用的关系图 |
| GET | `/api/agents/{resident_id}/learning` | 学习记录 |
| GET | `/api/agents/{resident_id}/long-term-goals` | 长期目标 |
| POST | `/api/goals` | 创建长期目标 |
| GET | `/api/organizations` | 校园组织 |
| GET | `/api/groups` | 群体目标 |
| POST | `/api/groups` | 创建群体目标 |

## 记忆、时间线与日志

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/agents/{resident_id}/memories/relevant?query=图书馆,考试` | 按相关性检索个人记忆 |
| GET | `/api/agents/{resident_id}/timeline?limit=30` | 简化行动时间线 |
| GET | `/api/agents/{resident_id}/simulation-logs?limit=12` | 完整感知、记忆、决策、执行和反馈日志 |

## 日报与外部资讯

| Method | Path | 说明 |
| --- | --- | --- |
| GET | `/api/newspaper/today` | 当日事件和 Agent 状态数据 |
| GET | `/api/newspaper/agent-posts` | Agent 自主投稿 |
| GET | `/api/newspaper/ai-today` | 调用 LLM 生成校园日报 |
| POST | `/api/agents/daily-diaries/backfill` | 为指定日期补写 Agent 日记 |
| POST | `/api/external-information/sync` | 从固定 RSS 源同步外部资讯 |
| GET | `/api/external-information` | 查看已同步资讯 |

## 常见请求体

`CampusEnvironmentRequest` 支持的字段来自 `DEFAULT_ENV`，包括 `weather`、`semester_stage`、`time_slot`、`weekday`、`temperature`、`rainfall`、`exam_pressure`、`assignment_pressure`、`study_atmosphere`、`activity_heat`、各空间 crowd、`traffic_status`、`network_status`、`safety_level`、`resource_pressure`、`campus_mood`、`consumption_index` 等。

`CampusEventRequest`：

```json
{
  "title": "校园主题活动",
  "event_type": "大型活动",
  "intensity": 60,
  "target_spaces": ["操场", "教学楼"],
  "effects": {}
}
```

`GroupGoalRequest`：

```json
{
  "name": "图书馆复习互助组",
  "group_type": "学习小组",
  "leader_id": 2,
  "member_ids": [13, 16],
  "shared_goal": "一起完成期末复习计划",
  "current_plan": "每天晚间同步复习进度"
}
```
