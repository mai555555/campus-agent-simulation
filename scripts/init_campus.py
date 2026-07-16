from pathlib import Path
import json
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
    (1, "林小夏", "女", "大一学生", "好奇、外向、喜欢参加活动", "适应校园生活并结交朋友", 120, "宿舍区", "短发圆脸、蓝色卫衣、背双肩包的卡通女生", 88, "期待", "参加新生破冰活动", ["08:00 早餐", "10:00 高数课", "15:00 社团招新", "20:00 宿舍复盘"], {"seeing": "宿舍楼下有社团招新海报"}),
    (2, "陈宇航", "男", "大二学生", "自律、理性、重视成绩", "保持绩点并完成课程项目", 110, "教学楼", "戴眼镜、白衬衫、抱着电脑的卡通男生", 76, "专注", "完成课程项目代码", ["08:30 专业课", "13:30 实验室", "19:00 图书馆自习"], {"seeing": "教学楼今天人流稳定"}),
    (3, "赵一鸣", "男", "大三学生", "务实、压力较大、关注就业", "找到实习机会", 130, "图书馆", "黑色夹克、拿简历文件夹的卡通男生", 68, "焦虑", "修改实习简历", ["09:00 查招聘", "14:00 模拟面试", "21:00 投递简历"], {"seeing": "图书馆自习座位紧张"}),
    (4, "苏晴", "女", "学生会干部", "负责、组织力强、关心同学", "办好校园活动", 100, "校务处", "马尾辫、绿色外套、拿活动板夹的卡通女生", 82, "忙碌", "协调校园活动审批", ["09:30 校务处沟通", "12:30 志愿者群通知", "18:00 活动彩排"], {"seeing": "校务处公告栏更新了活动规则"}),
    (5, "周老板", "男", "食堂商家", "精打细算、重视口碑", "提高窗口销量和评分", 280, "食堂", "围裙大叔、笑眯眯端餐盘的卡通男商家", 80, "务实", "准备午餐高峰", ["06:30 备菜", "11:30 午餐高峰", "16:00 补货", "20:00 盘点"], {"seeing": "食堂入口排队人数增加"}),
    (6, "李姐", "女", "奶茶店商家", "热情、会营销、反应快", "吸引学生消费", 260, "商业街", "卷发、粉色围裙、拿奶茶杯的卡通女商家", 86, "兴奋", "设计第二杯半价活动", ["10:00 开店", "14:00 上新海报", "18:00 晚高峰促销"], {"seeing": "商业街学生客流变多"}),
    (7, "王老师", "男", "辅导员", "稳重、耐心、关注安全", "维护学生秩序和心理状态", 200, "校务处", "灰色夹克、拿笔记本的卡通男老师", 72, "关切", "关注学生压力状态", ["09:00 班会通知", "15:00 个别谈话", "20:00 宿舍走访"], {"seeing": "部分学生临近考试压力升高"}),
    (8, "何管理员", "女", "图书馆管理员", "安静、规则意识强", "保持图书馆有序", 180, "图书馆", "短发、深蓝制服、推书车的卡通女生", 78, "平静", "维护自习秩序", ["08:00 开馆", "12:00 巡查座位", "19:00 安静提醒"], {"seeing": "图书馆二楼座位快满了"}),
    (9, "张晨", "男", "运动社团负责人", "积极、合群、行动力强", "组织训练和比赛", 90, "操场", "运动短发、红色队服、拿篮球的卡通男生", 90, "活跃", "组织社团训练", ["07:00 晨跑", "16:30 社团训练", "21:00 发训练通知"], {"seeing": "操场天气适合训练"}),
    (10, "校园后勤", "男", "学校组织", "谨慎、服务导向、关注资源", "保障设施和校园运行", 500, "校务处", "戴安全帽、拿维修工具箱的卡通男工作人员", 84, "稳定", "处理设施维修工单", ["08:30 巡检", "13:30 维修", "17:30 反馈处理结果"], {"seeing": "宿舍区有新的维修需求"}),
    (11, "顾南星", "女", "大一学生", "文静、细心、喜欢绘画", "找到适合自己的学习节奏", 115, "图书馆", "长发、米色开衫、抱速写本的卡通女生", 74, "安静", "完成英语阅读", ["09:00 英语课", "14:00 图书馆", "19:30 绘画社"], {"seeing": "图书馆窗边座位很安静"}),
    (12, "许嘉言", "男", "大一学生", "开朗、爱社交、容易分心", "扩大朋友圈", 105, "商业街", "棒球帽、橙色卫衣、挥手的卡通男生", 92, "开心", "约同学一起吃饭", ["10:00 选修课", "12:00 食堂", "16:00 商业街", "22:00 宿舍聊天"], {"seeing": "商业街有新店开业"}),
    (13, "孟雨桐", "女", "大二学生", "理性、独立、计划性强", "准备奖学金申请", 125, "教学楼", "高马尾、黑框眼镜、拿计划本的卡通女生", 70, "认真", "整理课程笔记", ["08:00 专业课", "13:00 小组讨论", "20:00 复习"], {"seeing": "教学楼讨论区有空位"}),
    (14, "沈亦舟", "男", "大二学生", "内向、技术宅、喜欢研究工具", "完成一个校园小程序", 118, "宿舍区", "连帽衫、抱笔记本电脑的卡通男生", 66, "沉浸", "调试校园小程序", ["09:30 编程", "15:00 需求调研", "23:00 提交代码"], {"seeing": "宿舍网络状态一般"}),
    (15, "唐晓棠", "女", "大三学生", "外向、表达力强、关注实践", "找到社团和实习机会", 135, "操场", "短发、黄色外套、拿麦克风的卡通女生", 83, "积极", "采访社团活动", ["10:00 新闻采写", "16:00 操场采访", "21:00 写稿"], {"seeing": "操场社团训练很热闹"}),
    (16, "陆子昂", "男", "大三学生", "稳重、竞争心强、目标明确", "准备考研", 100, "图书馆", "深色卫衣、拿厚书的卡通男生", 62, "紧张", "完成考研单词计划", ["07:30 背单词", "10:00 自习", "19:00 刷题"], {"seeing": "图书馆考研区很拥挤"}),
    (17, "乔安然", "女", "研究生", "温和、靠谱、善于协调", "推进课题项目", 160, "教学楼", "白色实验服、拿资料夹的卡通女生", 71, "专注", "整理实验数据", ["09:00 课题组会", "14:00 实验", "20:00 数据分析"], {"seeing": "实验室预约时间紧张"}),
    (18, "韩墨", "男", "研究生", "冷静、逻辑强、喜欢独处", "完成论文初稿", 150, "图书馆", "黑色毛衣、端咖啡的卡通男生", 58, "疲惫", "修改论文结构", ["10:00 查文献", "15:00 写论文", "22:00 整理引用"], {"seeing": "安静区适合写作"}),
    (19, "白露", "女", "心理委员", "敏感、共情力强、善于倾听", "帮助同学缓解压力", 95, "宿舍区", "浅蓝外套、拿便签纸的卡通女生", 79, "关心", "收集同学情绪反馈", ["09:00 上课", "18:00 宿舍交流", "21:00 情绪记录"], {"seeing": "宿舍群里有人抱怨考试压力"}),
    (20, "秦越", "男", "校园创业者", "大胆、灵活、喜欢尝试", "验证校园跑腿服务", 180, "商业街", "黑色背包、拿手机订单的卡通男生", 87, "兴奋", "测试跑腿订单流程", ["11:00 商业街调研", "17:00 试运行", "22:00 复盘数据"], {"seeing": "商业街订单需求变多"}),
]

INVENTORY = [
    (5, "套餐饭", 120),
    (5, "早餐券", 80),
    (6, "奶茶", 100),
    (6, "咖啡", 60),
    (10, "维修工单", 40),
    (8, "自习座位", 160),
    (20, "跑腿券", 30),
    (9, "训练名额", 25),
]


def main():
    execute_script(SCHEMA_SQL)
    execute_script(CAMPUS_STATE_SQL)

    with get_connection() as conn:
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM city_events")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM policies")
        conn.execute("DELETE FROM relationships")
        conn.execute("DELETE FROM inventory")
        conn.execute("DELETE FROM agent_profiles")
        conn.execute("DELETE FROM residents")
        conn.execute("DELETE FROM campus_state")
        conn.execute("INSERT OR REPLACE INTO simulation_state (key, value) VALUES ('current_day', '1')")
        conn.execute(
            """
            INSERT OR IGNORE INTO campus_state (day, weather, semester_stage)
            VALUES (1, '晴', '开学适应期')
            """
        )

        for agent in CAMPUS_AGENTS:
            (
                resident_id,
                name,
                gender,
                role,
                personality,
                goal,
                money,
                location,
                avatar_style,
                energy,
                mood,
                current_task,
                schedule,
                perception,
            ) = agent
            conn.execute(
                """
                INSERT INTO residents (id, name, role, personality, goal, money, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (resident_id, name, role, personality, goal, money, location),
            )
            conn.execute(
                """
                INSERT INTO agent_profiles (
                    resident_id, gender, avatar_style, energy, mood,
                    current_task, schedule, perception
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resident_id,
                    gender,
                    avatar_style,
                    energy,
                    mood,
                    current_task,
                    json.dumps(schedule, ensure_ascii=False),
                    json.dumps(perception, ensure_ascii=False),
                ),
            )

        for resident_id, item_name, quantity in INVENTORY:
            add_inventory(conn, resident_id, item_name, quantity)

        add_event(conn, 1, "system", "校园封闭世界初始化完成，20名卡通校园 Agent 进入校园。")
        conn.commit()

    print("校园封闭世界初始化完成：20名 Agent 已创建")


if __name__ == "__main__":
    main()
