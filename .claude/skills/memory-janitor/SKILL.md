# Memory Janitor

Distill daily logs into durable facts and update core memory files.

## Description

The Memory Janitor skill processes daily log files to extract important facts, decisions, preferences, and learnings. It proposes updates to core memory files (soul.md, memory.md, user.md, agents.md) and topics.

This is automated memory consolidation - turning transient daily logs into permanent knowledge.

## Usage

Run periodically (e.g., end of day) to consolidate memory:

```bash
# Process today's log
sentinel skill memory-janitor

# Process specific date
sentinel skill memory-janitor --date 2026-02-23

# Dry run (show proposals without applying)
sentinel skill memory-janitor --dry-run
```

## Parameters

```yaml
date:
  type: string
  required: false
  description: "Date to process (YYYY-MM-DD). Defaults to today."

dry_run:
  type: boolean
  required: false
  default: false
  description: "Show proposals without applying them."

auto_apply:
  type: boolean
  required: false
  default: false
  description: "Automatically apply proposed changes without confirmation."
```

## What It Does

1. **Reads daily log** for specified date
2. **Analyzes content** using semantic search
3. **Extracts durable facts**:
   - Personal preferences
   - Important decisions
   - Lessons learned
   - Project status updates
   - Skills acquired
4. **Proposes updates** to core memory files
5. **Updates topics** (creates new topics if needed)
6. **Cleans up** redundant information

## Output

Returns proposed updates as JSON:

```json
{
  "date_processed": "2026-02-23",
  "facts_extracted": 12,
  "proposals": [
    {
      "file": "memory/soul.md",
      "section": "Values & Principles",
      "action": "append",
      "content": "Prefers building creative projects over algo trading"
    },
    {
      "file": "memory/memory.md",
      "section": "Projects",
      "action": "update",
      "content": "Music Automation System - Phase 1 complete (melody generation)"
    }
  ],
  "topics_created": ["music-automation", "ableton-osc"],
  "applied": false
}
```

## Integration

Called automatically by:
- **Heartbeat** (end of day)
- **SessionEnd hook** (after long sessions)
- **Manual trigger** via Slack or CLI

## Example

```bash
$ sentinel skill memory-janitor --date 2026-02-23

🧹 Memory Janitor - Processing 2026-02-23
===========================================

📖 Reading daily log...
✓ Found 387 lines

🧠 Analyzing content...
✓ Extracted 12 facts

📝 Proposed updates:

[soul.md] Values & Principles
  + Prefers creative projects over algo trading

[memory.md] Projects
  ~ Music Automation System - Phase 1 complete

[agents.md] Skills
  + Music generation (melody, motif, humanization)

[topics/] New Topics
  + music-automation.md
  + ableton-osc.md

Apply changes? [y/N]:
```

## Dependencies

- `src/memory/semantic_indexer.py` - Search daily logs
- `src/memory/memory_manager.py` - Update core files
- OpenAI/Anthropic API - For distillation (optional, falls back to rules)

## Error Handling

- **Daily log not found**: Skip gracefully
- **Parse errors**: Log warning, continue
- **Update conflicts**: Show diff, ask for confirmation
- **API failures**: Fall back to rule-based extraction

## Notes

- **Non-destructive**: Always creates backups before updating
- **Versioned**: Uses git to track memory changes
- **Reviewable**: Shows diffs before applying
- **Reversible**: Can rollback via git

---

**Category**: Memory Management
**Local**: Yes
**Requires API**: Optional (falls back to rules)
**Execution Time**: ~5-15 seconds
**Safety**: High (non-destructive, reviewable)
