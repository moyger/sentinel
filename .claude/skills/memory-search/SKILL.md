# Memory Search

Semantic search across all memory files using hybrid BM25 + Vector search.

## Description

The Memory Search skill provides intelligent search across all of Sentinel's memory:
- Core files (soul.md, memory.md, user.md, agents.md)
- Daily logs
- Topics

Uses hybrid search combining:
- **BM25**: Keyword-based full-text search
- **Vector similarity**: Semantic understanding with embeddings

## Usage

```bash
# Search memory
sentinel skill memory-search --query "What are my goals?"

# Search specific file types
sentinel skill memory-search --query "project status" --file-type daily

# Vector-only search (semantic)
sentinel skill memory-search --query "preferences" --mode vector

# Get recent context
sentinel skill memory-search --recent-days 2
```

## Parameters

```yaml
query:
  type: string
  required: false
  description: "Search query"

mode:
  type: string
  required: false
  default: "hybrid"
  enum: ["hybrid", "vector", "bm25"]
  description: "Search mode"

file_type:
  type: string
  required: false
  description: "Filter by file type (soul, memory, daily, topic, user)"

top_k:
  type: integer
  required: false
  default: 10
  description: "Number of results to return"

recent_days:
  type: integer
  required: false
  description: "Get recent context (last N days)"
```

## Output

Returns search results as JSON:

```json
{
  "success": true,
  "query": "What are my goals?",
  "mode": "hybrid",
  "results_count": 5,
  "results": [
    {
      "rank": 1,
      "score": 0.87,
      "file": "soul.md",
      "file_type": "soul",
      "chunk_text": "# Soul - Identity & Evolving Personality...",
      "chunk_id": "uuid-here"
    }
  ],
  "execution_time_ms": 234
}
```

## Examples

### Find preferences
```bash
$ sentinel skill memory-search --query "What do I prefer?"

Results:
1. [soul.md] Score: 0.85
   "Prefers creative projects over algo trading"

2. [user.md] Score: 0.73
   "Prefers lo-fi and Nujabes-style music"
```

### Find project status
```bash
$ sentinel skill memory-search --query "music automation status" --file-type daily

Results:
1. [2026-02-23.md] Score: 0.91
   "Music Automation System - Phase 1 complete"
   "Generated 4 demo MIDI files with varying creativity"
```

### Get recent context
```bash
$ sentinel skill memory-search --recent-days 2

Found 11 recent chunks from last 2 days:
- 2026-02-23.md (8 chunks)
- test-topic.md (2 chunks)
- agents.md (1 chunk)
```

## Integration

### SessionStart Hook
Automatically loads recent context (last 2 days) at session start:

```json
{
  "on_session_start": {
    "memory_search": {
      "recent_days": 2,
      "auto_load": true
    }
  }
}
```

### Slack Integration
Search memory via Slack:

```
/sentinel search What did I work on yesterday?
```

### Heartbeat Integration
Used by heartbeat to check for:
- Overdue tasks
- Upcoming events
- Important reminders

## Performance

- **Cold start**: ~2-3 seconds (model loading)
- **Warm search**: ~200-500ms
- **Recent context**: <100ms

## Dependencies

- `src/memory/semantic_indexer.py` - Core search engine
- `sentence-transformers` - Embedding model
- `sqlite-vec` - Vector search (optional, falls back to numpy)

## Notes

- **Local**: All processing happens locally (no API calls)
- **Fast**: Optimized for sub-second search
- **Smart**: Understands semantic meaning, not just keywords
- **Privacy**: Your memory never leaves your machine

---

**Category**: Memory Management
**Local**: Yes
**Requires API**: No
**Execution Time**: ~0.2-3 seconds
**Safety**: High (read-only)
