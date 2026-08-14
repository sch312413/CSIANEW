CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    whole_day BOOLEAN NOT NULL CHECK (whole_day IN (0, 1)),  -- 0 not 1 yes
    recurrence TEXT,  -- [None, or days of the week]
    starting_datetime TEXT NOT NULL,   
    ending_datetime TEXT NOT NULL 
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,  
    title TEXT NOT NULL,
    due_time TEXT NOT NULL,
    total_minutes INTEGER NOT NULL,     
    scheduled_minute INTEGER DEFAULT 0,  
    status_now TEXT NOT NULL DEFAULT 'active'
        CHECK (status_now IN ('active', 'completed')) 
);

CREATE TABLE IF NOT EXISTS work_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status_now TEXT NOT NULL
        CHECK (status_now IN ('accepted', 'suggested', 'completed')), -- makes sure its accepted, suggested, or completed
    FOREIGN KEY (task_id) REFERENCES tasks (task_id) 
        ON DELETE CASCADE  -- if a task is deleted, its sessions go with it
);

CREATE TABLE IF NOT EXISTS unavailable_windows (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    unavailable_start TEXT NOT NULL,
    unavailable_end TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    settings_id INTEGER PRIMARY KEY CHECK (settings_id = 1),
    max_working INTEGER NOT NULL,
    min_break INTEGER NOT NULL,
    max_session_minutes INTEGER NOT NULL
);

-- some exampliary tasks and settings
-- ##############################################################################################################
INSERT INTO settings (settings_id, max_working, min_break, max_session_minutes)
VALUES (1, 480, 15, 60);

INSERT INTO events (title, whole_day, recurrence, starting_datetime, ending_datetime)
VALUES
    ('CS class', 'class', 0, 'Mon', '2026-09-07T09:00', '2026-09-07T10:00'),
    ('Math class', 'class', 0, 'Tue,Thu', '2026-09-08T11:00', '2026-09-08T12:00'),
    ('School trip', 'event', 1, NULL, '2026-09-12T00:00', '2026-09-13T00:00');

INSERT INTO tasks (title, due_time, total_minutes, scheduled_minute, status_now)
VALUES
    ('IA write-up', '2026-09-20T23:59', 180, 0, 'active'),
    ('Math homework', '2026-09-10T23:59', 60, 0, 'active'),
    ('Read chapter 4', '2026-09-05T23:59', 45, 0, 'active');

INSERT INTO work_sessions (task_id, start_time, end_time, status_now)
VALUES
    (1, '2026-09-02T14:00', '2026-09-02T15:00', 'suggested'),
    (1, '2026-09-03T14:00', '2026-09-03T15:00', 'suggested'),
    (3, '2026-09-01T10:00', '2026-09-01T10:45', 'completed');

INSERT INTO unavailable_windows (title, unavailable_start, unavailable_end)
VALUES
    ('Sleep', '23:00', '07:00'),
    ('Dinner', '18:00', '19:00');