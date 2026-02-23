-- Sentinel Memory System Database Schema
-- SQLite database for session indexing, RAG, and memory management

-- Sessions table: Track conversation sessions across different adapters
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,  -- UUID for session
    adapter TEXT NOT NULL,  -- 'slack', 'cli', 'terminal'
    channel_id TEXT,  -- Slack channel or thread ID
    user_id TEXT,  -- User identifier
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',  -- 'active', 'archived', 'completed'
    metadata TEXT,  -- JSON for additional context
    daily_log_path TEXT  -- Path to daily log file
);

CREATE INDEX IF NOT EXISTS idx_sessions_adapter ON sessions(adapter);
CREATE INDEX IF NOT EXISTS idx_sessions_channel ON sessions(channel_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);

-- Messages table: Individual messages within sessions
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,  -- UUID for message
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    token_count INTEGER,
    metadata TEXT,  -- JSON for attachments, reactions, etc.
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- Memory entries: Key decisions, facts, and context extracted from conversations
CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY,  -- UUID
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    entry_type TEXT NOT NULL,  -- 'fact', 'decision', 'preference', 'context', 'skill'
    importance INTEGER DEFAULT 5,  -- 1-10 scale
    source_session_id TEXT,  -- Optional reference to originating session
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,  -- Comma-separated tags
    markdown_path TEXT,  -- Path to corresponding markdown file
    metadata TEXT,  -- JSON for additional data
    FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_updated ON memory_entries(updated_at);

-- Topics: Organize memories by topic/category
CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,  -- Slug-based ID (e.g., 'work-projects')
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    markdown_path TEXT  -- Path to topic markdown file
);

CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);

-- Memory-Topic associations: Many-to-many relationship
CREATE TABLE IF NOT EXISTS memory_topics (
    memory_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    PRIMARY KEY (memory_id, topic_id),
    FOREIGN KEY (memory_id) REFERENCES memory_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Embeddings table: Vector embeddings for semantic search (RAG)
-- Using sqlite-vec extension for vector similarity search
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,  -- UUID
    content_type TEXT NOT NULL,  -- 'message', 'memory', 'topic'
    content_id TEXT NOT NULL,  -- Foreign key to messages, memory_entries, or topics
    embedding BLOB NOT NULL,  -- Vector embedding (serialized)
    embedding_model TEXT NOT NULL,  -- Model used (e.g., 'voyage-2', 'text-embedding-3-small')
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_type, content_id)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_content ON embeddings(content_id);

-- Heartbeat logs: Track proactive monitoring activities
CREATE TABLE IF NOT EXISTS heartbeat_logs (
    id TEXT PRIMARY KEY,  -- UUID
    run_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    monitors_checked TEXT NOT NULL,  -- JSON array of checked monitors
    alerts_sent INTEGER DEFAULT 0,
    issues_found INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT DEFAULT 'completed',  -- 'completed', 'failed', 'partial'
    error_message TEXT,
    metadata TEXT  -- JSON for detailed results
);

CREATE INDEX IF NOT EXISTS idx_heartbeat_run ON heartbeat_logs(run_at);
CREATE INDEX IF NOT EXISTS idx_heartbeat_status ON heartbeat_logs(status);

-- Alerts: Proactive notifications sent by heartbeat
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,  -- UUID
    heartbeat_log_id TEXT,
    alert_type TEXT NOT NULL,  -- 'email', 'meeting', 'task', 'message'
    source TEXT NOT NULL,  -- 'gmail', 'calendar', 'asana', 'slack'
    title TEXT NOT NULL,
    description TEXT,
    urgency TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'urgent'
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    metadata TEXT,  -- JSON for source-specific data
    FOREIGN KEY (heartbeat_log_id) REFERENCES heartbeat_logs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_source ON alerts(source);
CREATE INDEX IF NOT EXISTS idx_alerts_urgency ON alerts(urgency);
CREATE INDEX IF NOT EXISTS idx_alerts_sent ON alerts(sent_at);
CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts(acknowledged);

-- Skills: Track available skills and their usage
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,  -- Skill name/identifier
    name TEXT NOT NULL,
    description TEXT,
    skill_path TEXT NOT NULL,  -- Path to .claude/skills/{skill_name}
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    metadata TEXT  -- JSON for skill configuration
);

CREATE INDEX IF NOT EXISTS idx_skills_enabled ON skills(enabled);
CREATE INDEX IF NOT EXISTS idx_skills_usage ON skills(usage_count);

-- Skill executions: Log skill usage for debugging and analytics
CREATE TABLE IF NOT EXISTS skill_executions (
    id TEXT PRIMARY KEY,  -- UUID
    skill_id TEXT NOT NULL,
    session_id TEXT,  -- Optional: which session triggered it
    input_params TEXT,  -- JSON of input parameters
    output_result TEXT,  -- Skill output
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL,
    status TEXT DEFAULT 'success',  -- 'success', 'failed', 'timeout'
    error_message TEXT,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_exec_skill ON skill_executions(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_exec_session ON skill_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_skill_exec_time ON skill_executions(executed_at);
CREATE INDEX IF NOT EXISTS idx_skill_exec_status ON skill_executions(status);

-- Daily summaries: Generated summaries for each day
CREATE TABLE IF NOT EXISTS daily_summaries (
    date DATE PRIMARY KEY,
    summary TEXT NOT NULL,
    sessions_count INTEGER DEFAULT 0,
    messages_count INTEGER DEFAULT 0,
    alerts_count INTEGER DEFAULT 0,
    key_events TEXT,  -- JSON array of important events
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    markdown_path TEXT  -- Path to daily/{date}.md file
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_summaries(date);

-- Version tracking for schema migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema with sessions, messages, memories, embeddings, heartbeat, and skills');
