# Semantic Memory System

OpenClaw-style semantic memory indexer for Sentinel.

## Overview

Sentinel's semantic memory system provides intelligent search and retrieval across all memory files using local embeddings and hybrid search.

### Key Features

- **Local embeddings** - No API calls, runs entirely on your machine
- **Hybrid search** - Combines BM25 (keyword) + Vector (semantic) search
- **Auto-indexing** - Watches memory directory for changes
- **Memory distillation** - Extracts durable facts from daily logs
- **Fast** - Sub-second search after initial model load

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Memory Files                         │
│  (soul.md, memory.md, daily/*.md, topics/*.md)         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              File Observer (Watchdog)                   │
│  Detects changes → Triggers reindexing                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│           Semantic Indexer                              │
│  ┌─────────────────────────────────────────┐           │
│  │ 1. Chunking (400 tokens, 80 overlap)    │           │
│  │ 2. Embedding (all-MiniLM-L6-v2)         │           │
│  │ 3. Storage (SQLite + sqlite-vec)         │           │
│  └─────────────────────────────────────────┘           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                 Search Engine                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐         │
│  │   BM25   │  │  Vector  │  │    Hybrid    │         │
│  │ (FTS5)   │  │ (Cosine) │  │ (Combined)   │         │
│  └──────────┘  └──────────┘  └──────────────┘         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Skills & Integration                       │
│  • memory-search (semantic search)                      │
│  • memory-janitor (distillation)                        │
│  • SessionStart hook (auto-load context)                │
│  • Slack commands                                       │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Semantic Indexer ([src/memory/semantic_indexer.py](../src/memory/semantic_indexer.py))

Core search engine providing:

```python
from memory.semantic_indexer import SemanticIndexer

indexer = SemanticIndexer(
    db_path="sentinel_memory.db",
    model_name="all-MiniLM-L6-v2",  # 384-dim embeddings
    chunk_size=400,                  # tokens per chunk
    chunk_overlap=80                 # overlap between chunks
)

# Index a file
indexer.index_file(Path("memory/soul.md"))

# Search
results = indexer.search_hybrid("What are my goals?", top_k=10)
```

**Methods:**
- `index_file(path)` - Index a markdown file
- `search_hybrid(query, top_k)` - Hybrid BM25 + Vector search
- `search_vector(query, top_k)` - Pure semantic search
- `search_bm25(query, top_k)` - Pure keyword search
- `get_recent_context(days)` - Get recent chunks

### 2. File Observer ([src/memory/file_observer.py](../src/memory/file_observer.py))

Watches `~/sentinel/memory/` for changes and auto-reindexes:

```python
from memory.file_observer import MemoryObserver

observer = MemoryObserver(memory_dir, indexer, debounce_seconds=2.0)
observer.start()  # Background watching
```

**Features:**
- Debouncing (avoid multiple triggers)
- Recursive watching (all subdirectories)
- Markdown-only filtering
- Change detection (via file hashing)

### 3. Memory Manager ([src/memory/memory_manager.py](../src/memory/memory_manager.py))

Distills daily logs into durable facts:

```python
from memory.memory_manager import MemoryManager

manager = MemoryManager(memory_dir, indexer)

# Process daily log
result = manager.distill_daily_log(
    log_date=date(2026, 2, 23),
    dry_run=False
)
```

**Extraction patterns:**
- **Preferences**: "I prefer X"
- **Decisions**: "Decided to X"
- **Learnings**: "Learned that X"
- **Achievements**: "Built/Created/Implemented X"
- **Completions**: Headers with "Complete", "Done", "✅"

### 4. Skills

#### memory-search
```bash
# Semantic search
sentinel skill memory-search --query "What are my goals?"

# Filter by type
sentinel skill memory-search --query "project status" --file-type daily

# Recent context
sentinel skill memory-search --recent-days 2
```

#### memory-janitor
```bash
# Distill today's log
sentinel skill memory-janitor

# Specific date
sentinel skill memory-janitor --date 2026-02-23

# Dry run
sentinel skill memory-janitor --dry-run
```

## Database Schema

### Tables

**memory_chunks** - Text chunks with metadata
```sql
CREATE TABLE memory_chunks (
    chunk_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'soul', 'memory', 'daily', 'topic'
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);
```

**vec_memory_chunks** - Vector embeddings (sqlite-vec)
```sql
CREATE VIRTUAL TABLE vec_memory_chunks USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding FLOAT[384]  -- all-MiniLM-L6-v2 dimension
);
```

**fts_memory_chunks** - Full-text search index (FTS5)
```sql
CREATE VIRTUAL TABLE fts_memory_chunks USING fts5(
    chunk_id UNINDEXED,
    chunk_text,
    file_path UNINDEXED,
    file_type UNINDEXED
);
```

## Usage Examples

### Example 1: Index All Memory Files

```bash
python scripts/test_semantic_indexer.py
```

Output:
```
📚 Found 6 markdown files in ~/sentinel/memory
======================================================================
✅ Indexed soul.md: 1 chunks
✅ Indexed memory.md: 2 chunks
✅ Indexed user.md: 2 chunks
✅ Indexed agents.md: 4 chunks
✅ Indexed 2026-02-23.md: 1 chunks
======================================================================
✅ Indexed 6 files, 10 total chunks
```

### Example 2: Search Memory

```python
from memory.semantic_indexer import SemanticIndexer

indexer = SemanticIndexer("sentinel_memory.db")

# Semantic search
results = indexer.search_hybrid("What music projects am I working on?", top_k=5)

for r in results:
    print(f"[{r.rank}] {Path(r.file_path).name} - Score: {r.score:.2f}")
    print(f"    {r.chunk_text[:100]}...")
```

Output:
```
[1] 2026-02-23.md - Score: 0.89
    Music Automation System - Phase 1 complete. Generated 4 demo MIDI files...

[2] memory.md - Score: 0.73
    Projects: Music generation with varying creativity levels...
```

### Example 3: Distill Daily Log

```bash
sentinel skill memory-janitor --date 2026-02-23
```

Output:
```
🧹 Memory Janitor - Processing 2026-02-23
======================================================================

📖 Reading daily log... (387 lines)
🧠 Extracted 12 facts

📝 Proposed updates:
======================================================================

[soul.md]
  + [Values & Principles] Prefers creative projects over algo trading

[memory.md]
  + [Projects] Music Automation System - Phase 1 complete
  + [Lessons] Ableton CAN be fully automated with AbletonOSC

[topics/] New Topics
  + music-automation.md
  + ableton-osc.md

Apply changes? [y/N]:
```

### Example 4: Watch Directory for Changes

```python
from memory.file_observer import MemoryObserver, index_all_memory_files

# Initial indexing
index_all_memory_files(memory_dir, indexer)

# Start watching
observer = MemoryObserver(memory_dir, indexer)
observer.run_forever()  # Blocks until Ctrl+C
```

Output:
```
👀 Watching /Users/you/sentinel/memory for changes...

🔍 Detected change: soul.md
📝 Chunking soul.md: 1 chunks
🧠 Generating embeddings...
✅ Indexed soul.md: 1 chunks
```

## Integration Points

### SessionStart Hook

Add to [`.claude/settings.json`](../.claude/settings.json):

```json
{
  "hooks": {
    "session_start": {
      "command": "sentinel skill memory-search --recent-days 2",
      "description": "Load recent context at session start"
    }
  }
}
```

### Heartbeat Integration

The heartbeat can trigger memory janitor at end of day:

```python
# In heartbeat loop
if datetime.now().hour == 23:  # 11 PM
    skill_manager.execute("memory-janitor")
```

### Slack Integration

Search memory via Slack:

```python
@app.command("/search")
def handle_search(ack, command, say):
    query = command['text']
    result = skill_manager.execute("memory-search", {"query": query})
    say(format_search_results(result))
```

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Model load (cold) | ~2-3s | First time only |
| Index file (1000 tokens) | ~300ms | Including embedding |
| Vector search (warm) | ~200ms | 10 results |
| Hybrid search | ~400ms | BM25 + Vector |
| Recent context | <100ms | No embedding needed |

### Optimization Tips

1. **Keep model loaded** - Reuse SemanticIndexer instance
2. **Batch indexing** - Index multiple files together
3. **Use file hashing** - Skip unchanged files
4. **Limit top_k** - Fewer results = faster search

## Troubleshooting

### Issue: "sqlite-vec extension not found"

**Solution**: Falls back to numpy-based search automatically. Performance impact minimal.

### Issue: "FTS5 syntax error near apostrophe"

**Cause**: BM25 search doesn't handle special characters well.

**Solution**: Use vector or hybrid search instead:
```python
results = indexer.search_vector(query)  # More robust
```

### Issue: "Model download taking forever"

**Cause**: First-time download of sentence-transformers model (~90MB).

**Solution**: Model cached after first download to `~/.cache/torch/sentence_transformers/`.

### Issue: "Out of memory"

**Cause**: Too many chunks or large embedding model.

**Solution**:
- Increase `chunk_size` (fewer chunks)
- Decrease `chunk_overlap`
- Use smaller model: `all-MiniLM-L6-v2` (384d) instead of larger models

## Future Enhancements

### Short-term
- [ ] Fix BM25 special character handling
- [ ] Add time-based weighting (recent = more relevant)
- [ ] Topic auto-linking (suggest related topics)

### Medium-term
- [ ] Multi-modal search (images, audio)
- [ ] Query expansion (synonyms, related terms)
- [ ] Personalized ranking (learn from user clicks)

### Long-term
- [ ] Distributed search (multiple machines)
- [ ] Real-time streaming (index as you type)
- [ ] Knowledge graph integration

## Dependencies

```
sentence-transformers>=5.0.0  # Local embeddings
sqlite-vec>=0.1.0              # Vector search
watchdog>=6.0.0                # File monitoring
numpy>=1.20.0                  # Fallback vector ops
```

## Files Created

```
src/memory/
├── semantic_indexer.py          # Core search engine
├── file_observer.py             # Auto-indexing watcher
├── memory_manager.py            # Distillation logic
└── memory_index_schema.sql      # Database schema

.claude/skills/
├── memory-search/
│   ├── SKILL.md
│   └── memory-search.py
└── memory-janitor/
    ├── SKILL.md
    └── memory-janitor.py

scripts/
└── test_semantic_indexer.py     # Test script

docs/
└── SEMANTIC_MEMORY.md           # This file
```

## References

- [OpenClaw Memory System](https://github.com/moyger/openclaw) - Inspiration
- [sentence-transformers](https://www.sbert.net/) - Embedding library
- [sqlite-vec](https://github.com/asg017/sqlite-vec) - Vector search extension
- [FTS5](https://www.sqlite.org/fts5.html) - SQLite full-text search

---

**Built with Claude Code** 🤖
**Date**: February 24, 2026
