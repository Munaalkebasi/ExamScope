CREATE TABLE IF NOT EXISTS exams (
    id TEXT PRIMARY KEY,
    course_code TEXT NOT NULL,
    exam_name TEXT NOT NULL,
    exam_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL,
    name TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    practice_score INTEGER NOT NULL,
    last_reviewed TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS progress_history (
    id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL,
    readiness_score INTEGER NOT NULL,
    critical_count INTEGER NOT NULL,
    high_count INTEGER NOT NULL,
    moderate_count INTEGER NOT NULL,
    safe_count INTEGER NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL,
    topic_name TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    theme TEXT NOT NULL DEFAULT 'dark',
    active_exam_id TEXT
);
