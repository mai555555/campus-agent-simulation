from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import DB_PATH, execute_script, get_connection
from app.models import SCHEMA_SQL


def seed_data() -> None:
    residents = [
        ("陈小面", "小吃老板", "热情、精明", "扩大老城小吃摊生意", 180, "老城"),
        ("李清茶", "茶馆老板", "稳重、会聊天", "让茶馆成为交流中心", 160, "老城"),
        ("王谷雨", "农户", "勤劳、朴实", "把农产品卖到城里", 120, "乡村"),
        ("赵云码", "程序员创业者", "理性、好奇", "开发AI工具", 90, "高新区"),
    ]

    with get_connection() as conn:
        for resident in residents:
            conn.execute(
                """
                INSERT OR IGNORE INTO residents
                (name, role, personality, goal, money, location)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                resident,
            )

        conn.execute(
            "INSERT OR IGNORE INTO simulation_state (key, value) VALUES ('current_day', '1')"
        )

        conn.execute(
            """
            INSERT INTO city_events (day, event_type, description)
            SELECT 1, 'system', '虚拟成都初始化完成。'
            WHERE NOT EXISTS (SELECT 1 FROM city_events WHERE event_type = 'system')
            """
        )

        conn.commit()


def main() -> None:
    execute_script(SCHEMA_SQL)
    seed_data()
    print(f"SQLite 数据库已创建：{DB_PATH}")


if __name__ == "__main__":
    main()