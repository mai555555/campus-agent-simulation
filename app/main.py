import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random
import re
import requests
import logging
from xml.etree import ElementTree
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import get_connection
from services.llm_service import ask_llm
PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)

from tools.city_tools import (
    VALID_LOCATIONS,
    add_event,
    add_memory,
    buy_sell,
    chat_between,
    ensure_memory_columns,
    get_current_day,
    get_resident,
    move_resident,
)

app = FastAPI(title="校园封闭世界 AI-Agent 沙盘系统", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/avatars", StaticFiles(directory=str(PROJECT_ROOT / "frontend" / "assets" / "avatars")), name="avatars")
THREE_MODULE_DIR = PROJECT_ROOT / "frontend" / "vendor" / "three"
app.mount("/three", StaticFiles(directory=str(THREE_MODULE_DIR)), name="three")

CAMPUS_STATE_SQL = """
CREATE TABLE IF NOT EXISTS campus_state (
    day INTEGER PRIMARY KEY,
    weather TEXT NOT NULL DEFAULT '晴',
    semester_stage TEXT NOT NULL DEFAULT '平时周',
    time_slot TEXT NOT NULL DEFAULT '上午',
    weekday TEXT NOT NULL DEFAULT '周一',
    temperature INTEGER NOT NULL DEFAULT 24,
    rainfall INTEGER NOT NULL DEFAULT 0,
    weather_source TEXT NOT NULL DEFAULT 'simulation',
    weather_observed_at TEXT NOT NULL DEFAULT '',
    real_date TEXT NOT NULL DEFAULT '',
    real_time TEXT NOT NULL DEFAULT '',
    time_source TEXT NOT NULL DEFAULT 'simulation',
    exam_pressure INTEGER NOT NULL DEFAULT 35,
    assignment_pressure INTEGER NOT NULL DEFAULT 40,
    study_atmosphere INTEGER NOT NULL DEFAULT 60,
    activity_heat INTEGER NOT NULL DEFAULT 50,
    event_name TEXT NOT NULL DEFAULT '社团招新',
    event_intensity INTEGER NOT NULL DEFAULT 50,
    campus_flow INTEGER NOT NULL DEFAULT 55,
    classroom_crowd INTEGER NOT NULL DEFAULT 55,
    canteen_crowd INTEGER NOT NULL DEFAULT 50,
    library_crowd INTEGER NOT NULL DEFAULT 45,
    dorm_crowd INTEGER NOT NULL DEFAULT 45,
    playground_crowd INTEGER NOT NULL DEFAULT 40,
    commercial_crowd INTEGER NOT NULL DEFAULT 50,
    traffic_status TEXT NOT NULL DEFAULT '正常',
    network_status TEXT NOT NULL DEFAULT '稳定',
    safety_level INTEGER NOT NULL DEFAULT 90,
    resource_pressure INTEGER NOT NULL DEFAULT 45,
    campus_mood TEXT NOT NULL DEFAULT '平稳',
    consumption_index REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SPACE_SYSTEM_SQL = """
CREATE TABLE IF NOT EXISTS campus_spaces (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL,
    open_hour INTEGER NOT NULL,
    close_hour INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT '开放',
    crowd_field TEXT NOT NULL,
    purpose TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    intensity INTEGER NOT NULL DEFAULT 50,
    target_spaces TEXT NOT NULL DEFAULT '[]',
    effects TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);
"""

DEFAULT_SPACES = [
    ("dorm", "宿舍区", "宿舍区", 600, 0, 24, "开放", "dorm_crowd", "休息、社交与夜间生活"),
    ("teaching", "教学楼", "教学楼", 450, 7, 22, "开放", "classroom_crowd", "上课、小组讨论与实验"),
    ("library", "图书馆", "图书馆", 220, 8, 22, "开放", "library_crowd", "自习、阅读与研究"),
    ("canteen", "食堂", "食堂", 300, 6, 21, "开放", "canteen_crowd", "用餐与日常交流"),
    ("playground", "操场", "操场", 500, 6, 22, "开放", "playground_crowd", "运动、训练与大型活动"),
    ("business", "商业街", "商业街", 180, 9, 22, "开放", "commercial_crowd", "消费、创业与服务"),
    ("admin", "校务处", "校务处", 80, 8, 18, "开放", "campus_flow", "通知、管理与政策协商"),
]

DEFAULT_ENV = {
    "weather": "晴",
    "semester_stage": "平时周",
    "time_slot": "上午",
    "weekday": "周一",
    "temperature": 24,
    "rainfall": 0,
    "weather_source": "simulation",
    "weather_observed_at": "",
    "real_date": "",
    "real_time": "",
    "time_source": "simulation",
    "exam_pressure": 35,
    "assignment_pressure": 40,
    "study_atmosphere": 60,
    "activity_heat": 50,
    "event_name": "社团招新",
    "event_intensity": 50,
    "campus_flow": 55,
    "classroom_crowd": 55,
    "canteen_crowd": 50,
    "library_crowd": 45,
    "dorm_crowd": 45,
    "playground_crowd": 40,
    "commercial_crowd": 50,
    "traffic_status": "正常",
    "network_status": "稳定",
    "safety_level": 90,
    "resource_pressure": 45,
    "campus_mood": "平稳",
    "consumption_index": 1.0,
}

ENV_COLUMN_TYPES = {
    "weather": "TEXT NOT NULL DEFAULT '晴'",
    "semester_stage": "TEXT NOT NULL DEFAULT '平时周'",
    "time_slot": "TEXT NOT NULL DEFAULT '上午'",
    "weekday": "TEXT NOT NULL DEFAULT '周一'",
    "temperature": "INTEGER NOT NULL DEFAULT 24",
    "rainfall": "INTEGER NOT NULL DEFAULT 0",
    "weather_source": "TEXT NOT NULL DEFAULT 'simulation'",
    "weather_observed_at": "TEXT NOT NULL DEFAULT ''",
    "real_date": "TEXT NOT NULL DEFAULT ''",
    "real_time": "TEXT NOT NULL DEFAULT ''",
    "time_source": "TEXT NOT NULL DEFAULT 'simulation'",
    "exam_pressure": "INTEGER NOT NULL DEFAULT 35",
    "assignment_pressure": "INTEGER NOT NULL DEFAULT 40",
    "study_atmosphere": "INTEGER NOT NULL DEFAULT 60",
    "activity_heat": "INTEGER NOT NULL DEFAULT 50",
    "event_name": "TEXT NOT NULL DEFAULT '社团招新'",
    "event_intensity": "INTEGER NOT NULL DEFAULT 50",
    "campus_flow": "INTEGER NOT NULL DEFAULT 55",
    "classroom_crowd": "INTEGER NOT NULL DEFAULT 55",
    "canteen_crowd": "INTEGER NOT NULL DEFAULT 50",
    "library_crowd": "INTEGER NOT NULL DEFAULT 45",
    "dorm_crowd": "INTEGER NOT NULL DEFAULT 45",
    "playground_crowd": "INTEGER NOT NULL DEFAULT 40",
    "commercial_crowd": "INTEGER NOT NULL DEFAULT 50",
    "traffic_status": "TEXT NOT NULL DEFAULT '正常'",
    "network_status": "TEXT NOT NULL DEFAULT '稳定'",
    "safety_level": "INTEGER NOT NULL DEFAULT 90",
    "resource_pressure": "INTEGER NOT NULL DEFAULT 45",
    "campus_mood": "TEXT NOT NULL DEFAULT '平稳'",
    "consumption_index": "REAL NOT NULL DEFAULT 1.0",
}

AGENT_NEWS_SQL = """
CREATE TABLE IF NOT EXISTS agent_news_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(day, resident_id)
);
"""

EXTERNAL_INFORMATION_SQL = """
CREATE TABLE IF NOT EXISTS external_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    relevance INTEGER NOT NULL DEFAULT 50,
    published_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_information (
    information_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    relevance INTEGER NOT NULL DEFAULT 50,
    credibility INTEGER NOT NULL DEFAULT 80,
    distortion_note TEXT NOT NULL DEFAULT '',
    source_resident_id INTEGER,
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (information_id, resident_id),
    FOREIGN KEY (information_id) REFERENCES external_information(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);
"""

AGENT_PROFILE_SQL = """
CREATE TABLE IF NOT EXISTS agent_profiles (
    resident_id INTEGER PRIMARY KEY,
    gender TEXT NOT NULL,
    avatar_style TEXT NOT NULL,
    avatar_image TEXT NOT NULL DEFAULT '',
    hierarchy_level INTEGER NOT NULL DEFAULT 1,
    organization TEXT NOT NULL DEFAULT '学生',
    skills TEXT NOT NULL DEFAULT '{}',
    strategy TEXT NOT NULL DEFAULT '{}',
    energy INTEGER NOT NULL DEFAULT 80,
    time_budget INTEGER NOT NULL DEFAULT 100,
    mood TEXT NOT NULL DEFAULT '平稳',
    current_task TEXT NOT NULL DEFAULT '适应校园生活',
    schedule TEXT NOT NULL DEFAULT '[]',
    perception TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);
"""

PROFILE_COLUMN_TYPES = {
    "avatar_image": "TEXT NOT NULL DEFAULT ''",
    "hierarchy_level": "INTEGER NOT NULL DEFAULT 1",
    "organization": "TEXT NOT NULL DEFAULT '学生'",
    "skills": "TEXT NOT NULL DEFAULT '{}'",
    "strategy": "TEXT NOT NULL DEFAULT '{}'",
    "time_budget": "INTEGER NOT NULL DEFAULT 100",
}

SOCIAL_SYSTEM_SQL = """
CREATE TABLE IF NOT EXISTS agent_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    day INTEGER NOT NULL DEFAULT 1,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    score_delta INTEGER NOT NULL DEFAULT 0,
    lesson TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collaborations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    leader_id INTEGER NOT NULL,
    member_ids TEXT NOT NULL DEFAULT '[]',
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    score INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    participant_ids TEXT NOT NULL DEFAULT '[]',
    metric TEXT NOT NULL,
    winner_id INTEGER,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

BEHAVIOR_SYSTEM_SQL = """
CREATE TABLE IF NOT EXISTS relationship_dynamics (
    from_resident_id INTEGER NOT NULL,
    to_resident_id INTEGER NOT NULL,
    affinity INTEGER NOT NULL DEFAULT 50,
    trust INTEGER NOT NULL DEFAULT 50,
    cooperation INTEGER NOT NULL DEFAULT 50,
    competition INTEGER NOT NULL DEFAULT 0,
    conflict INTEGER NOT NULL DEFAULT 0,
    tension INTEGER NOT NULL DEFAULT 0,
    interaction_count INTEGER NOT NULL DEFAULT 0,
    last_day INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (from_resident_id, to_resident_id),
    FOREIGN KEY (from_resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (to_resident_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS long_term_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    progress INTEGER NOT NULL DEFAULT 0,
    target_progress INTEGER NOT NULL DEFAULT 100,
    deadline_day INTEGER NOT NULL DEFAULT 14,
    status TEXT NOT NULL DEFAULT 'active',
    last_update_day INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL DEFAULT '临时小组',
    leader_id INTEGER NOT NULL,
    member_ids TEXT NOT NULL DEFAULT '[]',
    roles TEXT NOT NULL DEFAULT '{}',
    shared_goal TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    target_progress INTEGER NOT NULL DEFAULT 100,
    deadline_day INTEGER NOT NULL DEFAULT 14,
    status TEXT NOT NULL DEFAULT 'active',
    current_plan TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (leader_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS campus_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    organization_type TEXT NOT NULL,
    goal TEXT NOT NULL,
    budget INTEGER NOT NULL DEFAULT 1000,
    resources TEXT NOT NULL DEFAULT '{}',
    schedule TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization_members (
    organization_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    member_role TEXT NOT NULL DEFAULT 'member',
    joined_day INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    PRIMARY KEY (organization_id, resident_id),
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulation_action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    perception TEXT NOT NULL DEFAULT '{}',
    retrieved_memories TEXT NOT NULL DEFAULT '[]',
    decision TEXT NOT NULL DEFAULT '{}',
    execution TEXT NOT NULL DEFAULT '{}',
    environment_feedback TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);
"""

RELATIONSHIP_DYNAMIC_COLUMNS = {
    "affinity": "INTEGER NOT NULL DEFAULT 50",
    "competition": "INTEGER NOT NULL DEFAULT 0",
    "conflict": "INTEGER NOT NULL DEFAULT 0",
}

LONG_TERM_GOAL_COLUMNS = {
    "completed_at": "TEXT",
}

AGENT_INFORMATION_COLUMNS = {
    "credibility": "INTEGER NOT NULL DEFAULT 80",
    "distortion_note": "TEXT NOT NULL DEFAULT ''",
    "source_resident_id": "INTEGER",
}


def ensure_agent_profile_table(conn):
    conn.executescript(AGENT_PROFILE_SQL)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(agent_profiles)").fetchall()}
    for column, column_type in PROFILE_COLUMN_TYPES.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE agent_profiles ADD COLUMN {column} {column_type}")


def ensure_social_system_tables(conn):
    ensure_agent_profile_table(conn)
    conn.executescript(SOCIAL_SYSTEM_SQL)
    conn.executescript(BEHAVIOR_SYSTEM_SQL)
    relationship_columns = {row["name"] for row in conn.execute("PRAGMA table_info(relationship_dynamics)").fetchall()}
    for column, column_type in RELATIONSHIP_DYNAMIC_COLUMNS.items():
        if column not in relationship_columns:
            conn.execute(f"ALTER TABLE relationship_dynamics ADD COLUMN {column} {column_type}")
    goal_columns = {row["name"] for row in conn.execute("PRAGMA table_info(long_term_goals)").fetchall()}
    for column, column_type in LONG_TERM_GOAL_COLUMNS.items():
        if column not in goal_columns:
            conn.execute(f"ALTER TABLE long_term_goals ADD COLUMN {column} {column_type}")
    normalize_agent_hierarchy(conn)
    seed_long_term_goals(conn)
    seed_campus_organizations(conn)


def load_json_text(text, fallback):
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def infer_goal_category(goal_text):
    text = str(goal_text or "")
    if any(word in text for word in ["成绩", "课程", "考研", "论文", "学习", "实验", "奖学金"]):
        return "study"
    if any(word in text for word in ["销售", "创业", "消费", "订单", "收入", "商机"]):
        return "business"
    if any(word in text for word in ["活动", "社团", "朋友", "交流", "合作"]):
        return "social"
    if any(word in text for word in ["秩序", "设施", "服务", "管理", "安全"]):
        return "service"
    return "general"


def seed_long_term_goals(conn):
    day = get_current_day(conn)
    residents = conn.execute("SELECT id, goal FROM residents").fetchall()
    for resident in residents:
        exists = conn.execute(
            "SELECT 1 FROM long_term_goals WHERE resident_id = ? LIMIT 1",
            (resident["id"],),
        ).fetchone()
        if not exists:
            conn.execute(
                """
                INSERT INTO long_term_goals
                (resident_id, title, category, deadline_day, last_update_day)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    resident["id"],
                    resident["goal"],
                    infer_goal_category(resident["goal"]),
                    day + 14,
                    day,
                ),
            )


def seed_campus_organizations(conn):
    """Create a small set of persistent campus organizations without forcing membership."""
    defaults = [
        ("学生会", "school", "组织校园活动与学生服务", 2200, {"venue_slots": 3, "notice_channels": 2}, [{"time": "周三 18:00", "task": "例会", "location": "校务处"}]),
        ("创新社", "club", "推进技术项目与成员协作", 1600, {"workstations": 8, "project_slots": 4}, [{"time": "周二 19:00", "task": "项目讨论", "location": "教学楼"}]),
        ("校园商户联盟", "business", "保障服务供给并维持经营", 3000, {"stock_budget": 1200, "marketing_slots": 2}, [{"time": "每日 11:30", "task": "经营协调", "location": "商业街"}]),
        ("图书馆服务组", "service", "维护学习空间与资源秩序", 1200, {"maintenance_slots": 2, "study_seats": 220}, [{"time": "周一 09:00", "task": "设施巡检", "location": "图书馆"}]),
    ]
    for name, organization_type, goal, budget, resources, schedule in defaults:
        conn.execute(
            """
            INSERT OR IGNORE INTO campus_organizations
            (name, organization_type, goal, budget, resources, schedule)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, organization_type, goal, budget, json.dumps(resources, ensure_ascii=False), json.dumps(schedule, ensure_ascii=False)),
        )


def get_relationship_dynamics(conn, from_id, to_id):
    ensure_social_system_tables(conn)
    row = conn.execute(
        "SELECT * FROM relationship_dynamics WHERE from_resident_id = ? AND to_resident_id = ?",
        (from_id, to_id),
    ).fetchone()
    if not row:
        base_score = get_relationship_score(conn, from_id, to_id)
        conn.execute(
            """
            INSERT INTO relationship_dynamics
            (from_resident_id, to_resident_id, affinity, trust, cooperation, competition, conflict, tension, last_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                from_id,
                to_id,
                clamp(50 + base_score // 2),
                clamp(45 + base_score // 2),
                clamp(40 + base_score // 2),
                0,
                0,
                0,
                get_current_day(conn),
            ),
        )
        row = conn.execute(
            "SELECT * FROM relationship_dynamics WHERE from_resident_id = ? AND to_resident_id = ?",
            (from_id, to_id),
        ).fetchone()
    return dict(row)


def evolve_relationship(
    conn,
    from_id,
    to_id,
    interaction,
    note,
    trust_delta=0,
    cooperation_delta=0,
    tension_delta=0,
    affinity_delta=None,
    competition_delta=0,
    conflict_delta=None,
):
    current = get_relationship_dynamics(conn, from_id, to_id)
    if affinity_delta is None:
        affinity_delta = round((trust_delta + cooperation_delta - tension_delta) / 3)
    if conflict_delta is None:
        conflict_delta = tension_delta
    affinity = clamp(int(current["affinity"]) + affinity_delta)
    trust = clamp(int(current["trust"]) + trust_delta)
    cooperation = clamp(int(current["cooperation"]) + cooperation_delta)
    competition = clamp(int(current["competition"]) + competition_delta)
    conflict = clamp(int(current["conflict"]) + conflict_delta)
    tension = clamp(int(current["tension"]) + tension_delta)
    relationship_delta = round((affinity_delta + trust_delta + cooperation_delta - conflict_delta) / 4)
    relationship_score = change_relationship(conn, from_id, to_id, relationship_delta, note)
    conn.execute(
        """
        UPDATE relationship_dynamics
        SET affinity = ?, trust = ?, cooperation = ?, competition = ?, conflict = ?, tension = ?,
            interaction_count = interaction_count + 1, last_day = ?
        WHERE from_resident_id = ? AND to_resident_id = ?
        """,
        (affinity, trust, cooperation, competition, conflict, tension, get_current_day(conn), from_id, to_id),
    )
    return {
        "interaction": interaction,
        "affinity": affinity,
        "trust": trust,
        "cooperation": cooperation,
        "competition": competition,
        "conflict": conflict,
        "tension": tension,
        "relationship_score": relationship_score,
    }


def advance_personal_goal(conn, resident_id, action, success):
    ensure_social_system_tables(conn)
    goal = conn.execute(
        """
        SELECT * FROM long_term_goals
        WHERE resident_id = ? AND status = 'active'
        ORDER BY deadline_day, id LIMIT 1
        """,
        (resident_id,),
    ).fetchone()
    if not goal:
        return None
    action_points = {
        "study": {"observe": 3, "move": 2, "chat": 1},
        "business": {"buy_sell": 6, "chat": 2, "move": 2, "observe": 1},
        "social": {"chat": 5, "move": 2, "observe": 1},
        "service": {"submit_policy": 5, "observe": 2, "move": 2, "chat": 1},
        "general": {"move": 2, "chat": 2, "buy_sell": 2, "submit_policy": 3, "observe": 1},
    }
    points = action_points.get(goal["category"], action_points["general"]).get(action, 1)
    if not success:
        points = 0
    progress = clamp(int(goal["progress"]) + points)
    status = "completed" if progress >= int(goal["target_progress"]) else "active"
    conn.execute(
        """
        UPDATE long_term_goals
        SET progress = ?, status = ?, last_update_day = ?,
            completed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
        WHERE id = ?
        """,
        (progress, status, get_current_day(conn), status, goal["id"]),
    )
    if status == "completed":
        add_event(conn, get_current_day(conn), "goal_completed", f"Agent {resident_id} 完成长期目标《{goal['title']}》。")
    return {"goal_id": goal["id"], "title": goal["title"], "progress": progress, "status": status, "points": points}


def advance_group_goals(conn, day, action_results):
    ensure_social_system_tables(conn)
    completed_actions = {
        item["resident_id"]: item["action"]
        for item in action_results
        if item.get("success")
    }
    updates = []
    groups = conn.execute("SELECT * FROM group_goals WHERE status = 'active'").fetchall()
    for group in groups:
        members = json.loads(group["member_ids"])
        participant_count = sum(1 for member_id in members if member_id in completed_actions)
        if participant_count == 0:
            continue
        increment = min(15, 2 + participant_count * 2)
        progress = clamp(int(group["progress"]) + increment)
        status = "completed" if progress >= int(group["target_progress"]) else "active"
        conn.execute("UPDATE group_goals SET progress = ?, status = ? WHERE id = ?", (progress, status, group["id"]))
        updates.append({"group_id": group["id"], "name": group["name"], "progress": progress, "status": status, "active_members": participant_count})
        if status == "completed":
            add_event(conn, day, "group_goal_completed", f"群体目标《{group['shared_goal']}》已完成。")

    conn.execute(
        """
        UPDATE relationship_dynamics
        SET tension = CASE WHEN tension > 0 THEN tension - 1 ELSE 0 END
        WHERE last_day < ?
        """,
        (day,),
    )
    return updates


def schedule_location(task):
    text = str(task or "")
    if any(word in text for word in ["早餐", "午餐", "晚餐", "吃饭", "备菜"]):
        return "食堂"
    if any(word in text for word in ["课程", "课", "实验", "面试", "小组讨论", "编程"]):
        return "教学楼"
    if any(word in text for word in ["图书馆", "自习", "阅读", "背单词", "论文", "查招聘", "投递简历"]):
        return "图书馆"
    if any(word in text for word in ["训练", "晨跑", "操场", "采访"]):
        return "操场"
    if any(word in text for word in ["开店", "促销", "订单", "调研", "奶茶", "商业"]):
        return "商业街"
    if any(word in text for word in ["通知", "校务", "审批", "巡查", "维护", "维修", "治理"]):
        return "校务处"
    if any(word in text for word in ["宿舍", "复盘", "休息", "睡"]):
        return "宿舍区"
    return None


def get_schedule_context(schedule, env):
    entries = schedule if isinstance(schedule, list) else []
    time_text = str(env.get("real_time") or "")
    try:
        hour, minute = [int(value) for value in time_text.split(":")[:2]]
        now_minutes = hour * 60 + minute
    except (TypeError, ValueError):
        now_minutes = {"上午": 9 * 60, "中午": 12 * 60, "下午": 15 * 60, "晚上": 20 * 60, "深夜": 2 * 60}.get(env.get("time_slot"), 9 * 60)

    parsed = []
    for entry in entries:
        match = re.match(r"\s*(\d{1,2}):(\d{2})\s+(.+)", str(entry))
        if not match:
            continue
        start = int(match.group(1)) * 60 + int(match.group(2))
        task = match.group(3).strip()
        parsed.append({"entry": str(entry), "start_minutes": start, "task": task, "location": schedule_location(task)})
    if not parsed:
        return {"current_task": "自由安排", "is_due": False, "location": None, "minutes_until": None}

    parsed.sort(key=lambda item: item["start_minutes"])
    current = min(parsed, key=lambda item: abs(item["start_minutes"] - now_minutes))
    minutes_until = current["start_minutes"] - now_minutes
    is_due = -30 <= minutes_until <= 45
    return {
        "current_task": current["task"],
        "entry": current["entry"],
        "location": current["location"],
        "minutes_until": minutes_until,
        "is_due": is_due,
        "next_tasks": parsed[:4],
    }


def attach_schedule_guidance(schedule_context, decision):
    """Expose the current commitment to the Agent without overriding its choice."""
    decision["schedule_guidance"] = schedule_context
    if schedule_context.get("is_due"):
        decision["schedule_note"] = f"当前安排「{schedule_context['current_task']}」已到点，Agent 可自主选择执行或暂缓。"
    return decision


def is_schedule_aligned(resident, action, tool_input, schedule_context):
    if not schedule_context or not schedule_context.get("is_due"):
        return None
    expected_location = schedule_context.get("location")
    if not expected_location:
        return None
    if action == "move":
        return tool_input.get("destination") == expected_location
    return action == "observe" and resident["location"] == expected_location


def get_agent_module_state(conn, resident_id):
    ensure_agent_profile_table(conn)
    ensure_memory_columns(conn)
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
    current_day = get_current_day(conn)
    memory_rows = conn.execute(
        """
        SELECT day, content, importance, memory_type, tags, source, access_count, last_accessed_at, created_at
        FROM memories
        WHERE resident_id = ? AND day <= ?
        ORDER BY id DESC
        LIMIT 8
        """,
        (resident_id, current_day),
    ).fetchall()

    profile_data = dict(profile) if profile else {}
    schedule = load_json_text(profile_data.get("schedule"), [])
    perception = load_json_text(profile_data.get("perception"), {})
    skills = load_json_text(profile_data.get("skills"), {})
    strategy = load_json_text(profile_data.get("strategy"), {})
    hierarchy_level = profile_data.get("hierarchy_level", 1)
    hierarchy_title = get_hierarchy_title(hierarchy_level)
    env = get_campus_environment(conn)
    schedule_context = get_schedule_context(schedule, env)

    return {
        "id": resident["id"],
        "name": resident["name"],
        "gender": profile_data.get("gender", "未设置"),
        "avatar_style": profile_data.get("avatar_style", "简单卡通校园人物"),
        "avatar_image": profile_data.get("avatar_image", ""),
        "organization": profile_data.get("organization", "学生"),
        "hierarchy_level": hierarchy_level,
        "hierarchy_title": hierarchy_title,
        "modules": {
            "Physical": {
                "description": "我是谁、我在哪",
                "position": resident["location"],
                "role": resident["role"],
                "energy": profile_data.get("energy", 80),
                "time_budget": profile_data.get("time_budget", 100),
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
                "current_schedule": schedule_context,
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


def clamp(value, low=0, high=100):
    return max(low, min(high, int(value)))


def choose_mood(energy, action, success=True):
    if not success:
        return "受挫"
    if energy <= 25:
        return "疲惫"
    if action == "chat":
        return "放松"
    if action == "buy_sell":
        return "满足"
    if action == "submit_policy":
        return "认真"
    if action == "move":
        return "行动中"
    return "观察中"


def calculate_action_cost(conn, resident_id, action, tool_input=None, success=True):
    tool_input = tool_input or {}
    base_costs = {
        "move": {"energy": 8, "time": 12},
        "chat": {"energy": 3, "time": 10},
        "buy_sell": {"energy": 5, "time": 15},
        "submit_policy": {"energy": 6, "time": 25},
        "create_group": {"energy": 7, "time": 28},
        "join_group": {"energy": 3, "time": 12},
        "leave_group": {"energy": 2, "time": 8},
        "observe": {"energy": 2, "time": 8},
    }
    cost = dict(base_costs.get(action, base_costs["observe"]))
    env = get_campus_environment(conn)
    if action == "move":
        destination = tool_input.get("destination")
        space = next((item for item in get_space_snapshot(conn)["spaces"] if item["location"] == destination), None)
        if space and int(space["crowd_percent"]) >= 70:
            cost["time"] += 6
            cost["energy"] += 2
        if int(env.get("rainfall", 0)) >= 20:
            cost["time"] += 4
            cost["energy"] += 2
        if env.get("traffic_status") == "拥堵":
            cost["time"] += 3
    if action == "buy_sell" and int(env.get("commercial_crowd", 0)) >= 70:
        cost["time"] += 5
    if action == "observe" and int(env.get("study_atmosphere", 0)) >= 75:
        cost["time"] = max(5, cost["time"] - 2)
    if not success:
        cost["energy"] += 3
        cost["time"] += 5
    return cost


def ensure_action_affordable(conn, resident_id, cost, action):
    profile = conn.execute("SELECT energy, time_budget FROM agent_profiles WHERE resident_id = ?", (resident_id,)).fetchone()
    if not profile:
        return
    if action != "observe" and int(profile["energy"]) < int(cost["energy"]):
        raise ValueError("精力不足，需要先休息或进行低成本观察")
    if int(profile["time_budget"]) < int(cost["time"]):
        raise ValueError("今日可用时间不足，需要等待下一模拟日")


def update_agent_profile_after_action(conn, resident_id, action, reason, success=True, cost=None, schedule_context=None, tool_input=None):
    ensure_agent_profile_table(conn)
    profile = conn.execute(
        "SELECT energy, time_budget FROM agent_profiles WHERE resident_id = ?",
        (resident_id,),
    ).fetchone()
    if not profile:
        return

    cost = cost or calculate_action_cost(conn, resident_id, action, success=success)
    energy_delta = -int(cost["energy"])

    new_energy = clamp(int(profile["energy"]) + energy_delta)
    new_time_budget = clamp(int(profile["time_budget"]) - int(cost["time"]))
    new_mood = choose_mood(new_energy, action, success)
    task_label = {
        "move": "前往新地点并观察周围变化",
        "chat": "完成一次校园交流",
        "buy_sell": "完成一次校园消费或交易",
        "submit_policy": "提出校园治理建议",
        "create_group": "发起一项协作计划",
        "join_group": "加入一项协作计划",
        "leave_group": "调整自己的协作关系",
        "observe": "观察校园环境并记录线索",
    }.get(action, "根据当前状态继续行动")
    schedule_aligned = is_schedule_aligned(get_resident(conn, resident_id), action, tool_input or {}, schedule_context)
    if schedule_aligned is True:
        task_label = f"按日程执行：{schedule_context['current_task']}"
    elif schedule_aligned is False:
        task_label = f"自主选择暂缓日程：{schedule_context['current_task']}"
    perception = {
        "last_action": action,
        "last_reason": reason,
        "status": "成功" if success else "失败后转为观察",
        "action_cost": cost,
        "time_budget_remaining": new_time_budget,
        "schedule_adherence": schedule_aligned,
    }
    conn.execute(
        """
        UPDATE agent_profiles
        SET energy = ?, time_budget = ?, mood = ?, current_task = ?, perception = ?
        WHERE resident_id = ?
        """,
        (new_energy, new_time_budget, new_mood, task_label, json.dumps(perception, ensure_ascii=False), resident_id),
    )
    return {"energy_cost": int(cost["energy"]), "time_cost": int(cost["time"]), "energy_remaining": new_energy, "time_budget_remaining": new_time_budget}


def recover_agents_for_new_day(conn, day):
    ensure_agent_profile_table(conn)
    conn.execute(
        """
        UPDATE agent_profiles
        SET energy = CASE WHEN energy + 16 > 100 THEN 100 ELSE energy + 16 END,
            time_budget = 100,
            current_task = '开始新的一天，准备执行日程'
        """
    )
    add_event(conn, day, "daily_recovery", "新的一天开始：所有 Agent 恢复部分精力，并重置每日时间预算。")




CHENGDU_LATITUDE = 30.5728
CHENGDU_LONGITUDE = 104.0668

WEATHER_CODE_MAP = {
    0: "晴",
    1: "多云",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾",
    51: "小雨",
    53: "小雨",
    55: "小雨",
    56: "小雨",
    57: "小雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "小雨",
    67: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "小雪",
    80: "阵雨",
    81: "阵雨",
    82: "大雨",
    85: "小雪",
    86: "大雪",
    95: "雷雨",
    96: "雷雨",
    99: "雷雨",
}


def get_real_campus_time(now=None):
    tz = timezone(timedelta(hours=8))
    current = now or datetime.now(tz)
    if current.tzinfo is None:
        current = current.replace(tzinfo=tz)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    hour = current.hour
    if 5 <= hour <= 10:
        time_slot = "上午"
    elif 11 <= hour <= 13:
        time_slot = "中午"
    elif 14 <= hour <= 17:
        time_slot = "下午"
    elif 18 <= hour <= 23:
        time_slot = "晚上"
    else:
        time_slot = "深夜"

    month = current.month
    day = current.day
    if month in {2, 8}:
        semester_stage = "假期"
    elif month in {1, 7}:
        semester_stage = "考试周"
    elif month in {4, 11} and 10 <= day <= 25:
        semester_stage = "期中周"
    elif month in {3, 9} and day <= 20:
        semester_stage = "开学适应期"
    elif month in {5, 10}:
        semester_stage = "活动周"
    else:
        semester_stage = "平时周"

    return {
        "real_date": current.strftime("%Y-%m-%d"),
        "real_time": current.strftime("%H:%M:%S"),
        "weekday": weekdays[current.weekday()],
        "time_slot": time_slot,
        "semester_stage": semester_stage,
        "time_source": "system_clock",
        "hour": hour,
        "is_weekend": current.weekday() >= 5,
    }


def derive_environment_from_real_time(values, now=None):
    real_time = get_real_campus_time(now)
    hour = real_time["hour"]
    is_weekend = real_time["is_weekend"]
    time_slot = real_time["time_slot"]
    semester_stage = real_time["semester_stage"]
    values.update({key: real_time[key] for key in ["real_date", "real_time", "weekday", "time_slot", "semester_stage", "time_source"]})

    class_peak = 0 if is_weekend else (75 if 8 <= hour <= 11 or 14 <= hour <= 17 else 30)
    canteen_peak = 90 if 11 <= hour <= 13 or 17 <= hour <= 19 else (45 if 7 <= hour <= 9 else 25)
    library_base = 75 if semester_stage in {"期中周", "考试周"} else 45
    library_peak = library_base + (20 if 18 <= hour <= 22 else 0) - (15 if is_weekend and hour < 12 else 0)
    dorm_peak = 85 if hour >= 22 or hour <= 7 else (55 if 12 <= hour <= 14 else 35)
    playground_peak = 70 if 16 <= hour <= 20 and int(values.get("rainfall", 0)) < 20 else 25
    commercial_peak = 80 if 12 <= hour <= 14 or 18 <= hour <= 21 else 40

    exam_pressure = 82 if semester_stage == "考试周" else (65 if semester_stage == "期中周" else int(values.get("exam_pressure", 35)))
    activity_heat = 75 if semester_stage == "活动周" else int(values.get("activity_heat", 50))
    if is_weekend:
        activity_heat = min(100, activity_heat + 10)

    values.update({
        "exam_pressure": clamp(exam_pressure, 0, 100),
        "assignment_pressure": clamp(70 if semester_stage in {"期中周", "考试周"} else int(values.get("assignment_pressure", 40)), 0, 100),
        "study_atmosphere": clamp(55 + exam_pressure // 3 + (10 if time_slot == "晚上" else 0), 0, 100),
        "activity_heat": clamp(activity_heat, 0, 100),
        "event_name": "真实时间驱动校园状态",
        "event_intensity": clamp(activity_heat + (10 if time_slot in {"中午", "晚上"} else 0), 0, 100),
        "classroom_crowd": clamp(class_peak, 0, 100),
        "canteen_crowd": clamp(canteen_peak, 0, 100),
        "library_crowd": clamp(library_peak, 0, 100),
        "dorm_crowd": clamp(dorm_peak, 0, 100),
        "playground_crowd": clamp(playground_peak, 0, 100),
        "commercial_crowd": clamp(commercial_peak, 0, 100),
    })
    campus_flow = (values["classroom_crowd"] + values["canteen_crowd"] + values["commercial_crowd"] + values["playground_crowd"]) // 4
    values["campus_flow"] = clamp(campus_flow + (10 if time_slot in {"中午", "下午"} else 0), 0, 100)
    values["traffic_status"] = "拥堵" if values["campus_flow"] >= 75 else "正常"
    values["network_status"] = "拥堵" if values["dorm_crowd"] >= 75 and time_slot in {"晚上", "深夜"} else "稳定"
    values["resource_pressure"] = clamp((values["canteen_crowd"] + values["library_crowd"] + values["classroom_crowd"]) // 3, 0, 100)
    values["campus_mood"] = "紧张" if values["exam_pressure"] >= 75 else ("活跃" if values["activity_heat"] >= 70 else "平稳")
    values["consumption_index"] = round(max(0.5, min(1.8, 0.75 + values["commercial_crowd"] / 180 + values["canteen_crowd"] / 260)), 2)
    return values


def fetch_met_no_weather(latitude=CHENGDU_LATITUDE, longitude=CHENGDU_LONGITUDE):
    response = requests.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact",
        params={"lat": latitude, "lon": longitude},
        headers={"User-Agent": "campus-agent-simulation/1.0 github.com/mai555555/campus-agent-simulation"},
        timeout=12,
    )
    response.raise_for_status()
    series = response.json()["properties"]["timeseries"][0]
    details = series["data"]["instant"]["details"]
    next_hour = series["data"].get("next_1_hours", {})
    symbol = str(next_hour.get("summary", {}).get("symbol_code", "clearsky"))
    rainfall = max(0, min(100, int(round(float(next_hour.get("details", {}).get("precipitation_amount", 0) or 0) * 20))))
    temperature = int(round(float(details.get("air_temperature", 24))))

    if "thunder" in symbol:
        weather = "雷雨"
    elif "snow" in symbol:
        weather = "小雪"
    elif "rain" in symbol or "sleet" in symbol:
        weather = "小雨"
    elif "fog" in symbol:
        weather = "雾"
    elif "cloudy" in symbol:
        weather = "多云"
    else:
        weather = "晴"
    if temperature >= 32 and weather in {"晴", "多云"}:
        weather = "闷热"

    return {
        "weather": weather,
        "temperature": temperature,
        "rainfall": rainfall,
        "weather_source": "met-no",
        "weather_observed_at": str(series.get("time", "")),
        "raw": {"symbol_code": symbol, "wind_speed_10m": details.get("wind_speed"), "precipitation": rainfall / 20},
    }


def fetch_real_weather(latitude=CHENGDU_LATITUDE, longitude=CHENGDU_LONGITUDE):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,rain,weather_code,wind_speed_10m,relative_humidity_2m",
        "timezone": "Asia/Shanghai",
        "forecast_days": 1,
    }
    last_error = None
    data = None
    for attempt in range(2):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": "campus-agent-simulation/1.0"},
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            break
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Real weather request failed on attempt %s: %s", attempt + 1, exc)

    if data is None:
        logger.warning("Open-Meteo unavailable, trying Met.no fallback: %s", last_error)
        return fetch_met_no_weather(latitude, longitude)
    current = data.get("current", {})
    weather_code = int(current.get("weather_code", 0))
    precipitation = float(current.get("precipitation", 0) or 0)
    rain = float(current.get("rain", 0) or 0)
    rainfall = max(0, min(100, int(round(max(precipitation, rain) * 20))))
    temperature = int(round(float(current.get("temperature_2m", 24))))
    weather = WEATHER_CODE_MAP.get(weather_code, "多云")
    if temperature >= 32 and weather in {"晴", "多云"}:
        weather = "闷热"
    return {
        "weather": weather,
        "temperature": temperature,
        "rainfall": rainfall,
        "weather_source": "open-meteo",
        "weather_observed_at": str(current.get("time", "")),
        "raw": {
            "weather_code": weather_code,
            "wind_speed_10m": current.get("wind_speed_10m"),
            "relative_humidity_2m": current.get("relative_humidity_2m"),
            "precipitation": precipitation,
        },
    }


def derive_environment_from_weather(base_values):
    values = dict(base_values)
    rainfall = int(values.get("rainfall", 0) or 0)
    temperature = int(values.get("temperature", 24) or 24)
    weather = values.get("weather", "晴")
    activity_heat = int(values.get("activity_heat", 50) or 50)
    exam_pressure = int(values.get("exam_pressure", 35) or 35)
    assignment_pressure = int(values.get("assignment_pressure", 40) or 40)

    outdoor_penalty = min(35, rainfall // 2)
    heat_penalty = 10 if temperature >= 32 else 0
    values["playground_crowd"] = clamp(int(values.get("playground_crowd", 40)) - outdoor_penalty - heat_penalty, 10, 100)
    values["library_crowd"] = clamp(35 + exam_pressure // 2 + rainfall // 4, 10, 100)
    values["canteen_crowd"] = clamp(int(values.get("canteen_crowd", 50)) + (10 if rainfall > 20 else 0), 10, 100)
    values["commercial_crowd"] = clamp(35 + activity_heat // 2 - rainfall // 5 + (8 if temperature >= 30 else 0), 10, 100)
    values["campus_flow"] = clamp(55 + activity_heat // 3 - rainfall // 4, 10, 100)
    values["classroom_crowd"] = clamp(40 + assignment_pressure // 2, 10, 100)
    values["dorm_crowd"] = clamp(int(values.get("dorm_crowd", 45)) + (12 if rainfall > 20 else 0), 10, 100)
    values["study_atmosphere"] = clamp(35 + exam_pressure // 2 + assignment_pressure // 3, 10, 100)
    values["traffic_status"] = "拥堵" if values["campus_flow"] > 75 or rainfall > 40 else "正常"
    values["resource_pressure"] = clamp((values["canteen_crowd"] + values["library_crowd"] + values["classroom_crowd"]) // 3, 10, 100)
    values["network_status"] = "拥堵" if values["dorm_crowd"] > 75 else "稳定"
    values["safety_level"] = clamp(92 - rainfall // 8 - values["campus_flow"] // 12, 50, 100)
    values["consumption_index"] = round(max(0.5, min(1.8, 0.7 + activity_heat / 120 + values["commercial_crowd"] / 240)), 2)
    if exam_pressure > 75:
        values["campus_mood"] = "紧张"
    elif weather in {"小雨", "中雨", "大雨", "雷雨"}:
        values["campus_mood"] = "低落"
    elif activity_heat > 70:
        values["campus_mood"] = "活跃"
    else:
        values["campus_mood"] = "平稳"
    return values


def save_environment_values(conn, day, values):
    full_values = {key: values.get(key, default) for key, default in DEFAULT_ENV.items()}
    columns = list(DEFAULT_ENV.keys())
    assignments = ", ".join([f"{column} = excluded.{column}" for column in columns])
    placeholders = ", ".join(["?"] * (len(columns) + 1))
    conn.execute(
        f"""
        INSERT INTO campus_state (day, {', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(day) DO UPDATE SET {assignments}
        """,
        [day] + [full_values[column] for column in columns],
    )



def get_hierarchy_title(level):
    titles = {
        1: "普通成员",
        2: "小组/商家负责人",
        3: "管理与协调者",
        4: "学校/组织决策层",
    }
    try:
        level = int(level)
    except (TypeError, ValueError):
        level = 1
    return titles.get(level, "普通成员")


def infer_hierarchy(role):
    if any(word in role for word in ["学校", "后勤", "组织"]):
        return 4, "学校组织"
    if any(word in role for word in ["辅导员", "管理员", "老师"]):
        return 3, "学校管理"
    if any(word in role for word in ["商家", "创业", "学生会", "社团", "委员"]):
        return 2, "校园服务/学生组织"
    return 1, "学生"




def normalize_agent_hierarchy(conn):
    rows = conn.execute(
        """
        SELECT residents.id, residents.role, agent_profiles.hierarchy_level, agent_profiles.organization
        FROM residents
        JOIN agent_profiles ON agent_profiles.resident_id = residents.id
        """
    ).fetchall()
    for row in rows:
        level, organization = infer_hierarchy(row["role"])
        if int(row["hierarchy_level"]) != level or row["organization"] != organization:
            conn.execute(
                """
                UPDATE agent_profiles
                SET hierarchy_level = ?, organization = ?
                WHERE resident_id = ?
                """,
                (level, organization, row["id"]),
            )


def ensure_profile_meta(conn, resident_id):
    ensure_social_system_tables(conn)
    resident = conn.execute("SELECT role FROM residents WHERE id = ?", (resident_id,)).fetchone()
    if not resident:
        return None
    profile = conn.execute("SELECT * FROM agent_profiles WHERE resident_id = ?", (resident_id,)).fetchone()
    if not profile:
        level, organization = infer_hierarchy(resident["role"])
        conn.execute(
            """
            INSERT INTO agent_profiles (
                resident_id, gender, avatar_style, hierarchy_level, organization, skills, strategy
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (resident_id, "未设置", "简单卡通校园人物", level, organization, "{}", "{}"),
        )
        profile = conn.execute("SELECT * FROM agent_profiles WHERE resident_id = ?", (resident_id,)).fetchone()
    return profile


def action_score(action, success=True):
    base = {
        "chat": 2,
        "communicate": 2,
        "negotiate": 4,
        "collaborate": 5,
        "compete": 3,
        "buy_sell": 3,
        "submit_policy": 4,
        "create_group": 5,
        "join_group": 3,
        "leave_group": 1,
        "move": 1,
        "observe": 1,
    }.get(action, 1)
    return base if success else -1


def record_learning(conn, resident_id, action, outcome, score_delta, lesson):
    profile = ensure_profile_meta(conn, resident_id)
    if not profile:
        return None
    day = get_current_day(conn)
    skills = load_json_text(profile["skills"], {})
    strategy = load_json_text(profile["strategy"], {})
    action_key = str(action)
    lesson = format_learning_diary(action_key, outcome, lesson)
    skill = skills.get(action_key, {"uses": 0, "score": 0})
    if not isinstance(skill, dict):
        skill = {"uses": int(skill), "score": 0}
    skill["uses"] = int(skill.get("uses", 0)) + 1
    skill["score"] = int(skill.get("score", 0)) + int(score_delta)
    skills[action_key] = skill
    strategy[action_key] = {
        "last_outcome": outcome,
        "last_score_delta": int(score_delta),
        "lesson": lesson,
    }
    conn.execute(
        """
        UPDATE agent_profiles
        SET skills = ?, strategy = ?
        WHERE resident_id = ?
        """,
        (json.dumps(skills, ensure_ascii=False), json.dumps(strategy, ensure_ascii=False), resident_id),
    )
    conn.execute(
        """
        INSERT INTO agent_learning (resident_id, day, action, outcome, score_delta, lesson)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (resident_id, day, action_key, outcome, int(score_delta), lesson),
    )
    add_memory(
        conn,
        resident_id,
        day,
        lesson,
        importance=4,
        memory_type="semantic",
        tags=[action_key, "学习", "经验"],
        source="learning",
    )
    return {
        "resident_id": resident_id,
        "action": action_key,
        "outcome": outcome,
        "score_delta": int(score_delta),
        "lesson": lesson,
        "skills": skills,
        "strategy": strategy,
    }


def format_learning_diary(action, outcome, lesson):
    """Keep personal memories readable; never store raw tool output or JSON."""
    action_text = {
        "chat": "和校园里的其他人聊了聊",
        "move": "前往了新的校园空间",
        "buy_sell": "完成了一次交易",
        "observe": "观察了周围的校园环境",
        "submit_policy": "参与了校园事务讨论",
        "create_group": "发起了一项协作计划",
        "join_group": "加入了一项协作计划",
        "leave_group": "调整了自己的协作安排",
        "negotiate": "和他人协商了一件事情",
        "collaborate": "参与了一次合作",
        "compete": "参与了一次竞争",
    }.get(action, "完成了一次自主行动")
    default_insight = {
        "chat": "交流能帮助我更了解他人的想法，也值得继续保持联系。",
        "move": "不同空间的氛围和资源会影响我的下一步选择。",
        "buy_sell": "我需要继续留意价格、预算和实际需求。",
        "observe": "环境变化值得记下来，之后可以据此调整计划。",
    }.get(action, "这次经历会帮助我以后做出更合适的选择。")
    raw_lesson = str(lesson or "").strip()
    if "{" in raw_lesson or "[" in raw_lesson or "执行 " in raw_lesson:
        insight = default_insight
    else:
        insight = raw_lesson.replace("学习记录：", "").strip() or default_insight
    outcome_text = "顺利完成" if outcome in {"成功", "完成沟通", "加入协作", "回应沟通", "获胜"} else "留下了新的经验"
    return f"今天我{action_text}，这次行动{outcome_text}。{insight}"


def get_relationship_score(conn, from_id, to_id):
    row = conn.execute(
        "SELECT score FROM relationships WHERE from_resident_id = ? AND to_resident_id = ?",
        (from_id, to_id),
    ).fetchone()
    return int(row["score"]) if row else 0


def change_relationship(conn, from_id, to_id, delta, note):
    current = get_relationship_score(conn, from_id, to_id)
    next_score = clamp(current + delta)
    conn.execute(
        """
        INSERT INTO relationships (from_resident_id, to_resident_id, score, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(from_resident_id, to_resident_id)
        DO UPDATE SET score = excluded.score, notes = excluded.notes
        """,
        (from_id, to_id, next_score, note),
    )
    return next_score


def negotiate_between(conn, initiator_id, target_id, topic, proposal):
    ensure_social_system_tables(conn)
    initiator = get_resident(conn, initiator_id)
    target = get_resident(conn, target_id)
    if not initiator or not target:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    initiator_profile = ensure_profile_meta(conn, initiator_id)
    target_profile = ensure_profile_meta(conn, target_id)
    relationship = get_relationship_score(conn, initiator_id, target_id)
    level_bonus = int(initiator_profile["hierarchy_level"]) - int(target_profile["hierarchy_level"])
    success = relationship + level_bonus * 8 >= 25
    delta = 6 if success else 2
    status = "达成初步共识" if success else "保留分歧，等待更多条件"
    description = f"{initiator['name']} 与 {target['name']} 围绕「{topic}」协商：{proposal}。结果：{status}。"
    evolve_relationship(conn, initiator_id, target_id, "negotiation", f"协商议题：{topic}", delta, delta, 0 if success else 2)
    evolve_relationship(conn, target_id, initiator_id, "negotiation", f"回应协商：{topic}", max(1, delta - 1), max(1, delta - 1), 0 if success else 2)
    add_event(conn, get_current_day(conn), "negotiation", description)
    record_learning(conn, initiator_id, "negotiate", status, action_score("negotiate", success), f"围绕「{topic}」协商，学会根据关系和层级调整提案。")
    record_learning(conn, target_id, "negotiate", status, action_score("negotiate", success), f"回应「{topic}」协商，形成对合作条件的判断。")
    conn.commit()
    return {
        "type": "negotiation",
        "success": success,
        "status": status,
        "relationship_after": get_relationship_score(conn, initiator_id, target_id),
        "description": description,
    }


def create_collaboration(conn, leader_id, member_ids, title, goal):
    ensure_social_system_tables(conn)
    ids = [leader_id] + [mid for mid in member_ids if mid != leader_id]
    residents = conn.execute(
        f"SELECT id, name FROM residents WHERE id IN ({','.join(['?'] * len(ids))})",
        ids,
    ).fetchall()
    if len(residents) != len(set(ids)):
        raise HTTPException(status_code=404, detail="有 Agent 不存在")
    score = 10 + len(ids) * 3
    conn.execute(
        """
        INSERT INTO collaborations (title, leader_id, member_ids, goal, status, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, leader_id, json.dumps(ids, ensure_ascii=False), goal, "active", score),
    )
    roles = {str(member_id): ("负责人" if member_id == leader_id else "成员") for member_id in ids}
    group_cursor = conn.execute(
        """
        INSERT INTO group_goals (name, group_type, leader_id, member_ids, roles, shared_goal, deadline_day, current_plan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, "协作小组", leader_id, json.dumps(ids, ensure_ascii=False), json.dumps(roles, ensure_ascii=False), goal, get_current_day(conn) + 10, "成员按各自任务推进，并在每日模拟后汇总进度。"),
    )
    for from_id in ids:
        for to_id in ids:
            if from_id != to_id:
                evolve_relationship(conn, from_id, to_id, "collaboration", f"参与协作：{title}", 4, 5, -1)
        record_learning(conn, from_id, "collaborate", "加入协作", action_score("collaborate", True), f"参与「{title}」，围绕「{goal}」分工合作。")
    add_event(conn, get_current_day(conn), "collaboration", f"协作项目「{title}」启动，目标：{goal}。")
    conn.commit()
    return {"title": title, "leader_id": leader_id, "member_ids": ids, "goal": goal, "status": "active"}


def join_group_goal(conn, resident_id, group_id):
    ensure_social_system_tables(conn)
    group = conn.execute("SELECT * FROM group_goals WHERE id = ? AND status = 'active'", (group_id,)).fetchone()
    if not group:
        raise ValueError("没有可加入的活跃小组")
    members = load_json_text(group["member_ids"], [])
    if resident_id in members:
        return {"group_id": group_id, "message": "已经是该小组成员"}
    members.append(resident_id)
    roles = load_json_text(group["roles"], {})
    roles[str(resident_id)] = "成员"
    conn.execute("UPDATE group_goals SET member_ids = ?, roles = ? WHERE id = ?", (json.dumps(members, ensure_ascii=False), json.dumps(roles, ensure_ascii=False), group_id))
    for member_id in members:
        if member_id != resident_id:
            evolve_relationship(conn, resident_id, member_id, "group_join", f"加入小组：{group['name']}", 2, 3, -1)
            evolve_relationship(conn, member_id, resident_id, "group_join", f"新成员加入：{group['name']}", 1, 2, 0)
    add_event(conn, get_current_day(conn), "group_join", f"Agent {resident_id} 加入小组「{group['name']}」。")
    return {"group_id": group_id, "group_name": group["name"], "member_ids": members, "message": "加入小组成功"}


def leave_group_goal(conn, resident_id, group_id):
    ensure_social_system_tables(conn)
    group = conn.execute("SELECT * FROM group_goals WHERE id = ? AND status = 'active'", (group_id,)).fetchone()
    if not group:
        raise ValueError("没有可退出的活跃小组")
    members = load_json_text(group["member_ids"], [])
    if resident_id not in members:
        raise ValueError("当前不是该小组成员")
    if int(group["leader_id"]) == resident_id:
        raise ValueError("负责人不能直接退出，请先由小组重新选择负责人")
    members.remove(resident_id)
    roles = load_json_text(group["roles"], {})
    roles.pop(str(resident_id), None)
    conn.execute("UPDATE group_goals SET member_ids = ?, roles = ? WHERE id = ?", (json.dumps(members, ensure_ascii=False), json.dumps(roles, ensure_ascii=False), group_id))
    add_event(conn, get_current_day(conn), "group_leave", f"Agent {resident_id} 退出小组「{group['name']}」。")
    return {"group_id": group_id, "group_name": group["name"], "member_ids": members, "message": "退出小组成功"}
    return {"type": "collaboration", "title": title, "leader_id": leader_id, "member_ids": ids, "goal": goal, "score": score, "status": "active", "group_goal_id": group_cursor.lastrowid}


def create_competition(conn, participant_ids, title, metric):
    ensure_social_system_tables(conn)
    if len(participant_ids) < 2:
        raise HTTPException(status_code=400, detail="竞争至少需要 2 个 Agent")
    rows = conn.execute(
        f"SELECT residents.id, residents.name, residents.money, agent_profiles.energy, agent_profiles.skills FROM residents JOIN agent_profiles ON agent_profiles.resident_id = residents.id WHERE residents.id IN ({','.join(['?'] * len(participant_ids))})",
        participant_ids,
    ).fetchall()
    if len(rows) != len(set(participant_ids)):
        raise HTTPException(status_code=404, detail="有 Agent 不存在")
    scores = []
    for row in rows:
        skills = load_json_text(row["skills"], {})
        compete_skill = skills.get("compete", {}) if isinstance(skills, dict) else {}
        skill_score = compete_skill.get("score", 0) if isinstance(compete_skill, dict) else 0
        score = int(row["energy"]) + int(row["money"]) // 10 + int(skill_score) + random.randint(0, 12)
        scores.append({"id": row["id"], "name": row["name"], "score": score})
    scores.sort(key=lambda item: item["score"], reverse=True)
    winner = scores[0]
    result = f"{winner['name']} 在「{title}」中以 {winner['score']} 分暂时领先，评价指标：{metric}。"
    conn.execute(
        """
        INSERT INTO competitions (title, participant_ids, metric, winner_id, result)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, json.dumps(participant_ids, ensure_ascii=False), metric, winner["id"], result),
    )
    for item in scores:
        won = item["id"] == winner["id"]
        record_learning(conn, item["id"], "compete", "获胜" if won else "参与竞争", action_score("compete", won), f"参与「{title}」竞争，理解自身在「{metric}」上的优势和差距。")
        for opponent in scores:
            if opponent["id"] != item["id"]:
                evolve_relationship(conn, item["id"], opponent["id"], "competition", f"参与竞争：{title}", 1 if won else 0, 0, 3)
    add_event(conn, get_current_day(conn), "competition", result)
    conn.commit()
    return {"type": "competition", "title": title, "metric": metric, "winner_id": winner["id"], "scores": scores, "result": result}


class MoveRequest(BaseModel):
    resident_id: int
    destination: str


class ChatRequest(BaseModel):
    speaker_id: int
    listener_id: int
    message: str


class NegotiateRequest(BaseModel):
    initiator_id: int
    target_id: int
    topic: str
    proposal: str


class CollaborateRequest(BaseModel):
    leader_id: int
    member_ids: list[int] = Field(default_factory=list)
    title: str
    goal: str


class CompeteRequest(BaseModel):
    participant_ids: list[int]
    title: str
    metric: str = "综合表现"


class LongTermGoalRequest(BaseModel):
    resident_id: int
    title: str
    category: str = "general"
    deadline_day: Optional[int] = None


class GroupGoalRequest(BaseModel):
    name: str
    group_type: str = "临时小组"
    leader_id: int
    member_ids: list[int] = Field(default_factory=list)
    shared_goal: str
    deadline_day: Optional[int] = None
    current_plan: str = "成员根据分工推进任务，并在每日模拟后汇总进度。"


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
    time_slot: Optional[str] = None
    weekday: Optional[str] = None
    real_date: Optional[str] = None
    real_time: Optional[str] = None
    time_source: Optional[str] = None
    temperature: Optional[int] = Field(default=None, ge=-20, le=45)
    rainfall: Optional[int] = Field(default=None, ge=0, le=100)
    exam_pressure: Optional[int] = Field(default=None, ge=0, le=100)
    assignment_pressure: Optional[int] = Field(default=None, ge=0, le=100)
    study_atmosphere: Optional[int] = Field(default=None, ge=0, le=100)
    activity_heat: Optional[int] = Field(default=None, ge=0, le=100)
    event_name: Optional[str] = None
    event_intensity: Optional[int] = Field(default=None, ge=0, le=100)
    campus_flow: Optional[int] = Field(default=None, ge=0, le=100)
    classroom_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    canteen_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    library_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    dorm_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    playground_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    commercial_crowd: Optional[int] = Field(default=None, ge=0, le=100)
    traffic_status: Optional[str] = None
    network_status: Optional[str] = None
    safety_level: Optional[int] = Field(default=None, ge=0, le=100)
    resource_pressure: Optional[int] = Field(default=None, ge=0, le=100)
    campus_mood: Optional[str] = None
    consumption_index: Optional[float] = Field(default=None, ge=0.1, le=3.0)


class CampusEventRequest(BaseModel):
    title: str
    event_type: str = "校园活动"
    intensity: int = Field(default=50, ge=1, le=100)
    target_spaces: list[str] = Field(default_factory=list)
    effects: dict = Field(default_factory=dict)


class SpaceStatusRequest(BaseModel):
    status: str


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def ensure_campus_state_table(conn):
    conn.executescript(CAMPUS_STATE_SQL)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(campus_state)").fetchall()}
    for column, column_type in ENV_COLUMN_TYPES.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE campus_state ADD COLUMN {column} {column_type}")


def ensure_space_system(conn):
    conn.executescript(SPACE_SYSTEM_SQL)
    for space in DEFAULT_SPACES:
        conn.execute(
            """
            INSERT OR IGNORE INTO campus_spaces
            (code, name, location, capacity, open_hour, close_hour, status, crowd_field, purpose)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            space,
        )


def ensure_agent_news_system(conn):
    conn.executescript(AGENT_NEWS_SQL)


def ensure_external_information_system(conn):
    conn.executescript(EXTERNAL_INFORMATION_SQL)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(agent_information)").fetchall()}
    for column, column_type in AGENT_INFORMATION_COLUMNS.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE agent_information ADD COLUMN {column} {column_type}")


def get_environment_hour(env):
    real_time = str(env.get("real_time") or "")
    try:
        return int(real_time.split(":", 1)[0])
    except (TypeError, ValueError):
        return {"上午": 9, "中午": 12, "下午": 15, "晚上": 20, "深夜": 2}.get(env.get("time_slot"), 9)


def get_active_campus_events(conn, day=None):
    day = day or get_current_day(conn)
    return rows_to_dicts(
        conn.execute(
            "SELECT * FROM campus_events WHERE day = ? AND status = 'active' ORDER BY id DESC",
            (day,),
        ).fetchall()
    )


def get_space_snapshot(conn, day=None):
    ensure_space_system(conn)
    env = get_campus_environment(conn, day)
    hour = get_environment_hour(env)
    active_events = get_active_campus_events(conn, day)
    actual_counts = {
        row["location"]: row["count"]
        for row in conn.execute("SELECT location, COUNT(*) AS count FROM residents GROUP BY location").fetchall()
    }
    spaces = []
    for row in conn.execute("SELECT * FROM campus_spaces ORDER BY code").fetchall():
        space = dict(row)
        capacity = int(space["capacity"])
        crowd_percent = clamp(env.get(space["crowd_field"], env.get("campus_flow", 50)))
        estimated_occupancy = round(capacity * crowd_percent / 100)
        actual_agents = int(actual_counts.get(space["location"], 0))
        occupancy = max(actual_agents, estimated_occupancy)
        event_status = None
        relevant_events = []
        for event in active_events:
            targets = json.loads(event["target_spaces"])
            effects = json.loads(event["effects"])
            if space["location"] in targets:
                relevant_events.append(event["title"])
                event_status = effects.get("space_status", event_status)
        within_hours = space["open_hour"] <= hour < space["close_hour"] if space["close_hour"] != 24 else hour >= space["open_hour"]
        base_status = space["status"]
        if base_status != "开放":
            effective_status = base_status
        elif event_status:
            effective_status = event_status
        elif not within_hours:
            effective_status = "已关闭"
        elif occupancy >= capacity:
            effective_status = "满员"
        else:
            effective_status = "开放"
        space.update(
            {
                "crowd_percent": crowd_percent,
                "actual_agents": actual_agents,
                "estimated_occupancy": estimated_occupancy,
                "occupancy": occupancy,
                "available_slots": max(0, capacity - occupancy),
                "effective_status": effective_status,
                "active_events": relevant_events,
            }
        )
        spaces.append(space)
    return {"hour": hour, "spaces": spaces, "active_events": active_events}


def assert_destination_available(conn, destination):
    if destination not in VALID_LOCATIONS:
        raise ValueError("地点不存在")
    snapshot = get_space_snapshot(conn)
    space = next((item for item in snapshot["spaces"] if item["location"] == destination), None)
    if not space:
        return
    if space["effective_status"] != "开放":
        raise ValueError(f"{destination}当前{space['effective_status']}，Agent 需要调整计划")


def apply_campus_event_effects(conn, day, effects):
    updates = effects.get("environment_updates", {}) if isinstance(effects, dict) else {}
    allowed = set(DEFAULT_ENV.keys())
    updates = {key: value for key, value in updates.items() if key in allowed}
    if not updates:
        return {}
    get_campus_environment(conn, day)
    set_clause = ", ".join([f"{key} = ?" for key in updates])
    conn.execute(f"UPDATE campus_state SET {set_clause} WHERE day = ?", list(updates.values()) + [day])
    return updates


def default_event_configuration(env, event_type, intensity, target_spaces):
    intensity = clamp(intensity, 1, 100)
    targets = target_spaces or {
        "设施故障": ["图书馆"],
        "天气预警": ["操场"],
        "大型活动": ["操场", "教学楼"],
        "考试通知": ["图书馆", "教学楼"],
    }.get(event_type, [])
    updates = {
        "event_name": event_type,
        "event_intensity": intensity,
    }
    space_status = "开放"
    if event_type == "设施故障":
        space_status = "维护中"
        updates.update(
            {
                "resource_pressure": clamp(int(env["resource_pressure"]) + intensity // 2),
                "campus_mood": "关注中",
            }
        )
    elif event_type == "天气预警":
        space_status = "暂停开放"
        updates.update(
            {
                "playground_crowd": clamp(int(env["playground_crowd"]) - intensity // 2),
                "campus_flow": clamp(int(env["campus_flow"]) - intensity // 4),
                "campus_mood": "谨慎",
            }
        )
    elif event_type == "大型活动":
        updates.update(
            {
                "activity_heat": clamp(int(env["activity_heat"]) + intensity // 3),
                "campus_flow": clamp(int(env["campus_flow"]) + intensity // 4),
                "campus_mood": "活跃",
            }
        )
    elif event_type == "考试通知":
        updates.update(
            {
                "exam_pressure": clamp(int(env["exam_pressure"]) + intensity // 3),
                "study_atmosphere": clamp(int(env["study_atmosphere"]) + intensity // 4),
                "library_crowd": clamp(int(env["library_crowd"]) + intensity // 3),
                "campus_mood": "紧张",
            }
        )
    return targets, {"space_status": space_status, "environment_updates": updates}


def create_campus_event(conn, day, title, event_type, intensity, target_spaces=None, effects=None):
    ensure_space_system(conn)
    env = get_campus_environment(conn, day)
    targets, default_effects = default_event_configuration(env, event_type, intensity, target_spaces or [])
    final_effects = effects or default_effects
    cursor = conn.execute(
        """
        INSERT INTO campus_events (day, title, event_type, intensity, target_spaces, effects)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            day,
            title,
            event_type,
            intensity,
            json.dumps(targets, ensure_ascii=False),
            json.dumps(final_effects, ensure_ascii=False),
        ),
    )
    updates = apply_campus_event_effects(conn, day, final_effects)
    description = f"校园事件《{title}》已触发，类型：{event_type}，影响空间：{targets or '全校'}。"
    add_event(conn, day, "campus_event", description)
    conn.commit()
    return {"id": cursor.lastrowid, "title": title, "event_type": event_type, "target_spaces": targets, "effects": final_effects, "environment_updates": updates}


def maybe_generate_environment_event(conn, day):
    if get_active_campus_events(conn, day):
        return None
    env = get_campus_environment(conn, day)
    if int(env.get("rainfall", 0)) >= 60:
        return create_campus_event(conn, day, "降雨天气预警", "天气预警", 65, ["操场"])
    if int(env.get("resource_pressure", 0)) >= 80:
        return create_campus_event(conn, day, "设施资源紧张", "设施故障", 55, ["图书馆"])
    if int(env.get("activity_heat", 0)) >= 75 and random.random() < 0.45:
        return create_campus_event(conn, day, "校园主题活动", "大型活动", 60, ["操场", "教学楼"])
    return None


def build_environment_modules(env):
    return {
        "TimeWeather": {
            "description": "时间、天气和学期阶段",
            "weather": env["weather"],
            "temperature": env["temperature"],
            "rainfall": env["rainfall"],
            "weather_source": env["weather_source"],
            "weather_observed_at": env["weather_observed_at"],
            "real_date": env.get("real_date", ""),
            "real_time": env.get("real_time", ""),
            "time_source": env.get("time_source", "simulation"),
            "weekday": env["weekday"],
            "time_slot": env["time_slot"],
            "semester_stage": env["semester_stage"],
        },
        "Academic": {
            "description": "学习氛围、考试压力和作业压力",
            "exam_pressure": env["exam_pressure"],
            "assignment_pressure": env["assignment_pressure"],
            "study_atmosphere": env["study_atmosphere"],
        },
        "Activity": {
            "description": "校园活动与事件热度",
            "activity_heat": env["activity_heat"],
            "event_name": env["event_name"],
            "event_intensity": env["event_intensity"],
        },
        "Crowd": {
            "description": "校园各空间人流和拥挤度",
            "campus_flow": env["campus_flow"],
            "classroom_crowd": env["classroom_crowd"],
            "canteen_crowd": env["canteen_crowd"],
            "library_crowd": env["library_crowd"],
            "dorm_crowd": env["dorm_crowd"],
            "playground_crowd": env["playground_crowd"],
            "commercial_crowd": env["commercial_crowd"],
        },
        "Infrastructure": {
            "description": "交通、网络、资源和安全秩序",
            "traffic_status": env["traffic_status"],
            "network_status": env["network_status"],
            "safety_level": env["safety_level"],
            "resource_pressure": env["resource_pressure"],
        },
        "Business": {
            "description": "商业消费和校园整体情绪",
            "consumption_index": env["consumption_index"],
            "campus_mood": env["campus_mood"],
        },
    }


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
        full_values = {key: values.get(key, default) for key, default in DEFAULT_ENV.items()}
        columns = ["day"] + list(DEFAULT_ENV.keys())
        placeholders = ", ".join(["?"] * len(columns))
        conn.execute(
            f"INSERT INTO campus_state ({', '.join(columns)}) VALUES ({placeholders})",
            [day] + [full_values[key] for key in DEFAULT_ENV.keys()],
        )
        conn.commit()
        row = conn.execute("SELECT * FROM campus_state WHERE day = ?", (day,)).fetchone()

    env = dict(row)
    env["modules"] = build_environment_modules(env)
    return env


def retrieve_relevant_memories(conn, resident_id, query_terms=None, limit=6):
    """Rank personal memories by relevance, importance, recency, and prior reuse."""
    ensure_memory_columns(conn)
    current_day = get_current_day(conn)
    terms = [str(term).strip() for term in (query_terms or []) if str(term).strip()]
    rows = conn.execute(
        """
        SELECT id, day, content, importance, memory_type, tags, source,
               access_count, last_accessed_at, created_at
        FROM memories
        WHERE resident_id = ? AND day <= ?
        ORDER BY id DESC
        LIMIT 120
        """,
        (resident_id, current_day),
    ).fetchall()
    type_bonus = {"relationship": 18, "semantic": 15, "episodic": 9, "working": 5}
    ranked = []
    for row in rows:
        memory = dict(row)
        text = f"{memory.get('tags', '')} {memory['content']}"
        matches = sum(1 for term in terms if term in text)
        age = max(0, current_day - int(memory["day"]))
        score = (
            int(memory["importance"]) * 10
            + type_bonus.get(memory.get("memory_type"), 6)
            + min(int(memory.get("access_count") or 0), 5) * 2
            + matches * 18
            + max(0, 18 - age * 3)
        )
        memory["relevance_score"] = score
        ranked.append(memory)
    selected = sorted(ranked, key=lambda item: item["relevance_score"], reverse=True)[:limit]
    if selected:
        placeholders = ", ".join("?" for _ in selected)
        conn.execute(
            f"UPDATE memories SET access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            [item["id"] for item in selected],
        )
        for memory in selected:
            memory["access_count"] = int(memory.get("access_count") or 0) + 1
            memory["last_accessed_at"] = "本次决策检索"
    return selected


def get_recent_context(conn, resident_id, limit=6, query_terms=None):
    memories = retrieve_relevant_memories(conn, resident_id, query_terms=query_terms, limit=limit)
    events = conn.execute(
        """
        SELECT day, event_type, description, created_at
        FROM city_events
        WHERE day <= ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (get_current_day(conn), limit),
    ).fetchall()
    return {
        "memories": rows_to_dicts(memories),
        "memory_retrieval_terms": query_terms or [],
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




def perceive_environment(conn, resident_id):
    resident = get_resident(conn, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    day = get_current_day(conn)
    env = get_campus_environment(conn, day)
    module_state = get_agent_module_state(conn, resident_id)
    schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
    location = resident["location"]
    crowd_by_location = {
        "教学楼": env.get("classroom_crowd", 50),
        "图书馆": env.get("library_crowd", 50),
        "食堂": env.get("canteen_crowd", 50),
        "宿舍区": env.get("dorm_crowd", 50),
        "操场": env.get("playground_crowd", 50),
        "商业街": env.get("commercial_crowd", 50),
        "校务处": env.get("campus_flow", 50),
    }
    local_crowd = crowd_by_location.get(location, env.get("campus_flow", 50))
    space_snapshot = get_space_snapshot(conn, day)
    current_space = next((space for space in space_snapshot["spaces"] if space["location"] == location), None)
    perception = {
        "day": day,
        "location": location,
        "weather": env.get("weather"),
        "temperature": env.get("temperature"),
        "rainfall": env.get("rainfall"),
        "local_crowd": local_crowd,
        "campus_mood": env.get("campus_mood"),
        "exam_pressure": env.get("exam_pressure"),
        "activity_heat": env.get("activity_heat"),
        "event_name": env.get("event_name"),
        "network_status": env.get("network_status"),
        "safety_level": env.get("safety_level"),
        "current_space": current_space,
        "active_events": space_snapshot["active_events"],
        "agent_energy": module_state["modules"]["Physical"]["energy"],
        "agent_mood": module_state["modules"]["Physical"]["mood"],
        "current_task": module_state["modules"]["Mental"]["task"],
    }
    conn.execute(
        "UPDATE agent_profiles SET perception = ? WHERE resident_id = ?",
        (json.dumps(perception, ensure_ascii=False), resident_id),
    )
    add_memory(
        conn,
        resident_id,
        day,
        f"感知环境：当前位置 {location}，天气 {perception['weather']}，局部拥挤度 {local_crowd}，校园情绪 {perception['campus_mood']}。",
        importance=1,
    )
    conn.commit()
    return perception


def apply_environment_feedback(conn, resident_id, action, result):
    day = get_current_day(conn)
    env = get_campus_environment(conn, day)
    updates = {}
    description = result.get("description", "") if isinstance(result, dict) else ""

    if action == "move":
        updates["campus_flow"] = clamp(int(env.get("campus_flow", 55)) + 1, 0, 100)
        if "图书馆" in description:
            updates["library_crowd"] = clamp(int(env.get("library_crowd", 45)) + 2, 0, 100)
        elif "食堂" in description:
            updates["canteen_crowd"] = clamp(int(env.get("canteen_crowd", 50)) + 2, 0, 100)
        elif "操场" in description:
            updates["playground_crowd"] = clamp(int(env.get("playground_crowd", 40)) + 2, 0, 100)
        elif "商业街" in description:
            updates["commercial_crowd"] = clamp(int(env.get("commercial_crowd", 50)) + 2, 0, 100)
    elif action == "chat":
        updates["campus_mood"] = "活跃"
        updates["activity_heat"] = clamp(int(env.get("activity_heat", 50)) + 1, 0, 100)
    elif action == "buy_sell":
        updates["consumption_index"] = round(min(1.8, float(env.get("consumption_index", 1.0)) + 0.03), 2)
        updates["commercial_crowd"] = clamp(int(env.get("commercial_crowd", 50)) + 1, 0, 100)
    elif action == "submit_policy":
        updates["resource_pressure"] = clamp(int(env.get("resource_pressure", 45)) - 1, 0, 100)
        updates["campus_mood"] = "有序"
    elif action in {"create_group", "join_group"}:
        updates["activity_heat"] = clamp(int(env.get("activity_heat", 50)) + 3, 0, 100)
        updates["campus_mood"] = "活跃"
    elif action == "leave_group":
        updates["activity_heat"] = clamp(int(env.get("activity_heat", 50)) - 1, 0, 100)
    elif action == "observe":
        updates["study_atmosphere"] = clamp(int(env.get("study_atmosphere", 60)) + 1, 0, 100)

    if updates:
        set_clause = ", ".join([f"{key} = ?" for key in updates])
        conn.execute(f"UPDATE campus_state SET {set_clause} WHERE day = ?", list(updates.values()) + [day])
        add_event(conn, day, "environment_feedback", f"Agent 行动 {action} 反馈到环境：{updates}")
        conn.commit()
    return updates


def record_simulation_log(conn, resident_id, perception, decision_data, execution, feedback):
    """Persist the exact inputs and outcome that explain one autonomous action."""
    ensure_social_system_tables(conn)
    memory_context = decision_data.get("memory_context", {})
    conn.execute(
        """
        INSERT INTO simulation_action_logs
        (day, resident_id, perception, retrieved_memories, decision, execution, environment_feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            get_current_day(conn),
            resident_id,
            json.dumps(perception or {}, ensure_ascii=False),
            json.dumps(memory_context.get("memories", []), ensure_ascii=False),
            json.dumps(decision_data.get("decision", {}), ensure_ascii=False),
            json.dumps(execution or {}, ensure_ascii=False),
            json.dumps(feedback or {}, ensure_ascii=False),
        ),
    )


def run_lifecycle_step(conn, resident_id):
    before = get_agent_module_state(conn, resident_id)
    perception = perceive_environment(conn, resident_id)
    decision_data = decide_agent_action(conn, resident_id)
    execution = execute_decision(conn, resident_id, decision_data["decision"])
    feedback = apply_environment_feedback(conn, resident_id, execution["action"], execution["result"])
    record_simulation_log(conn, resident_id, perception, decision_data, execution, feedback)
    conn.commit()
    after = get_agent_module_state(conn, resident_id)
    env_after = get_campus_environment(conn)
    return {
        "loop": "perceive -> decide -> act -> feedback -> memory",
        "resident_id": resident_id,
        "before": before,
        "perception": perception,
        "decision": decision_data["decision"],
        "action_result": execution,
        "environment_feedback": feedback,
        "after": after,
        "environment_after": env_after,
    }


def decide_agent_action(conn, resident_id):
    ensure_social_system_tables(conn)
    resident = get_resident(conn, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    day = get_current_day(conn)
    env = get_campus_environment(conn, day)
    module_state = get_agent_module_state(conn, resident_id)
    schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
    memory_terms = [
        resident["location"],
        resident["goal"],
        env.get("weather", ""),
        env.get("event_name", ""),
        schedule_context.get("current_task", ""),
        schedule_context.get("location", ""),
    ]
    context = get_recent_context(conn, resident_id, query_terms=memory_terms)
    other_agents = conn.execute(
        "SELECT id, name, role, location FROM residents WHERE id != ? ORDER BY id",
        (resident_id,),
    ).fetchall()
    active_groups = conn.execute(
        "SELECT id, name, shared_goal, member_ids, deadline_day FROM group_goals WHERE status = 'active' ORDER BY id DESC LIMIT 8"
    ).fetchall()

    prompt = f"""
你正在驱动一个校园封闭世界中的 Agent。

当前日期：第 {day} 天
校园环境：{json.dumps(env, ensure_ascii=False)}
空间状态（容量、开放状态和事件）：{json.dumps(get_space_snapshot(conn, day), ensure_ascii=False)}
当前 Agent：{json.dumps(dict(resident), ensure_ascii=False)}
其他 Agent：{json.dumps(rows_to_dicts(other_agents), ensure_ascii=False)}
可加入或协作的活跃小组：{json.dumps(rows_to_dicts(active_groups), ensure_ascii=False)}
近期记忆和事件：{json.dumps(context, ensure_ascii=False)}
Agent 六模块状态：{json.dumps(module_state, ensure_ascii=False)}
当前日程提示：{json.dumps(schedule_context, ensure_ascii=False)}。日程、天气、关系和资源都是你需要权衡的信息，不是强制命令。你必须自主选择行动，也要在 reason 中说明是否愿意承担暂缓日程、绕开拥挤或消耗资源的后果。

请只返回严格 JSON，不要解释，不要 Markdown。
可选 action 只能是：move、chat、buy_sell、submit_policy、observe、create_group、join_group、leave_group。
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
create_group: {{"title": "小组名称", "goal": "共同目标", "member_ids": [2, 3]}}
join_group: {{"group_id": 1}}
leave_group: {{"group_id": 1}}
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

    decision = attach_schedule_guidance(schedule_context, decision)

    return {
        "resident": dict(resident),
        "decision": decision,
        "schedule_context": schedule_context,
        "memory_context": context,
    }


def execute_decision(conn, resident_id, decision):
    resident = get_resident(conn, resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    action = str(decision.get("action", "observe")).strip()
    reason = str(decision.get("reason", "自主决策"))
    tool_input = decision.get("tool_input") or {}
    day = get_current_day(conn)
    module_state = get_agent_module_state(conn, resident_id)
    schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
    planned_cost = calculate_action_cost(conn, resident_id, action, tool_input, success=True)

    try:
        ensure_action_affordable(conn, resident_id, planned_cost, action)
        if action == "move":
            destination = tool_input.get("destination", resident["location"])
            assert_destination_available(conn, destination)
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
        elif action == "create_group":
            title = str(tool_input.get("title") or f"{resident['name']}的协作小组")[:40]
            goal = str(tool_input.get("goal") or resident["goal"])[:180]
            member_ids = [int(member_id) for member_id in tool_input.get("member_ids", []) if str(member_id).isdigit()]
            member_ids = [member_id for member_id in member_ids if member_id != resident_id][:5]
            if not member_ids:
                raise ValueError("发起协作至少需要邀请一位其他 Agent")
            group = create_collaboration(conn, resident_id, member_ids, title, goal)
            result = {"message": "协作小组已发起", "description": f"{resident['name']} 发起小组「{title}」。", "group": group}
        elif action == "join_group":
            group_id = int(tool_input.get("group_id"))
            group = join_group_goal(conn, resident_id, group_id)
            result = {"message": group["message"], "description": f"{resident['name']} 加入小组「{group['group_name']}」。", "group": group}
        elif action == "leave_group":
            group_id = int(tool_input.get("group_id"))
            group = leave_group_goal(conn, resident_id, group_id)
            result = {"message": group["message"], "description": f"{resident['name']} 退出小组「{group['group_name']}」。", "group": group}
        elif action == "observe":
            focus = tool_input.get("focus", "校园状态")
            text = f"{resident['name']} 观察 {focus}。原因：{reason}"
            add_event(conn, day, "agent_observe", text)
            add_memory(conn, resident_id, day, text, importance=1)
            conn.commit()
            result = {"message": "观察完成", "description": text}
        else:
            raise ValueError(f"不支持的自主行动：{action}")
    except Exception as exc:
        # PostgreSQL marks the current transaction as unusable after a failed
        # statement. Roll it back before recording this Agent's failed action.
        conn.rollback()
        text = f"{resident['name']} 自主选择执行 {action}，但未能完成：{exc}。本轮不替 Agent 改选其他行为。"
        add_event(conn, day, "agent_action_failed", text)
        add_memory(conn, resident_id, day, text, importance=1)
        failed_cost = calculate_action_cost(conn, resident_id, action, tool_input, success=False)
        action_cost = update_agent_profile_after_action(conn, resident_id, action, reason, success=False, cost=failed_cost, schedule_context=schedule_context, tool_input=tool_input)
        conn.commit()
        result = {"message": "行动失败，保留自主选择结果", "description": text, "error": str(exc)}

    success = "error" not in result
    learned_action = action
    if success:
        action_cost = update_agent_profile_after_action(conn, resident_id, action, reason, success=True, cost=planned_cost, schedule_context=schedule_context, tool_input=tool_input)
    social_update = None
    if success and action == "chat":
        try:
            target_id = int(tool_input.get("target_id"))
            social_update = {
                "speaker": evolve_relationship(conn, resident_id, target_id, "chat", "日常交流", 3, 2, -1),
                "listener": evolve_relationship(conn, target_id, resident_id, "chat", "回应交流", 2, 2, -1),
            }
        except Exception as exc:
            conn.rollback()
            social_update = {"error": str(exc)}
    goal_update = advance_personal_goal(conn, resident_id, learned_action, success)
    learning = record_learning(
        conn,
        resident_id,
        learned_action,
        "成功" if success else "失败",
        action_score(learned_action, success),
        f"执行 {learned_action} 后得到反馈：{result}",
    )
    conn.commit()

    return {
        "resident_id": resident_id,
        "action": action,
        "reason": reason,
        "result": result,
        "success": success,
        "learning": learning,
        "social_update": social_update,
        "long_term_goal": goal_update,
        "action_cost": action_cost,
        "schedule_context": schedule_context,
    }


def auto_update_environment(conn, day):
    previous = get_campus_environment(conn, day)
    weather = random.choice(["晴", "多云", "小雨", "闷热", "大风"])
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][(day - 1) % 7]
    time_slot = random.choice(["上午", "中午", "下午", "晚上"])
    temperature = random.randint(18, 32)
    rainfall = random.randint(20, 80) if weather == "小雨" else random.randint(0, 15)

    semester_stage = previous.get("semester_stage", "平时周")
    exam_pressure = int(previous.get("exam_pressure", 35))
    assignment_pressure = int(previous.get("assignment_pressure", 40))
    activity_heat = int(previous.get("activity_heat", 50))

    if day % 7 == 0:
        semester_stage = "考试周"
        exam_pressure = min(100, exam_pressure + 25)
        assignment_pressure = min(100, assignment_pressure + 15)
        activity_heat = max(20, activity_heat - 15)
        event_name = "期末复习"
    elif day % 5 == 0:
        semester_stage = "活动周"
        exam_pressure = max(10, exam_pressure - 10)
        assignment_pressure = max(10, assignment_pressure - 5)
        activity_heat = min(100, activity_heat + 25)
        event_name = "校园社团节"
    else:
        event_name = random.choice(["社团招新", "普通教学日", "讲座通知", "运动训练"])
        exam_pressure = max(10, min(100, exam_pressure + random.randint(-8, 8)))
        assignment_pressure = max(10, min(100, assignment_pressure + random.randint(-8, 8)))
        activity_heat = max(10, min(100, activity_heat + random.randint(-10, 10)))

    study_atmosphere = max(10, min(100, 35 + exam_pressure // 2 + assignment_pressure // 3))
    event_intensity = max(10, min(100, activity_heat + random.randint(-10, 15)))
    campus_flow = max(10, min(100, 45 + activity_heat // 2 + random.randint(-10, 10)))
    classroom_crowd = max(10, min(100, 40 + assignment_pressure // 2 + random.randint(-10, 10)))
    canteen_crowd = max(10, min(100, campus_flow + (20 if time_slot in {"中午", "晚上"} else 0) + random.randint(-10, 10)))
    library_crowd = max(10, min(100, 35 + exam_pressure // 2 + random.randint(-10, 15)))
    dorm_crowd = max(10, min(100, 35 + (20 if time_slot == "晚上" else 0) + random.randint(-10, 15)))
    playground_crowd = max(10, min(100, 30 + activity_heat // 2 - rainfall // 3 + random.randint(-10, 10)))
    commercial_crowd = max(10, min(100, 35 + activity_heat // 2 + random.randint(-5, 20)))

    traffic_status = "拥堵" if campus_flow > 75 else "正常"
    network_status = "拥堵" if dorm_crowd > 70 and time_slot == "晚上" else "稳定"
    safety_level = max(50, min(100, 95 - campus_flow // 8 - event_intensity // 10))
    resource_pressure = max(10, min(100, (canteen_crowd + library_crowd + classroom_crowd) // 3))
    campus_mood = "紧张" if exam_pressure > 75 else ("活跃" if activity_heat > 70 else "平稳")
    consumption_index = round(max(0.5, min(1.8, 0.7 + activity_heat / 110 + commercial_crowd / 220 + random.uniform(-0.1, 0.1))), 2)

    values = {
        "weather": weather,
        "semester_stage": semester_stage,
        "time_slot": time_slot,
        "weekday": weekday,
        "temperature": temperature,
        "rainfall": rainfall,
        "exam_pressure": exam_pressure,
        "assignment_pressure": assignment_pressure,
        "study_atmosphere": study_atmosphere,
        "activity_heat": activity_heat,
        "event_name": event_name,
        "event_intensity": event_intensity,
        "campus_flow": campus_flow,
        "classroom_crowd": classroom_crowd,
        "canteen_crowd": canteen_crowd,
        "library_crowd": library_crowd,
        "dorm_crowd": dorm_crowd,
        "playground_crowd": playground_crowd,
        "commercial_crowd": commercial_crowd,
        "traffic_status": traffic_status,
        "network_status": network_status,
        "safety_level": safety_level,
        "resource_pressure": resource_pressure,
        "campus_mood": campus_mood,
        "consumption_index": consumption_index,
    }

    try:
        real_weather = fetch_real_weather()
        values.update({key: real_weather[key] for key in ["weather", "temperature", "rainfall", "weather_source", "weather_observed_at"]})
    except Exception as exc:
        logger.warning("Falling back to simulated weather: %s", exc)
        values["weather_source"] = "simulation"
        values["weather_observed_at"] = ""
    values = derive_environment_from_weather(values)
    values = derive_environment_from_real_time(values)
    save_environment_values(conn, day, values)
    conn.commit()
    maybe_generate_environment_event(conn, day)
    return get_campus_environment(conn, day)


@app.get("/")
def home():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")


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
            "spaces": get_space_snapshot(conn, day),
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


@app.get("/api/agents/{resident_id}/memories/relevant")
def get_relevant_agent_memories(resident_id: int, query: str = ""):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        terms = [term.strip() for term in query.split(",") if term.strip()]
        return {
            "resident_id": resident_id,
            "query_terms": terms,
            "memories": retrieve_relevant_memories(conn, resident_id, query_terms=terms),
        }

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


@app.get("/api/campus/spaces")
def get_campus_spaces():
    with get_connection() as conn:
        return get_space_snapshot(conn)


@app.post("/api/campus/spaces/{location}/status")
def set_space_status(location: str, payload: SpaceStatusRequest):
    with get_connection() as conn:
        ensure_space_system(conn)
        updated = conn.execute(
            "UPDATE campus_spaces SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE location = ?",
            (payload.status, location),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="空间不存在")
        day = get_current_day(conn)
        add_event(conn, day, "space_status", f"空间「{location}」状态调整为：{payload.status}。")
        conn.commit()
        return get_space_snapshot(conn, day)


@app.post("/api/campus/events/trigger")
def trigger_campus_event(payload: CampusEventRequest):
    with get_connection() as conn:
        day = get_current_day(conn)
        invalid_spaces = set(payload.target_spaces) - set(VALID_LOCATIONS)
        if invalid_spaces:
            raise HTTPException(status_code=400, detail=f"不存在的空间：{sorted(invalid_spaces)}")
        event = create_campus_event(
            conn,
            day,
            payload.title,
            payload.event_type,
            payload.intensity,
            payload.target_spaces,
            payload.effects,
        )
        return {"message": "校园事件已触发", "event": event, "environment": get_campus_environment(conn, day), "spaces": get_space_snapshot(conn, day)}


@app.post("/api/campus/events/{event_id}/resolve")
def resolve_campus_event(event_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM campus_events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="事件不存在")
        conn.execute(
            "UPDATE campus_events SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (event_id,),
        )
        day = get_current_day(conn)
        add_event(conn, day, "campus_event_resolved", f"校园事件《{row['title']}》已结束。")
        conn.commit()
        return {"message": "校园事件已结束", "event_id": event_id, "spaces": get_space_snapshot(conn, day)}


@app.post("/api/campus/environment/sync-real-time")
def sync_real_time():
    with get_connection() as conn:
        day = get_current_day(conn)
        values = dict(get_campus_environment(conn, day))
        values = derive_environment_from_real_time(values)
        save_environment_values(conn, day, values)
        add_event(conn, day, "real_time_sync", f"校园环境已同步真实时间：{values['real_date']} {values['real_time']}，{values['weekday']}，{values['time_slot']}。")
        conn.commit()
        return {"message": "真实时间同步成功", "environment": get_campus_environment(conn, day)}


@app.post("/api/campus/environment/sync-real-weather")
def sync_real_weather():
    with get_connection() as conn:
        day = get_current_day(conn)
        current_env = get_campus_environment(conn, day)
        weather_data = fetch_real_weather()
        values = dict(current_env)
        values.update({key: weather_data[key] for key in ["weather", "temperature", "rainfall", "weather_source", "weather_observed_at"]})
        values = derive_environment_from_weather(values)
        values = derive_environment_from_real_time(values)
        save_environment_values(conn, day, values)
        add_event(conn, day, "real_weather_sync", f"接入真实天气：{values['weather']}，{values['temperature']}℃，降雨指数 {values['rainfall']}。")
        conn.commit()
        env = get_campus_environment(conn, day)
        env["real_weather_raw"] = weather_data["raw"]
        return env


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




@app.get("/api/social/hierarchy")
def get_social_hierarchy():
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT residents.id, residents.name, residents.role,
                   agent_profiles.organization, agent_profiles.hierarchy_level
            FROM residents
            JOIN agent_profiles ON agent_profiles.resident_id = residents.id
            ORDER BY agent_profiles.hierarchy_level DESC, residents.id
            """
        ).fetchall()
        levels = {}
        for row in rows:
            level = int(row["hierarchy_level"])
            levels.setdefault(str(level), {"title": get_hierarchy_title(level), "agents": []})
            levels[str(level)]["agents"].append(dict(row))
        return {"levels": levels}


@app.get("/api/agents/{resident_id}/learning")
def get_agent_learning(resident_id: int):
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT day, action, outcome, score_delta, lesson, created_at
            FROM agent_learning
            WHERE resident_id = ?
            ORDER BY id DESC
            LIMIT 30
            """,
            (resident_id,),
        ).fetchall()
        return {"resident_id": resident_id, "learning": rows_to_dicts(rows)}


@app.post("/api/social/communicate")
def social_communicate(payload: ChatRequest):
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        result = chat_between(conn, payload.speaker_id, payload.listener_id, payload.message)
        record_learning(conn, payload.speaker_id, "communicate", "完成沟通", action_score("communicate", True), f"主动沟通：{payload.message}")
        record_learning(conn, payload.listener_id, "communicate", "回应沟通", action_score("communicate", True), f"收到沟通：{payload.message}")
        conn.commit()
        return {"type": "communication", "result": result}


@app.post("/api/social/negotiate")
def social_negotiate(payload: NegotiateRequest):
    with get_connection() as conn:
        return negotiate_between(conn, payload.initiator_id, payload.target_id, payload.topic, payload.proposal)


@app.post("/api/social/collaborate")
def social_collaborate(payload: CollaborateRequest):
    with get_connection() as conn:
        return create_collaboration(conn, payload.leader_id, payload.member_ids, payload.title, payload.goal)


@app.post("/api/social/compete")
def social_compete(payload: CompeteRequest):
    with get_connection() as conn:
        return create_competition(conn, payload.participant_ids, payload.title, payload.metric)


@app.get("/api/agents/{resident_id}/long-term-goals")
def get_long_term_goals(resident_id: int):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        rows = conn.execute(
            "SELECT * FROM long_term_goals WHERE resident_id = ? ORDER BY status, deadline_day, id",
            (resident_id,),
        ).fetchall()
        return rows_to_dicts(rows)


@app.post("/api/goals")
def create_long_term_goal(payload: LongTermGoalRequest):
    with get_connection() as conn:
        if not get_resident(conn, payload.resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        day = get_current_day(conn)
        cursor = conn.execute(
            """
            INSERT INTO long_term_goals (resident_id, title, category, deadline_day, last_update_day)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.resident_id, payload.title, payload.category, payload.deadline_day or day + 14, day),
        )
        add_event(conn, day, "long_term_goal", f"Agent {payload.resident_id} 新增长期目标《{payload.title}》。")
        conn.commit()
        return {"message": "长期目标已创建", "goal_id": cursor.lastrowid}


@app.get("/api/social/relationships/{resident_id}")
def get_social_relationships(resident_id: int):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT relationships.to_resident_id, residents.name, residents.role, relationships.score, relationships.notes
            FROM relationships JOIN residents ON residents.id = relationships.to_resident_id
            WHERE relationships.from_resident_id = ?
            ORDER BY relationships.score DESC
            """,
            (resident_id,),
        ).fetchall()
        relationships = []
        for row in rows:
            item = dict(row)
            item["dynamics"] = get_relationship_dynamics(conn, resident_id, item["to_resident_id"])
            relationships.append(item)
        return relationships


@app.get("/api/agents/{resident_id}/social-graph")
def get_agent_social_graph(resident_id: int):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT relationships.to_resident_id, residents.name, residents.role,
                   relationships.score, relationship_dynamics.affinity, relationship_dynamics.trust,
                   relationship_dynamics.cooperation, relationship_dynamics.competition,
                   relationship_dynamics.conflict
            FROM relationships
            JOIN residents ON residents.id = relationships.to_resident_id
            LEFT JOIN relationship_dynamics
              ON relationship_dynamics.from_resident_id = relationships.from_resident_id
             AND relationship_dynamics.to_resident_id = relationships.to_resident_id
            WHERE relationships.from_resident_id = ?
            ORDER BY relationships.score DESC
            """,
            (resident_id,),
        ).fetchall()
        owner = get_resident(conn, resident_id)
        return {
            "nodes": [{"id": resident_id, "name": owner["name"], "role": owner["role"], "owner": True}]
            + [{"id": row["to_resident_id"], "name": row["name"], "role": row["role"], "owner": False} for row in rows],
            "links": [
                {
                    "from": resident_id,
                    "to": row["to_resident_id"],
                    "score": row["score"],
                    "affinity": row["affinity"] if row["affinity"] is not None else 50,
                    "trust": row["trust"] if row["trust"] is not None else 50,
                    "cooperation": row["cooperation"] if row["cooperation"] is not None else 50,
                    "competition": row["competition"] if row["competition"] is not None else 0,
                    "conflict": row["conflict"] if row["conflict"] is not None else 0,
                }
                for row in rows
            ],
        }


@app.get("/api/agents/{resident_id}/timeline")
def get_agent_timeline(resident_id: int, limit: int = 30):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT day, decision, execution, environment_feedback, created_at
            FROM simulation_action_logs
            WHERE resident_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (resident_id, min(max(limit, 1), 100)),
        ).fetchall()
        return [
            {
                "day": row["day"],
                "decision": load_json_text(row["decision"], {}),
                "execution": load_json_text(row["execution"], {}),
                "environment_feedback": load_json_text(row["environment_feedback"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


@app.get("/api/agents/{resident_id}/simulation-logs")
def get_agent_simulation_logs(resident_id: int, limit: int = 12):
    with get_connection() as conn:
        if not get_resident(conn, resident_id):
            raise HTTPException(status_code=404, detail="Agent 不存在")
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT day, perception, retrieved_memories, decision, execution, environment_feedback, created_at
            FROM simulation_action_logs
            WHERE resident_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (resident_id, min(max(limit, 1), 50)),
        ).fetchall()
        return [
            {
                "day": row["day"],
                "perception": load_json_text(row["perception"], {}),
                "retrieved_memories": load_json_text(row["retrieved_memories"], []),
                "decision": load_json_text(row["decision"], {}),
                "execution": load_json_text(row["execution"], {}),
                "environment_feedback": load_json_text(row["environment_feedback"], {}),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


@app.get("/api/organizations")
def get_campus_organizations():
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        rows = conn.execute(
            """
            SELECT campus_organizations.*,
                   COUNT(organization_members.resident_id) AS active_members
            FROM campus_organizations
            LEFT JOIN organization_members
              ON organization_members.organization_id = campus_organizations.id
             AND organization_members.status = 'active'
            GROUP BY campus_organizations.id
            ORDER BY campus_organizations.organization_type, campus_organizations.id
            """
        ).fetchall()
        organizations = []
        for row in rows:
            item = dict(row)
            item["resources"] = load_json_text(item["resources"], {})
            item["schedule"] = load_json_text(item["schedule"], [])
            organizations.append(item)
        return organizations


@app.get("/api/groups")
def get_group_goals():
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        rows = conn.execute("SELECT * FROM group_goals ORDER BY status, deadline_day, id DESC").fetchall()
        return rows_to_dicts(rows)


@app.post("/api/groups")
def create_group_goal(payload: GroupGoalRequest):
    with get_connection() as conn:
        ensure_social_system_tables(conn)
        ids = [payload.leader_id] + [member_id for member_id in payload.member_ids if member_id != payload.leader_id]
        residents = conn.execute(
            f"SELECT id FROM residents WHERE id IN ({','.join(['?'] * len(ids))})",
            ids,
        ).fetchall()
        if len(residents) != len(set(ids)):
            raise HTTPException(status_code=404, detail="有 Agent 不存在")
        day = get_current_day(conn)
        roles = {str(member_id): ("负责人" if member_id == payload.leader_id else "成员") for member_id in ids}
        cursor = conn.execute(
            """
            INSERT INTO group_goals
            (name, group_type, leader_id, member_ids, roles, shared_goal, deadline_day, current_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.group_type,
                payload.leader_id,
                json.dumps(ids, ensure_ascii=False),
                json.dumps(roles, ensure_ascii=False),
                payload.shared_goal,
                payload.deadline_day or day + 10,
                payload.current_plan,
            ),
        )
        for from_id in ids:
            for to_id in ids:
                if from_id != to_id:
                    evolve_relationship(conn, from_id, to_id, "group_goal", f"共同目标：{payload.shared_goal}", 2, 3, 0)
        add_event(conn, day, "group_goal", f"群体「{payload.name}」成立，共同目标：{payload.shared_goal}。")
        conn.commit()
        return {"message": "群体目标已创建", "group_id": cursor.lastrowid, "member_ids": ids}

@app.post("/api/tools/move")
def tool_move(payload: MoveRequest):
    with get_connection() as conn:
        module_state = get_agent_module_state(conn, payload.resident_id)
        schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
        cost = calculate_action_cost(conn, payload.resident_id, "move", {"destination": payload.destination})
        ensure_action_affordable(conn, payload.resident_id, cost, "move")
        assert_destination_available(conn, payload.destination)
        result = move_resident(conn, payload.resident_id, payload.destination)
        result["long_term_goal"] = advance_personal_goal(conn, payload.resident_id, "move", True)
        result["action_cost"] = update_agent_profile_after_action(conn, payload.resident_id, "move", "手动移动", cost=cost, schedule_context=schedule_context, tool_input={"destination": payload.destination})
        conn.commit()
        return result


@app.post("/api/tools/chat")
def tool_chat(payload: ChatRequest):
    with get_connection() as conn:
        module_state = get_agent_module_state(conn, payload.speaker_id)
        schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
        cost = calculate_action_cost(conn, payload.speaker_id, "chat")
        ensure_action_affordable(conn, payload.speaker_id, cost, "chat")
        result = chat_between(conn, payload.speaker_id, payload.listener_id, payload.message)
        result["social_update"] = {
            "speaker": evolve_relationship(conn, payload.speaker_id, payload.listener_id, "chat", "日常交流", 3, 2, -1),
            "listener": evolve_relationship(conn, payload.listener_id, payload.speaker_id, "chat", "回应交流", 2, 2, -1),
        }
        result["long_term_goal"] = advance_personal_goal(conn, payload.speaker_id, "chat", True)
        result["action_cost"] = update_agent_profile_after_action(conn, payload.speaker_id, "chat", "手动交流", cost=cost, schedule_context=schedule_context, tool_input={"target_id": payload.listener_id})
        conn.commit()
        return result


@app.post("/api/tools/buy-sell")
def tool_buy_sell(payload: BuySellRequest):
    with get_connection() as conn:
        module_state = get_agent_module_state(conn, payload.buyer_id)
        schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
        cost = calculate_action_cost(conn, payload.buyer_id, "buy_sell")
        ensure_action_affordable(conn, payload.buyer_id, cost, "buy_sell")
        result = buy_sell(
            conn,
            payload.buyer_id,
            payload.seller_id,
            payload.item_name,
            payload.quantity,
            payload.unit_price,
        )
        result["long_term_goal"] = advance_personal_goal(conn, payload.buyer_id, "buy_sell", True)
        result["action_cost"] = update_agent_profile_after_action(conn, payload.buyer_id, "buy_sell", "手动交易", cost=cost, schedule_context=schedule_context, tool_input={"seller_id": payload.seller_id})
        conn.commit()
        return result


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
        module_state = get_agent_module_state(conn, payload.proposer_id)
        schedule_context = module_state["modules"]["Schedule"]["current_schedule"]
        cost = calculate_action_cost(conn, payload.proposer_id, "submit_policy")
        ensure_action_affordable(conn, payload.proposer_id, cost, "submit_policy")
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
        action_cost = update_agent_profile_after_action(conn, payload.proposer_id, "submit_policy", "手动提交政策", cost=cost, schedule_context=schedule_context, tool_input={"title": payload.title})
        conn.commit()
        return {"message": "政策提交成功", "description": description, "action_cost": action_cost}


@app.post("/api/tools/vote-policy")
def vote_policy(payload: VotePolicyRequest):
    if payload.vote not in {"yes", "no"}:
        raise HTTPException(status_code=400, detail="vote 只能是 yes 或 no")

    with get_connection() as conn:
        resident = get_resident(conn, payload.resident_id)
        policy = conn.execute("SELECT * FROM policies WHERE id = ?", (payload.policy_id,)).fetchone()
        if not resident or not policy:
            raise HTTPException(status_code=404, detail="投票人或政策不存在")
        cost = calculate_action_cost(conn, payload.resident_id, "observe")
        ensure_action_affordable(conn, payload.resident_id, cost, "observe")
        column = "yes_votes" if payload.vote == "yes" else "no_votes"
        conn.execute(f"UPDATE policies SET {column} = {column} + 1 WHERE id = ?", (payload.policy_id,))
        day = get_current_day(conn)
        description = f"{resident['name']} 对政策《{policy['title']}》投票：{payload.vote}"
        add_event(conn, day, "policy_vote", description)
        add_memory(conn, payload.resident_id, day, description, importance=1)
        action_cost = update_agent_profile_after_action(conn, payload.resident_id, "observe", "参与政策投票", cost=cost)
        conn.commit()
        return {"message": "投票成功", "description": description, "action_cost": action_cost}


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


def summarize_action_for_news(execution):
    result = execution.get("result") if isinstance(execution, dict) else None
    if isinstance(result, dict):
        return str(result.get("description") or result.get("message") or execution.get("action") or "完成了一次校园行动")
    return str(execution.get("action") or "完成了一次校园行动")


def publish_agent_news(conn, day, results):
    """Create a small number of public-facing posts from autonomous actions."""
    ensure_agent_news_system(conn)
    published = []
    for item in random.sample(results, min(4, len(results))):
        resident_id = item.get("resident_id")
        resident = conn.execute(
            "SELECT id, name, role, location, goal FROM residents WHERE id = ?",
            (resident_id,),
        ).fetchone()
        if not resident:
            continue

        action_summary = summarize_action_for_news(item.get("execution", {}))
        prompt = (
            f"你是校园里的{resident['role']}“{resident['name']}”。你刚在{resident['location']}完成了：{action_summary}。"
            "请自己判断这件事是否值得向全校发布一条新鲜事；若值得，用第一人称写一条40到80字的校园投稿。"
            "只输出投稿正文，不要标题、JSON、代码、行动日志或解释。"
        )
        try:
            content = ask_llm(prompt).strip()
        except Exception:
            content = f"我今天在{resident['location']}完成了一次新的校园行动，也留意到这里正在发生变化。"

        if not content or content.startswith(("{", "[")):
            content = f"我今天在{resident['location']}完成了一次新的校园行动，也留意到这里正在发生变化。"
        headline = f"{resident['name']}的校园来信"
        conn.execute(
            """
            INSERT OR IGNORE INTO agent_news_posts (day, resident_id, headline, content)
            VALUES (?, ?, ?, ?)
            """,
            (day, resident["id"], headline, content[:300]),
        )
        published.append({"resident_id": resident["id"], "headline": headline})
    return published


def write_agent_daily_diaries(conn, day, results=None, replace_existing=False):
    """Let every Agent write a first-person diary from its own lived context."""
    agents = conn.execute(
        "SELECT id, name, role, personality, location, goal FROM residents ORDER BY id"
    ).fetchall()
    by_agent = {item.get("resident_id"): item for item in (results or [])}
    created = []
    action_text = {
        "chat": "和校园里的其他人交流",
        "move": "前往新的校园空间",
        "buy_sell": "完成了一次交易",
        "observe": "观察校园环境",
        "submit_policy": "参与校园事务讨论",
    }
    for agent in agents:
        exists = conn.execute(
            "SELECT 1 FROM memories WHERE resident_id = ? AND day = ? AND content LIKE ?",
            (agent["id"], day, f"日记·第{day}天：%"),
        ).fetchone()
        if exists and not replace_existing:
            continue
        if exists and replace_existing:
            conn.execute(
                "DELETE FROM memories WHERE resident_id = ? AND day = ? AND content LIKE ?",
                (agent["id"], day, f"日记·第{day}天：%"),
            )
        item = by_agent.get(agent["id"], {})
        execution = item.get("execution", {}) if isinstance(item, dict) else {}
        decision = item.get("decision", {}).get("decision", {}) if isinstance(item, dict) else {}
        action = execution.get("action") or decision.get("action")
        activity = action_text.get(action, "完成自己的校园安排")
        reason = str(decision.get("reason") or "")[:90].strip()
        recent_memories = conn.execute(
            """
            SELECT content FROM memories
            WHERE resident_id = ? AND day = ? AND content NOT LIKE ?
            ORDER BY id DESC LIMIT 4
            """,
            (agent["id"], day, f"日记·第{day}天：%"),
        ).fetchall()
        memory_text = "；".join(row["content"][:160] for row in recent_memories)
        prompt = f"""
你是校园封闭世界中的 Agent“{agent['name']}”。
你的身份：{agent['role']}；性格：{agent['personality']}；长期目标：{agent['goal']}；当前位置：{agent['location']}。
今天你实际完成的行动：{activity}。你的行动理由：{reason or '根据自己的状态和环境自主判断'}。
今天留下的个人经历：{memory_text or '暂无额外记录'}。

请以第一人称写一段 70 到 130 字的中文个人日记，内容必须符合你的性格和目标，写真实感受、观察或下一步想法。
只输出日记正文，不要标题、JSON、Markdown、技术字段或解释。
"""
        fallback = f"今天我在{agent['location']}{activity}。这次经历让我更清楚地看到校园的变化，也提醒我继续朝“{agent['goal']}”努力。"
        try:
            diary_text = ask_llm(prompt).strip()
        except Exception:
            diary_text = fallback
        if not diary_text or diary_text.startswith(("{", "[")):
            diary_text = fallback
        diary = f"日记·第{day}天：{diary_text[:500]}"
        add_memory(
            conn,
            agent["id"],
            day,
            diary,
            importance=5,
            memory_type="episodic",
            tags=["日记", agent["location"], activity],
            source="diary",
        )
        created.append(agent["id"])
    return created


@app.post("/api/agents/daily-diaries/backfill")
def backfill_agent_daily_diaries(day: Optional[int] = None, rewrite: bool = False):
    with get_connection() as conn:
        target_day = day or get_current_day(conn)
        created = write_agent_daily_diaries(conn, target_day, replace_existing=rewrite)
        conn.commit()
        return {"day": target_day, "created": len(created), "agent_ids": created}


@app.get("/api/newspaper/agent-posts")
def agent_newspaper_posts():
    """Return the daily reflections that Agents publish in their own voice."""
    with get_connection() as conn:
        ensure_agent_news_system(conn)
        day = get_current_day(conn)
        posts = conn.execute(
            """
            SELECT p.resident_id, r.name, r.role, p.headline, p.content, p.created_at
            FROM agent_news_posts p
            JOIN residents r ON r.id = p.resident_id
            WHERE p.day = ?
            ORDER BY p.id DESC
            LIMIT 12
            """,
            (day,),
        ).fetchall()
        return {"day": day, "posts": rows_to_dicts(posts)}


@app.get("/api/newspaper/ai-today")
def ai_newspaper_today():
    data = newspaper_today()
    prompt = f"请把下面校园封闭世界数据写成一份简短校园日报，分为标题、环境、主要事件、趋势判断：{json.dumps(data, ensure_ascii=False)}"
    return {"day": data["title"], "newspaper": ask_llm(prompt), "source": data}


EXTERNAL_RSS_SOURCES = [
    (
        "Google News RSS",
        "https://news.google.com/rss/search?q=(AI%20OR%20%E5%A4%A7%E5%AD%A6%20OR%20%E6%95%99%E8%82%B2%20OR%20%E5%B0%B1%E4%B8%9A)&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ),
    (
        "Bing News RSS",
        "https://www.bing.com/news/search?q=(AI%20OR%20university%20OR%20education%20OR%20employment)&format=rss&setlang=zh-CN&cc=CN",
    ),
]


def classify_external_information(text):
    normalized = str(text or "").lower()
    if any(word in normalized for word in ("ai", "人工智能", "科技", "技术")):
        return "technology"
    if any(word in normalized for word in ("就业", "招聘", "创业", "商业", "经济")):
        return "career"
    if any(word in normalized for word in ("教育", "大学", "考试", "课程", "学生")):
        return "education"
    return "general"


def fetch_external_information(limit=5):
    """Read fixed public RSS sources; Agents never receive arbitrary URLs."""
    errors = []
    for source_name, source_url in EXTERNAL_RSS_SOURCES:
        try:
            response = requests.get(
                source_url,
                timeout=12,
                headers={"User-Agent": "CampusAgentSimulation/1.0 (+campus simulation)"},
            )
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            items = []
            for node in root.findall("./channel/item")[:limit]:
                title = (node.findtext("title") or "").strip()
                summary = re.sub(r"<[^>]+>", "", node.findtext("description") or "").strip()
                link = (node.findtext("link") or "").strip()
                published_at = (node.findtext("pubDate") or "").strip()
                if title:
                    items.append(
                        {
                            "title": title[:180],
                            "summary": (summary or title)[:400],
                            "source_name": source_name,
                            "source_url": link,
                            "published_at": published_at,
                            "category": classify_external_information(f"{title} {summary}"),
                        }
                    )
            if items:
                return items
            errors.append(f"{source_name}: no RSS items")
        except Exception as exc:
            logger.warning("External information source failed: %s", source_name, exc_info=True)
            errors.append(f"{source_name}: {type(exc).__name__}")
    raise RuntimeError("; ".join(errors))


def deliver_external_information(
    conn,
    information,
    resident_id,
    channel,
    relevance=65,
    credibility=80,
    distortion_note="",
    source_resident_id=None,
):
    ensure_external_information_system(conn)
    inserted = conn.execute(
        """
        INSERT OR IGNORE INTO agent_information
        (information_id, resident_id, channel, relevance, credibility, distortion_note, source_resident_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (information["id"], resident_id, channel, relevance, credibility, distortion_note, source_resident_id),
    ).rowcount
    if not inserted:
        return False

    profile = ensure_profile_meta(conn, resident_id)
    perception = load_json_text(profile["perception"], {}) if profile else {}
    feed = perception.get("external_information", [])
    feed.insert(0, {
        "title": information["title"],
        "category": information["category"],
        "channel": channel,
        "credibility": credibility,
        "distortion_note": distortion_note,
    })
    perception["external_information"] = feed[:4]
    conn.execute(
        "UPDATE agent_profiles SET perception = ? WHERE resident_id = ?",
        (json.dumps(perception, ensure_ascii=False), resident_id),
    )
    day = get_current_day(conn)
    add_memory(
        conn,
        resident_id,
        day,
        f"我从{channel}得知外部消息：{information['title']}。可信度 {credibility}。{distortion_note}",
        importance=4,
        memory_type="working",
        tags=["外部资讯", information["category"], channel, f"可信度{credibility}"],
        source="external_information",
    )
    return True


def seed_external_information_recipients(conn, information):
    agents = conn.execute(
        """
        SELECT residents.id, residents.role, residents.goal, residents.personality,
               agent_profiles.skills, agent_profiles.organization
        FROM residents LEFT JOIN agent_profiles ON agent_profiles.resident_id = residents.id
        ORDER BY residents.id
        """
    ).fetchall()
    category_terms = {
        "technology": ("AI", "人工智能", "技术", "创业"),
        "career": ("创业", "商业", "投资", "就业"),
        "education": ("学生", "教师", "课程", "学习"),
    }
    terms = category_terms.get(information["category"], ())
    ranked = sorted(
        agents,
        key=lambda agent: sum(term in f"{agent['role']} {agent['goal']} {agent['personality']} {agent['skills'] or ''} {agent['organization'] or ''}" for term in terms),
        reverse=True,
    )
    recipients = ranked[:4]
    return [
        agent["id"]
        for agent in recipients
        if deliver_external_information(conn, information, agent["id"], "外部资讯订阅", relevance=80, credibility=88)
    ]


def spread_external_information(conn, limit=12):
    """Let information travel along existing social relationships over later simulation days."""
    ensure_external_information_system(conn)
    rows = conn.execute(
        """
        SELECT ai.information_id, ai.resident_id AS sender_id, ai.credibility,
               ei.title, ei.category
        FROM agent_information ai
        JOIN external_information ei ON ei.id = ai.information_id
        ORDER BY ai.received_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    delivered = 0
    for row in rows:
        contacts = conn.execute(
            """
            SELECT relationships.to_resident_id, relationship_dynamics.trust, relationship_dynamics.affinity
            FROM relationships
            LEFT JOIN relationship_dynamics
              ON relationship_dynamics.from_resident_id = relationships.from_resident_id
             AND relationship_dynamics.to_resident_id = relationships.to_resident_id
            WHERE relationships.from_resident_id = ? AND relationships.score >= 55
            ORDER BY COALESCE(relationship_dynamics.trust, 50) + COALESCE(relationship_dynamics.affinity, 50) DESC LIMIT 2
            """,
            (row["sender_id"],),
        ).fetchall()
        info = {"id": row["information_id"], "title": row["title"], "category": row["category"]}
        for contact in contacts:
            distortion = random.choice(["", "转述时省略了部分背景。", "转述时更强调了与自己相关的部分。"])
            credibility = max(35, int(row["credibility"] or 80) - (8 if distortion else 3))
            relevance = min(85, 52 + int(contact["trust"] or 50) // 3)
            delivered += int(
                deliver_external_information(
                    conn,
                    info,
                    contact["to_resident_id"],
                    "熟人转述",
                    relevance=relevance,
                    credibility=credibility,
                    distortion_note=distortion,
                    source_resident_id=row["sender_id"],
                )
            )
    return delivered


@app.post("/api/external-information/sync")
def sync_external_information():
    with get_connection() as conn:
        ensure_external_information_system(conn)
        try:
            fetched = fetch_external_information()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"外部资讯同步失败：{exc}")

        created = []
        recipient_ids = set()
        for item in fetched:
            conn.execute(
                """
                INSERT OR IGNORE INTO external_information
                (title, summary, source_name, source_url, category, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (item["title"], item["summary"], item["source_name"], item["source_url"], item["category"], item["published_at"]),
            )
            row = conn.execute("SELECT * FROM external_information WHERE title = ?", (item["title"],)).fetchone()
            if row:
                information = dict(row)
                newly_informed = seed_external_information_recipients(conn, information)
                if newly_informed:
                    created.append(information)
                    recipient_ids.update(newly_informed)
        if created:
            add_event(conn, get_current_day(conn), "external_information", f"校园接入 {len(created)} 条外部资讯，已有 {len(recipient_ids)} 位 Agent 先行获知。")
        conn.commit()
        return {"fetched": len(fetched), "new_information": created, "initial_recipients": len(recipient_ids)}


@app.get("/api/external-information")
def get_external_information():
    with get_connection() as conn:
        ensure_external_information_system(conn)
        rows = conn.execute(
            "SELECT * FROM external_information ORDER BY id DESC LIMIT 20"
        ).fetchall()
        return {"items": rows_to_dicts(rows)}


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
            feedback = apply_environment_feedback(conn, agent["id"], execution["action"], execution["result"])
            results.append({"decision": decision_data, "execution": execution, "environment_feedback": feedback})
        return {"message": f"{len(results)} 个校园 Agent 已轮流自主行动", "results": results}


@app.post("/api/simulate/lifecycle-step/{resident_id}")
def simulate_lifecycle_step(resident_id: int):
    with get_connection() as conn:
        return run_lifecycle_step(conn, resident_id)


@app.post("/api/simulate/lifecycle-round")
def simulate_lifecycle_round():
    with get_connection() as conn:
        agents = conn.execute("SELECT id FROM residents ORDER BY id").fetchall()
        results = []
        for agent in agents:
            results.append(run_lifecycle_step(conn, agent["id"]))
        day = get_current_day(conn)
        add_event(conn, day, "lifecycle_round", f"第 {day} 天完成一轮 Agent-环境交互循环，共 {len(results)} 个 Agent。")
        conn.commit()
        return {
            "message": f"{len(results)} 个 Agent 完成感知-决策-行动-反馈循环",
            "loop": "perceive -> decide -> act -> feedback -> memory",
            "results": results,
        }


@app.post("/api/simulate/ai-day")
def simulate_ai_day():
    with get_connection() as conn:
        old_day = get_current_day(conn)
        new_day = old_day + 1
        conn.execute("UPDATE simulation_state SET value = ? WHERE key = 'current_day'", (str(new_day),))
        conn.commit()
        env = auto_update_environment(conn, new_day)
        recover_agents_for_new_day(conn, new_day)
        spread_count = spread_external_information(conn)
        conn.commit()
        agents = conn.execute("SELECT id FROM residents ORDER BY id").fetchall()
        results = []
        fallback_agents = []
        for agent in agents:
            try:
                perception = perceive_environment(conn, agent["id"])
                decision_data = decide_agent_action(conn, agent["id"])
                execution = execute_decision(conn, agent["id"], decision_data["decision"])
                feedback = apply_environment_feedback(conn, agent["id"], execution["action"], execution["result"])
            except Exception as exc:
                logger.exception("Agent %s failed during day %s", agent["id"], new_day)
                fallback_agents.append(agent["id"])
                perception = perceive_environment(conn, agent["id"])
                decision_data = {
                    "decision": {
                        "action": "observe",
                        "reason": f"当日行动异常，改为观察并保留状态：{type(exc).__name__}",
                        "tool_input": {"focus": "校园环境"},
                    }
                }
                execution = execute_decision(conn, agent["id"], decision_data["decision"])
                feedback = apply_environment_feedback(conn, agent["id"], execution["action"], execution["result"])

            record_simulation_log(conn, agent["id"], perception, decision_data, execution, feedback)
            results.append(
                {
                    "resident_id": agent["id"],
                    "perception": perception,
                    "decision": decision_data,
                    "execution": execution,
                    "environment_feedback": feedback,
                }
            )
        group_updates = advance_group_goals(conn, new_day, [item["execution"] for item in results])
        daily_diaries = write_agent_daily_diaries(conn, new_day, results)
        published_news = publish_agent_news(conn, new_day, results)
        add_event(conn, new_day, "daily_reflect", f"第 {new_day} 天校园自动模拟完成，共产生 {len(results)} 个行动。")
        conn.commit()
        return {
            "message": "校园一天模拟完成",
            "day": new_day,
            "environment": env,
            "external_information_spread": spread_count,
            "actions": results,
            "group_goal_updates": group_updates,
            "daily_diaries": len(daily_diaries),
            "published_news": published_news,
            "fallback_agents": fallback_agents,
        }




