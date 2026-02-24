#!/usr/bin/env python3
"""
Memory Search Skill - Semantic search across all memory files.

Provides hybrid BM25 + Vector search with local embeddings.
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sentinel_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(sentinel_root / 'src'))

from memory.semantic_indexer import SemanticIndexer


def main():
    """Execute memory search skill."""
    start_time = time.time()

    # Parse parameters from command line args
    params = {}
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            params[key.lstrip('-')] = value

    # Get parameters
    query = params.get('query', '')
    mode = params.get('mode', 'hybrid')
    file_type = params.get('file_type', None)
    top_k = int(params.get('top_k', '10'))
    recent_days = params.get('recent_days', None)

    # Validate mode
    if mode not in ['hybrid', 'vector', 'bm25']:
        print(json.dumps({
            "success": False,
            "error": f"Invalid mode: {mode}. Use 'hybrid', 'vector', or 'bm25'"
        }))
        sys.exit(1)

    # Initialize indexer
    db_path = sentinel_root / "sentinel_memory.db"

    try:
        indexer = SemanticIndexer(
            db_path=str(db_path),
            chunk_size=400,
            chunk_overlap=80
        )

        # Handle recent context query
        if recent_days is not None:
            days = int(recent_days)
            chunks = indexer.get_recent_context(days=days)

            output = {
                "success": True,
                "mode": "recent_context",
                "days": days,
                "results_count": len(chunks),
                "results": [
                    {
                        "file": Path(c.file_path).name,
                        "file_type": c.file_type,
                        "chunk_text": c.chunk_text[:300] + "..." if len(c.chunk_text) > 300 else c.chunk_text,
                        "created_at": c.created_at,
                        "chunk_index": c.chunk_index
                    }
                    for c in chunks
                ],
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

            print(json.dumps(output, indent=2))
            return

        # Validate query
        if not query:
            print(json.dumps({
                "success": False,
                "error": "Query is required (use --query='your search')"
            }))
            sys.exit(1)

        # Execute search
        if mode == 'hybrid':
            results = indexer.search_hybrid(query, top_k=top_k)
        elif mode == 'vector':
            results = indexer.search_vector(query, top_k=top_k)
        elif mode == 'bm25':
            results = indexer.search_bm25(query, top_k=top_k)

        # Filter by file type if specified
        if file_type:
            results = [r for r in results if r.file_type == file_type]

        # Format output
        output = {
            "success": True,
            "query": query,
            "mode": mode,
            "file_type_filter": file_type,
            "results_count": len(results),
            "results": [
                {
                    "rank": r.rank,
                    "score": round(r.score, 3),
                    "file": Path(r.file_path).name,
                    "file_type": r.file_type,
                    "chunk_text": r.chunk_text[:300] + "..." if len(r.chunk_text) > 300 else r.chunk_text,
                    "chunk_id": r.chunk_id
                }
                for r in results
            ],
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }

        print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
