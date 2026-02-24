#!/usr/bin/env python3
"""
Memory Janitor Skill - Distill daily logs into durable facts.

This skill processes daily logs and extracts important information to update
core memory files (soul.md, memory.md, user.md, agents.md).
"""

import sys
import json
from pathlib import Path
from datetime import datetime, date

# Add src to path
sentinel_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(sentinel_root / 'src'))

from memory.semantic_indexer import SemanticIndexer
from memory.memory_manager import MemoryManager


def main():
    """Execute memory janitor skill."""
    # Parse parameters from command line args
    params = {}
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            params[key.lstrip('-')] = value

    # Get parameters
    date_str = params.get('date', date.today().isoformat())
    dry_run = params.get('dry_run', 'false').lower() == 'true'
    auto_apply = params.get('auto_apply', 'false').lower() == 'true'

    # Parse date
    try:
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print(json.dumps({
            "success": False,
            "error": f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        }))
        sys.exit(1)

    # Initialize
    memory_dir = sentinel_root / "memory"
    db_path = sentinel_root / "sentinel_memory.db"

    try:
        indexer = SemanticIndexer(
            db_path=str(db_path),
            chunk_size=400,
            chunk_overlap=80
        )

        manager = MemoryManager(memory_dir, indexer)

        # Run distillation
        result = manager.distill_daily_log(
            log_date=log_date,
            dry_run=dry_run
        )

        # Output result as JSON
        output = {
            "success": True,
            "date_processed": result.date_processed,
            "facts_extracted": result.facts_extracted,
            "proposals": [
                {
                    "file": p.file_path,
                    "section": p.section,
                    "action": p.action,
                    "content": p.content,
                    "confidence": p.confidence
                }
                for p in result.proposals
            ],
            "topics_created": result.topics_created,
            "applied": result.applied
        }

        print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
