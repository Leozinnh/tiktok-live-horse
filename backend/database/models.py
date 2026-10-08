CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS viewers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tiktok_username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    races_count INTEGER DEFAULT 0,
    wins_count INTEGER DEFAULT 0,
    favorite_horse_id INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_viewers_username ON viewers(tiktok_username);
CREATE INDEX IF NOT EXISTS idx_viewers_xp ON viewers(xp DESC);

CREATE TABLE IF NOT EXISTS races (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_number INTEGER NOT NULL,
    status TEXT DEFAULT 'VOTING',
    winner_horse_id INTEGER DEFAULT NULL,
    total_participants INTEGER DEFAULT 0,
    total_gifts INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS race_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL,
    viewer_id INTEGER NOT NULL,
    horse_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(race_id) REFERENCES races(id),
    FOREIGN KEY(viewer_id) REFERENCES viewers(id),
    UNIQUE(race_id, viewer_id)
);

CREATE INDEX IF NOT EXISTS idx_choices_race ON race_choices(race_id);

CREATE TABLE IF NOT EXISTS race_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER NOT NULL,
    horse_id INTEGER NOT NULL,
    final_position INTEGER NOT NULL,
    finish_time_ms INTEGER NOT NULL,
    FOREIGN KEY(race_id) REFERENCES races(id)
);

CREATE TABLE IF NOT EXISTS events_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id INTEGER,
    viewer_id INTEGER,
    event_type TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    viewer_id INTEGER NOT NULL,
    season_number INTEGER DEFAULT 1,
    season_xp INTEGER DEFAULT 0,
    season_wins INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(viewer_id) REFERENCES viewers(id),
    UNIQUE(viewer_id, season_number)
);
"""
