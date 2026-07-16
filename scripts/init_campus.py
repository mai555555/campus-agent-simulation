from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import execute_script, get_connection
from app.models import SCHEMA_SQL
from tools.city_tools import add_event, add_inventory

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

CAMPUS_AGENTS = [
    (1, "林小夏", "大一学生", "好奇、外向、喜欢参加活动", "适应校园生活并结交朋友", 120, "宿舍区"),
    (2, "陈宇航", "大二学生", "自律、理性、重视成绩", "保持绩点并完成课程项目", 110, "教学楼"),
    (3, "赵一鸣", "大三学生", "务实、压力较大、关注就业", "找到实习机会", 130, "图书馆"),
    (4, "苏晴", "学生会干部", "负责、组织力强、关心同学", "办好校园活动", 100, "校务处"),
    (5, "周老板", "食堂商家", "精打细算、重视口碑", "提高窗口销量和评分", 280, "食堂"),
    (6, "李姐", "奶茶店商家", "热情、会营销、反应快", "吸引学生消费", 260, "商业街"),
    (7, "王老师", "辅导员", "稳重、耐心、关注安全", "维护学生秩序和心理状态", 200, "校务处"),
    (8, "何管理员", "图书馆管理员", "安静、规则意识强", "保持图书馆有序", 180, "图书馆"),
    (9, "张晨", "运动社团负责人", "积极、合群、行动力强", "组织训练和比赛", 90, "操场"),
    (10, "校园后勤", "学校组织", "谨慎、服务导向、关注资源", "保障设施和校园运行", 500, "校务处"),
]

INVENTORY = [
    (5, "套餐饭", 80),
    (5, "早餐券", 60),
    (6, "奶茶", 70),
    (6, "咖啡", 40),
    (10, "维修工单", 30),
    (8, "自习座位", 120),
]


def main():
    execute_script(SCHEMA_SQL)
    execute_script(CAMPUS_STATE_SQL)

    with get_connection() as conn:
        # Reset old city demo data so the closed campus world starts clean.
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM city_events")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM policies")
        conn.execute("DELETE FROM inventory")
        conn.execute("DELETE FROM campus_state")
        conn.execute("UPDATE simulation_state SET value = '1' WHERE key = 'current_day'")
        conn.execute(
            "INSERT OR IGNORE INTO simulation_state (key, value) VALUES ('current_day', '1')"
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO campus_state (day, weather, semester_stage)
            VALUES (1, '晴', '开学适应期')
            """
        )

        for agent in CAMPUS_AGENTS:
            conn.execute(
                """
                INSERT INTO residents (id, name, role, personality, goal, money, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    personality = excluded.personality,
                    goal = excluded.goal,
                    money = excluded.money,
                    location = excluded.location
                """,
                agent,
            )

        for resident_id, item_name, quantity in INVENTORY:
            add_inventory(conn, resident_id, item_name, quantity)

        add_event(conn, 1, "system", "校园封闭世界初始化完成，学生、商家和学校组织进入校园。")
        conn.commit()

    print("校园封闭世界初始化完成")


if __name__ == "__main__":
    main()


