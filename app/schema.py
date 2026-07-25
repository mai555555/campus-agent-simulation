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
