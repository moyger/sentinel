-- Semantic Memory Index Schema with sqlite-vec
-- Vector search extension for Sentinel's memory system

-- Enable vec0 extension
-- Note: sqlite-vec must be loaded before creating virtual tables

-- Chunks table: stores text chunks with metadata
CREATE TABLE IF NOT EXISTS memory_chunks (
    chunk_id TEXT PRIMARY KEY,  -- UUID for chunk
    file_path TEXT NOT NULL,     -- Path to source markdown file
    file_type TEXT NOT NULL,     -- 'soul', 'memory', 'daily', 'topic', 'user'
    chunk_text TEXT NOT NULL,    -- Actual text content
    chunk_index INTEGER NOT NULL, -- Position in file (0-based)
    token_count INTEGER NOT NULL, -- Number of tokens in chunk
    created_at TEXT NOT NULL,    -- ISO timestamp
    updated_at TEXT NOT NULL,    -- ISO timestamp
    metadata TEXT                -- JSON metadata (dates, tags, etc.)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_file_path ON memory_chunks(file_path);
CREATE INDEX IF NOT EXISTS idx_file_type ON memory_chunks(file_type);
CREATE INDEX IF NOT EXISTS idx_created_at ON memory_chunks(created_at);

-- Vector table: stores embeddings for chunks
-- Using vec0 virtual table from sqlite-vec
-- Embedding dimension: 384 (all-MiniLM-L6-v2 model)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory_chunks USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);

-- BM25 full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS fts_memory_chunks USING fts5(
    chunk_id UNINDEXED,
    chunk_text,
    file_path UNINDEXED,
    file_type UNINDEXED,
    content='memory_chunks',
    content_rowid='rowid'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS memory_chunks_ai AFTER INSERT ON memory_chunks BEGIN
    INSERT INTO fts_memory_chunks(rowid, chunk_id, chunk_text, file_path, file_type)
    VALUES (NEW.rowid, NEW.chunk_id, NEW.chunk_text, NEW.file_path, NEW.file_type);
END;

CREATE TRIGGER IF NOT EXISTS memory_chunks_ad AFTER DELETE ON memory_chunks BEGIN
    DELETE FROM fts_memory_chunks WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER IF NOT EXISTS memory_chunks_au AFTER UPDATE ON memory_chunks BEGIN
    UPDATE fts_memory_chunks
    SET chunk_text = NEW.chunk_text,
        file_path = NEW.file_path,
        file_type = NEW.file_type
    WHERE rowid = NEW.rowid;
END;

-- File tracking: track which files have been indexed
CREATE TABLE IF NOT EXISTS indexed_files (
    file_path TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,      -- SHA256 of content
    last_indexed TEXT NOT NULL,   -- ISO timestamp
    chunk_count INTEGER NOT NULL
);

-- Search history: track what users search for
CREATE TABLE IF NOT EXISTS search_history (
    search_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    search_type TEXT NOT NULL,    -- 'vector', 'bm25', 'hybrid'
    results_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- View: Recent chunks (last 2 days)
CREATE VIEW IF NOT EXISTS recent_chunks AS
SELECT
    chunk_id,
    file_path,
    file_type,
    chunk_text,
    created_at
FROM memory_chunks
WHERE datetime(created_at) >= datetime('now', '-2 days')
ORDER BY created_at DESC;
