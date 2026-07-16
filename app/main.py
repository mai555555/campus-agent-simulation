import json
import random
import re
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection
from services.llm_service import ask_llm
from tools.city_tools import (
    VALID_LOCATIONS,
    add_event,
    add_memory,
    buy_sell,
    chat_between,
    get_current_day,
    get_resident,
    move_resident,
)

app = FastAPI(title="校园封闭世界 AI-Agent 沙盘系统", version="0.2.0")

CAMPUS_STATE_SQL = """
CREATE TABLE IF NOT EXISTS campus_state (
    day INTEGER PRIMARY KEY,
    weather TEXT NOT NULL DEFAULT '晴',
    semester_stage TEXT NOT NULL DEFAULT '平时周',
    exam_pressure INTEGER NOT NULL DEFAULT 35,
    activity_heat INTEGER NOT NULL DEFAULT 50,
    campus_flow INTEGER NOT NULL DEFAULT 55,
    canteen_crowd INTEGER NOT NULL DEFAULT 50,
    library_crowd INTEGER NOT NULL DEFAULT 45,
    traffic_status TEXT NOT NULL DEFAULT '正常',
    campus_mood TEXT NOT NULL DEFAULT '平稳',
    consumption_index REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DEFAULT_ENV = {
    "weather": "晴",
    "semester_stage": "平时周",
    "exam_pressure": 35,
    "activity_heat": 50,
    "campus_flow": 55,
    "canteen_crowd": 50,
    "library_crowd": 45,
    "traffic_status": "正常",
    "campus_mood": "平稳",
    "consumption_index": 1.0,
}

AGENT_PROFILE_SQL = """
CREATE TABLE IF NOT EXISTS agent_profiles (
    resident_id INTEGER PRIMARY KEY,
    gender TEXT NOT NULL,
    avatar_style TEXT NOT NULL,
    energy INTEGER NOT NULL DEFAULT 80,
    mood TEXT NOT NULL DEFAULT '平稳',
    current_task TEXT NOT NULL DEFAULT '适应校园生活',
    schedule TEXT NOT NULL DEFAULT '[]',
    perception TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);
"""


def ensure_agent_profile_table(conn):
    conn.executescript(AGENT_PROFILE_SQL)


def load_json_text(text, fallback):
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def get_agent_module_state(conn, resident_id):
    ensure_agent_profile_table(conn)
    resident = conn.execute("SELECT * FROM residents WHERE id = ?", (resident_id,)).fetchone()
    if not resident:
        return None

    profile = conn.execute(
        "SELECT * FROM agent_profiles WHERE resident_id = ?",
        (resident_id,),
    ).fetchone()
    inventory_rows = conn.execute(
        "SELECT item_name, quantity FROM inventory WHERE resident_id = ? ORDER BY item_name",
        (resident_id,),
    ).fetchall()
    relationship_rows = conn.execute(
        """
        SELECT relationships.to_resident_id, residents.name, residents.role,
               relationships.score, relationships.notes
        FROM relationships
        JOIN residents ON residents.id = relationships.to_resident_id
        WHERE relationships.from_resident_id = ?
        ORDER BY relationships.score DESC
        LIMIT 10
        """,
        (resident_id,),
    ).fetchall()
    memory_rows = conn.execute(
        """
        SELECT day, content, importance, created_at
        FROM memories
        WHERE resident_id = ?
        ORDER BY id DESC
        LIMIT 8
        """,
        (resident_id,),
    ).fetchall()

    profile_data = dict(profile) if profile else {}
    schedule = load_json_text(profile_data.get("schedule"), [])
    perception = load_json_text(profile_data.get("perception"), {})

    return {
        "id": resident["id"],
        "name": resident["name"],
        "gender": profile_data.get("gender", "未设置"),
        "avatar_style": profile_data.get("avatar_style", "简单卡通校园人物"),
        "modules": {
            "Physical": {
                "description": "我是谁、我在哪",
                "position": resident["location"],
                "role": resident["role"],
                "energy": profile_data.get("energy", 80),
                "money": resident["money"],
                "mood": profile_data.get("mood", "平稳"),
                "inventory": rows_to_dicts(inventory_rows),
            },
            "Mental": {
                "description": "我想干什么",
                "goal": resident["goal"],
                "personality": resident["personality"],
                "task": profile_data.get("current_task", "适应校园生活"),
            },
            "Social": {
                "description": "我认识谁",
                "relationships": rows_to_dicts(relationship_rows),
            },
            "Memory": {
                "description": "我经历过什么",
                "memories": rows_to_dicts(memory_rows),
            },
            "Schedule": {
                "description": "我现在该干什么",
                "schedule": schedule,
            },
            "Perception": {
                "description": "我现在看见什么",
                "perception": perception,
            },
        },
    }


def get_all_agent_module_states(conn):
    rows = conn.execute("SELECT id FROM residents ORDER BY id").fetchall()
    return [get_agent_module_state(conn, row["id"]) for row in rows]


class MoveRequest(BaseModel):
    resident_id: int
    destination: str


class ChatRequest(BaseModel):
    speaker_id: int
    listener_id: int
    message: str


class BuySellRequest(BaseModel):
    buyer_id: int
    seller_id: int
    item_name: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)


class PolicyRequest(BaseModel):
    proposer_id: int
    title: str
    description: str


class VotePolicyRequest(BaseModel):
    resident_id: int
    policy_id: int
    vote: str


class CampusEnvironmentRequest(BaseModel):
    weather: Optional[str] = None
    semester_stage: Optional[str] = None
    exam_pressure: Optional[int] = Field(default=None, ge=0, le=100)
    activity_heat: Optional[int] = Field(default=None, ge=0, le=100)
    campus_flow: Optional[int] = Field(default=None, ge=0, le=100)
    canteen_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    library_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    traffic_status: Optional[str] = None
    campus_mood: Optional[str] = None
    consumption_index: Optional[float] = Field(default=None, ge=0.1, le=3.0)


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def ensure_campus_state_table(conn):
    conn.executescript(CAMPUS_STATE_SQL)


def get_campus_environment(conn, day=None):
    ensure_campus_state_table(conn)
    if day is None:
        day = get_current_day(conn)

    row = conn.execute("SELECT * FROM campus_state WHERE day = ?", (day,)).fetchone()
    if not row:
        previous = conn.execute(
            "SELECT * FROM campus_state WHERE day < ? ORDER BY day DESC LIMIT 1",
            (day,),
        ).fetchone()
        values = dict(previous) if previous else dict(DEFAULT_ENV)
        values.pop("day", None)
        values.pop("created_at", None)
        conn.execute(
            """
            INSERT INTO campus_state (
                day, weather, semester_stage, exam_pressure, activity_heat,
                campus_flow, canteen_crowd, library_crowd, traffic_status,
                campus_mood, consumption_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                day,
                values.get("weather", DEFAULT_ENV["weather"]),
                values.get("semester_stage", DEFAULT_ENV["semester_stage"]),
                values.get("exam_pressure", DEFAULT_ENV["exam_pressure"]),
                values.get("activity_heat", DEFAULT_ENV["activity_heat"]),
                values.get("campus_flow", DEFAULT_ENV["campus_flow"]),
                values.get("canteen_crowd", DEFAULT_ENV["canteen_crowd"]),
                values.get("library_crowd", DEFAULT_ENV["library_crowd"]),
                values.get("traffic_status", DEFAULT_ENV["traffic_status"]),
                values.get("campus_mood", DEFAULT_ENV["campus_mood"]),
                values.get("consumption_index", DEFAULT_ENV["consumption_index"]),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM campus_state WHERE day = ?", (day,)).fetchone()
    return dict(row)


def get_recent_context(conn, resident_id, limit=8):
    memories = conn.execute(
        """
        SELECT day, content, importance, created_at
        FROM memories
        WHERE resident_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (resident_id, limit),
    ).fetchall()
    events = conn.execute(
        """
        SELECT day, event_type, description, created_at
        FROM city_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return {
        "memories": rows_to_dicts(memories),
        "events": rows_to_dicts(events),
    }


def extract_json(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def decide_agent_action(conn, resident_id):
    resident = get_resident(conn, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    day = get_current_day(conn)
    env = get_campus_environment(conn, day)
    context = get_recent_context(conn, resident_id)
    module_state = get_agent_module_state(conn, resident_id)
    other_agents = conn.execute(
        "SELECT id, name, role, location FROM residents WHERE id != ? ORDER BY id",
        (resident_id,),
    ).fetchall()

    prompt = f"""
你正在驱动一个校园封闭世界中的 Agent。

当前日期：第 {day} 天
校园环境：{json.dumps(env, ensure_ascii=False)}
当前 Agent：{json.dumps(dict(resident), ensure_ascii=False)}
其他 Agent：{json.dumps(rows_to_dicts(other_agents), ensure_ascii=False)}
近期记忆和事件：{json.dumps(context, ensure_ascii=False)}
Agent 六模块状态：{json.dumps(module_state, ensure_ascii=False)}

请只返回严格 JSON，不要解释，不要 Markdown。
可选 action 只能是：move、chat、buy_sell、submit_policy、observe。
地点只能从这些里面选：{list(VALID_LOCATIONS)}。

返回格式：
{{
  "action": "move/chat/buy_sell/submit_policy/observe",
  "reason": "为什么这样做",
  "tool_input": {{}}
}}

tool_input 规则：
move: {{"destination": "图书馆"}}
chat: {{"target_id": 2, "message": "一句校园对话"}}
buy_sell: {{"seller_id": 5, "item_name": "套餐饭", "quantity": 1, "unit_price": 12}}
submit_policy: {{"title": "政策标题", "description": "政策内容"}}
observe: {{"focus": "观察什么"}}
"""

    try:
        raw = ask_llm(prompt)
        decision = extract_json(raw)
    except Exception as exc:
        decision = {
            "action": "observe",
            "reason": f"AI 决策解析失败，改为观察校园：{exc}",
            "tool_input": {"focus": "校园整体状态"},
        }

    return {
        "resident": dict(resident),
        "decision": decision,
    }


def execute_decision(conn, resident_id, decision):
    resident = get_resident(conn, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    action = str(decision.get("action", "observe")).strip()
    reason = str(decision.get("reason", "自主决策"))
    tool_input = decision.get("tool_input") or {}
    day = get_current_day(conn)

    try:
        if action == "move":
            destination = tool_input.get("destination", resident["location"])
            result = move_resident(conn, resident_id, destination)
        elif action == "chat":
            target_id = int(tool_input.get("target_id"))
            message = tool_input.get("message") or "今天校园情况怎么样？"
            result = chat_between(conn, resident_id, target_id, message)
        elif action == "buy_sell":
            seller_id = int(tool_input.get("seller_id", 5))
            item_name = tool_input.get("item_name", "套餐饭")
            quantity = int(tool_input.get("quantity", 1))
            unit_price = int(tool_input.get("unit_price", 10))
            result = buy_sell(conn, resident_id, seller_id, item_name, quantity, unit_price)
        elif action == "submit_policy":
            title = tool_input.get("title", "校园微调建议")
            description = tool_input.get("description", reason)
            conn.execute(
                """
                INSERT INTO policies (title, description, proposer_id)
                VALUES (?, ?, ?)
                """,
                (title, description, resident_id),
            )
            text = f"{resident['name']} 提交校园政策《{title}》：{description}"
            add_event(conn, day, "policy_submit", text)
            add_memory(conn, resident_id, day, text, importance=3)
            conn.commit()
            result = {"message": "政策提交成功", "description": text}
        else:
            focus = tool_input.get("focus", "校园状态")
            text = f"{resident['name']} 观察 {focus}。原因：{reason}"
            add_event(conn, day, "agent_observe", text)
            add_memory(conn, resident_id, day, text, importance=1)
            conn.commit()
            result = {"message": "观察完成", "description": text}
    except Exception as exc:
        text = f"{resident['name']} 原计划执行 {action}，但失败：{exc}。改为观察校园。"
        add_event(conn, day, "agent_observe", text)
        add_memory(conn, resident_id, day, text, importance=1)
        conn.commit()
        result = {"message": "行动失败，已转为观察", "description": text, "error": str(exc)}

    return {
        "resident_id": resident_id,
        "action": action,
        "reason": reason,
        "result": result,
    }


def auto_update_environment(conn, day):
    previous = get_campus_environment(conn, day)
    weather = random.choice(["晴", "多云", "小雨", "闷热", "大风"])
    semester_stage = previous.get("semester_stage", "平时周")
    exam_pressure = int(previous.get("exam_pressure", 35))
    activity_heat = int(previous.get("activity_heat", 50))

    if day % 7 == 0:
        semester_stage = "考试周"
        exam_pressure = min(100, exam_pressure + 25)
        activity_heat = max(20, activity_heat - 15)
    elif day % 5 == 0:
        semester_stage = "活动周"
        exam_pressure = max(10, exam_pressure - 10)
        activity_heat = min(100, activity_heat + 25)
    else:
        exam_pressure = max(10, min(100, exam_pressure + random.randint(-8, 8)))
        activity_heat = max(10, min(100, activity_heat + random.randint(-10, 10)))

    campus_flow = max(10, min(100, 45 + activity_heat // 2 + random.randint(-10, 10)))
    canteen_crowd = max(10, min(100, campus_flow + random.randint(-10, 20)))
    library_crowd = max(10, min(100, 35 + exam_pressure // 2 + random.randint(-10, 15)))
    traffic_status = "拥堵" if campus_flow > 75 else "正常"
    campus_mood = "紧张" if exam_pressure > 75 else ("活跃" if activity_heat > 70 else "平稳")
    consumption_index = round(max(0.5, min(1.8, 0.8 + activity_heat / 100 + random.uniform(-0.15, 0.15))), 2)

    conn.execute(
        """
        INSERT INTO campus_state (
            day, weather, semester_stage, exam_pressure, activity_heat,
            campus_flow, canteen_crowd, library_crowd, traffic_status,
            campus_mood, consumption_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(day) DO UPDATE SET
            weather = excluded.weather,
            semester_stage = excluded.semester_stage,
            exam_pressure = excluded.exam_pressure,
            activity_heat = excluded.activity_heat,
            campus_flow = excluded.campus_flow,
            canteen_crowd = excluded.canteen_crowd,
            library_crowd = excluded.library_crowd,
            traffic_status = excluded.traffic_status,
            campus_mood = excluded.campus_mood,
            consumption_index = excluded.consumption_index
        """,
        (
            day,
            weather,
            semester_stage,
            exam_pressure,
            activity_heat,
            campus_flow,
            canteen_crowd,
            library_crowd,
            traffic_status,
            campus_mood,
            consumption_index,
        ),
    )
    conn.commit()
    return get_campus_environment(conn, day)


@app.get("/")
def home():
    return {
        "name": "校园封闭世界 AI-Agent 沙盘系统",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/ai/test")
def ai_test():
    prompt = "请用一句话说明你已接入校园封闭世界 AI-Agent 系统。"
    return {"message": "AI API 调用成功", "result": ask_llm(prompt)}


@app.get("/api/state")
def get_state():
    with get_connection() as conn:
        day = get_current_day(conn)
        residents = conn.execute("SELECT * FROM residents ORDER BY id").fetchall()
        events = conn.execute(
            "SELECT * FROM city_events ORDER BY id DESC LIMIT 80"
        ).fetchall()
        return {
            "world_type": "campus_closed_world",
            "current_day": day,
            "locations": sorted(VALID_LOCATIONS),
            "environment": get_campus_environment(conn, day),
            "agents": rows_to_dicts(residents),
            "residents": rows_to_dicts(residents),
            "events": rows_to_dicts(events),
            "agent_modules": get_all_agent_module_states(conn),
        }


@app.get("/api/agents")
def get_agents():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM residents ORDER BY id").fetchall()
        return rows_to_dicts(rows)


@app.get("/api/residents")
def get_residents():
    return get_agents()



@app.get("/api/agents/modules")
def get_agents_modules():
    with get_connection() as conn:
        return get_all_agent_module_states(conn)


@app.get("/api/agents/{resident_id}/modules")
def get_agent_modules(resident_id: int):
    with get_connection() as conn:
        state = get_agent_module_state(conn, resident_id)
        if not state:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        return state

@app.get("/api/inventory")
def get_inventory():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT inventory.*, residents.name AS owner_name
            FROM inventory
            JOIN residents ON residents.id = inventory.resident_id
            ORDER BY resident_id, item_name
            """
        ).fetchall()
        return rows_to_dicts(rows)


@app.get("/api/campus/environment/today")
def get_today_environment():
    with get_connection() as conn:
        return get_campus_environment(conn)


@app.post("/api/campus/environment/set")
def set_today_environment(payload: CampusEnvironmentRequest):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="至少填写一个环境参数")

    allowed = set(DEFAULT_ENV.keys())
    if not set(updates).issubset(allowed):
        raise HTTPException(status_code=400, detail="存在不支持的环境参数")

    with get_connection() as conn:
        day = get_current_day(conn)
        get_campus_environment(conn, day)
        set_clause = ", ".join([f"{key} = ?" for key in updates])
        values = list(updates.values()) + [day]
        conn.execute(f"UPDATE campus_state SET {set_clause} WHERE day = ?", values)
        add_event(conn, day, "environment_update", f"校园环境参数更新：{updates}")
        conn.commit()
        return get_campus_environment(conn, day)


@app.post("/api/tools/move")
def tool_move(payload: MoveRequest):
    with get_connection() as conn:
        return move_resident(conn, payload.resident_id, payload.destination)


@app.post("/api/tools/chat")
def tool_chat(payload: ChatRequest):
    with get_connection() as conn:
        return chat_between(conn, payload.speaker_id, payload.listener_id, payload.message)


@app.post("/api/tools/buy-sell")
def tool_buy_sell(payload: BuySellRequest):
    with get_connection() as conn:
        return buy_sell(
            conn,
            payload.buyer_id,
            payload.seller_id,
            payload.item_name,
            payload.quantity,
            payload.unit_price,
        )


@app.get("/api/policies")
def get_policies():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT policies.*, residents.name AS proposer_name
            FROM policies
            LEFT JOIN residents ON residents.id = policies.proposer_id
            ORDER BY policies.id DESC
            """
        ).fetchall()
        return rows_to_dicts(rows)


@app.post("/api/tools/submit-policy")
def submit_policy(payload: PolicyRequest):
    with get_connection() as conn:
        proposer = get_resident(conn, payload.proposer_id)
        if not proposer:
            raise HTTPException(status_code=404, detail="提案人不存在")
        day = get_current_day(conn)
        conn.execute(
            """
            INSERT INTO policies (title, description, proposer_id)
            VALUES (?, ?, ?)
            """,
            (payload.title, payload.description, payload.proposer_id),
        )
        description = f"{proposer['name']} 提交校园政策《{payload.title}》：{payload.description}"
        add_event(conn, day, "policy_submit", description)
        add_memory(conn, payload.proposer_id, day, description, importance=3)
        conn.commit()
        return {"message": "政策提交成功", "description": description}


@app.post("/api/tools/vote-policy")
def vote_policy(payload: VotePolicyRequest):
    if payload.vote not in {"yes", "no"}:
        raise HTTPException(status_code=400, detail="vote 只能是 yes 或 no")

    with get_connection() as conn:
        resident = get_resident(conn, payload.resident_id)
        policy = conn.execute("SELECT * FROM policies WHERE id = ?", (payload.policy_id,)).fetchone()
        if not resident or not policy:
            raise HTTPException(status_code=404, detail="投票人或政策不存在")
        column = "yes_votes" if payload.vote == "yes" else "no_votes"
        conn.execute(f"UPDATE policies SET {column} = {column} + 1 WHERE id = ?", (payload.policy_id,))
        day = get_current_day(conn)
        description = f"{resident['name']} 对政策《{policy['title']}》投票：{payload.vote}"
        add_event(conn, day, "policy_vote", description)
        add_memory(conn, payload.resident_id, day, description, importance=1)
        conn.commit()
        return {"message": "投票成功", "description": description}


@app.post("/api/tools/close-policy/{policy_id}")
def close_policy(policy_id: int):
    with get_connection() as conn:
        policy = conn.execute("SELECT * FROM policies WHERE id = ?", (policy_id,)).fetchone()
        if not policy:
            raise HTTPException(status_code=404, detail="政策不存在")
        status = "passed" if int(policy["yes_votes"]) >= int(policy["no_votes"]) else "rejected"
        conn.execute("UPDATE policies SET status = ? WHERE id = ?", (status, policy_id))
        day = get_current_day(conn)
        description = f"政策《{policy['title']}》投票结束，赞成 {policy['yes_votes']}，反对 {policy['no_votes']}，结果：{status}。"
        add_event(conn, day, "policy_close", description)
        conn.commit()
        return {"message": "政策已结算", "status": status, "description": description}


@app.post("/api/tools/daily-reflect")
def daily_reflect():
    with get_connection() as conn:
        day = get_current_day(conn)
        agents = conn.execute("SELECT * FROM residents ORDER BY id").fetchall()
        events = conn.execute(
            "SELECT description FROM city_events WHERE day = ? ORDER BY id DESC LIMIT 20",
            (day,),
        ).fetchall()
        event_text = "；".join([row["description"] for row in events]) or "今天校园较为平静。"

        results = []
        for agent in agents:
            prompt = f"请以{agent['name']}的第一人称，用一句话总结今天的校园生活。今日事件：{event_text}"
            try:
                reflection = ask_llm(prompt)
            except Exception:
                reflection = f"{agent['name']} 记录了第 {day} 天的校园生活。"
            add_memory(conn, agent["id"], day, reflection, importance=2)
            results.append({"agent_id": agent["id"], "name": agent["name"], "reflection": reflection})

        add_event(conn, day, "daily_reflect", f"第 {day} 天校园日报总结完成，共生成 {len(results)} 条记忆。")
        conn.commit()
        return {"day": day, "results": results}


@app.get("/api/newspaper/today")
def newspaper_today():
    with get_connection() as conn:
        day = get_current_day(conn)
        env = get_campus_environment(conn, day)
        events = conn.execute(
            "SELECT event_type, description, created_at FROM city_events WHERE day = ? ORDER BY id DESC LIMIT 30",
            (day,),
        ).fetchall()
        return {
            "title": f"校园封闭世界日报 第 {day} 天",
            "environment": env,
            "events": rows_to_dicts(events),
            "agent_modules": get_all_agent_module_states(conn),
        }


@app.get("/api/newspaper/ai-today")
def ai_newspaper_today():
    data = newspaper_today()
    prompt = f"请把下面校园封闭世界数据写成一份简短校园日报，分为标题、环境、主要事件、趋势判断：{json.dumps(data, ensure_ascii=False)}"
    return {"day": data["title"], "newspaper": ask_llm(prompt), "source": data}


@app.post("/api/agent/decide/{resident_id}")
def decide_agent(resident_id: int):
    with get_connection() as conn:
        return decide_agent_action(conn, resident_id)


@app.post("/api/agent/act/{resident_id}")
def act_agent(resident_id: int):
    with get_connection() as conn:
        decision_data = decide_agent_action(conn, resident_id)
        result = execute_decision(conn, resident_id, decision_data["decision"])
        return {"decision": decision_data, "execution": result}


@app.post("/api/agent/act-all")
def act_all_agents():
    with get_connection() as conn:
        agents = conn.execute("SELECT id FROM residents ORDER BY id").fetchall()
        results = []
        for agent in agents:
            decision_data = decide_agent_action(conn, agent["id"])
            execution = execute_decision(conn, agent["id"], decision_data["decision"])
            results.append({"decision": decision_data, "execution": execution})
        return {"message": f"{len(results)} 个校园 Agent 已轮流自主行动", "results": results}


@app.post("/api/simulate/ai-day")
def simulate_ai_day():
    with get_connection() as conn:
        old_day = get_current_day(conn)
        new_day = old_day + 1
        conn.execute("UPDATE simulation_state SET value = ? WHERE key = 'current_day'", (str(new_day),))
        conn.commit()
        env = auto_update_environment(conn, new_day)
        agents = conn.execute("SELECT id FROM residents ORDER BY id").fetchall()
        results = []
        for agent in agents:
            decision_data = decide_agent_action(conn, agent["id"])
            execution = execute_decision(conn, agent["id"], decision_data["decision"])
            results.append({"decision": decision_data, "execution": execution})
        add_event(conn, new_day, "daily_reflect", f"第 {new_day} 天校园自动模拟完成，共产生 {len(results)} 个行动。")
        conn.commit()
        return {
            "message": "校园一天模拟完成",
            "day": new_day,
            "environment": env,
            "actions": results,
        }

