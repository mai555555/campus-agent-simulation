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

WORLD_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS world_runtime (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'paused',
    world_timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
    world_time TEXT NOT NULL DEFAULT '',
    tick_interval_seconds INTEGER NOT NULL DEFAULT 60,
    agents_per_tick INTEGER NOT NULL DEFAULT 3,
    daily_auto_model_budget INTEGER NOT NULL DEFAULT 500,
    auto_model_calls_used INTEGER NOT NULL DEFAULT 0,
    budget_date TEXT NOT NULL DEFAULT '',
    current_agent_cursor INTEGER NOT NULL DEFAULT 0,
    last_tick_started_at TEXT NOT NULL DEFAULT '',
    last_tick_completed_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_ticks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick_index INTEGER NOT NULL,
    world_time TEXT NOT NULL,
    day INTEGER NOT NULL,
    slot TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT 'background',
    status TEXT NOT NULL DEFAULT 'running',
    processed_agents INTEGER NOT NULL DEFAULT 0,
    failed_agents INTEGER NOT NULL DEFAULT 0,
    error_message TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS world_event_stream (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick_id INTEGER,
    day INTEGER NOT NULL,
    slot TEXT NOT NULL,
    event_type TEXT NOT NULL,
    resident_id INTEGER,
    location TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS agent_action_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    plan_json TEXT NOT NULL DEFAULT '{}',
    model_name TEXT NOT NULL DEFAULT 'rule-based-v1',
    prompt_version TEXT NOT NULL DEFAULT 'world-runtime-v1',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resident_id, window_start),
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS observer_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    session_type TEXT NOT NULL DEFAULT 'observer',
    focused_resident_id INTEGER,
    focused_location TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (focused_resident_id) REFERENCES residents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS participant_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    action_type TEXT NOT NULL,
    target_type TEXT NOT NULL DEFAULT '',
    target_id TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'queued',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_type TEXT NOT NULL,
    resident_id INTEGER,
    related_event_id INTEGER,
    model_name TEXT NOT NULL DEFAULT '',
    prompt_version TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'logged',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (related_event_id) REFERENCES world_event_stream(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS campus_schedule_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    role_group TEXT NOT NULL DEFAULT 'all',
    action_type TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    start_hour INTEGER NOT NULL DEFAULT 0,
    end_hour INTEGER NOT NULL DEFAULT 24,
    weekday_pattern TEXT NOT NULL DEFAULT 'all',
    min_exam_pressure INTEGER NOT NULL DEFAULT 0,
    max_exam_pressure INTEGER NOT NULL DEFAULT 100,
    base_weight REAL NOT NULL DEFAULT 1.0,
    noise REAL NOT NULL DEFAULT 0.15,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_causal_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weight_key TEXT NOT NULL UNIQUE,
    source_metric TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    direction REAL NOT NULL DEFAULT 1.0,
    strength REAL NOT NULL DEFAULT 1.0,
    threshold REAL NOT NULL DEFAULT 0.0,
    noise REAL NOT NULL DEFAULT 0.1,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calibration_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL DEFAULT '',
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    role_group TEXT NOT NULL DEFAULT '',
    sample_size INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calibration_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_key TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    summary TEXT NOT NULL DEFAULT '',
    parameter_updates TEXT NOT NULL DEFAULT '{}',
    quality_report_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_world_ticks_started_at ON world_ticks(started_at);
CREATE INDEX IF NOT EXISTS idx_world_event_stream_created_at ON world_event_stream(created_at);
CREATE INDEX IF NOT EXISTS idx_world_event_stream_event_type ON world_event_stream(event_type);
CREATE INDEX IF NOT EXISTS idx_world_event_stream_resident_id ON world_event_stream(resident_id);
CREATE INDEX IF NOT EXISTS idx_world_event_stream_tick_id ON world_event_stream(tick_id);
CREATE INDEX IF NOT EXISTS idx_agent_action_plans_window ON agent_action_plans(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_observer_sessions_last_seen ON observer_sessions(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_model_call_logs_trigger_date ON model_call_logs(trigger_type, created_at);
CREATE INDEX IF NOT EXISTS idx_campus_schedule_rules_context ON campus_schedule_rules(role_group, action_type, start_hour, end_hour);
CREATE INDEX IF NOT EXISTS idx_world_causal_weights_source ON world_causal_weights(source_metric, target_type);
CREATE INDEX IF NOT EXISTS idx_calibration_observations_metric ON calibration_observations(metric_name, observed_at);
CREATE INDEX IF NOT EXISTS idx_calibration_reports_run_id ON calibration_reports(run_id);
"""

RESEARCH_SYSTEM_SQL = """
CREATE TABLE IF NOT EXISTS experiment_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL UNIQUE,
    experiment_name TEXT NOT NULL DEFAULT '',
    hypothesis TEXT NOT NULL DEFAULT '',
    control_or_treatment TEXT NOT NULL DEFAULT 'natural',
    intervention_type TEXT NOT NULL DEFAULT '',
    start_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TEXT NOT NULL DEFAULT '',
    random_seed TEXT NOT NULL DEFAULT '',
    environment_version TEXT NOT NULL DEFAULT '',
    agent_config_version TEXT NOT NULL DEFAULT '',
    model_config_version TEXT NOT NULL DEFAULT '',
    world_rules_version TEXT NOT NULL DEFAULT 'world-runtime-v1',
    status TEXT NOT NULL DEFAULT 'running',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS world_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL DEFAULT '',
    snapshot_type TEXT NOT NULL DEFAULT 'manual_checkpoint',
    world_time TEXT NOT NULL DEFAULT '',
    day INTEGER NOT NULL DEFAULT 0,
    tick_id INTEGER,
    reason TEXT NOT NULL DEFAULT '',
    state_json TEXT NOT NULL DEFAULT '{}',
    schema_version TEXT NOT NULL DEFAULT 'research-v1',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_export_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL DEFAULT '',
    export_format TEXT NOT NULL DEFAULT 'both',
    export_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    quality_report_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_experiment_runs_run_id ON experiment_runs(run_id);
CREATE INDEX IF NOT EXISTS idx_experiment_runs_status ON experiment_runs(status);
CREATE INDEX IF NOT EXISTS idx_world_snapshots_run_id ON world_snapshots(run_id);
CREATE INDEX IF NOT EXISTS idx_world_snapshots_created_at ON world_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_research_export_jobs_run_id ON research_export_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_research_export_jobs_started_at ON research_export_jobs(started_at);
"""
