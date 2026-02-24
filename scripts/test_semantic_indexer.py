#!/usr/bin/env python3
"""
Test the semantic memory indexer.

This script:
1. Initializes the semantic indexer
2. Indexes all existing memory files
3. Tests different search modes (BM25, Vector, Hybrid)
4. Demonstrates recent context retrieval
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from memory.semantic_indexer import SemanticIndexer
from memory.file_observer import index_all_memory_files


def main():
    print("=" * 70)
    print("SENTINEL SEMANTIC MEMORY INDEXER - TEST")
    print("=" * 70)
    print()

    # Initialize indexer
    print("📦 Initializing semantic indexer...")
    memory_dir = Path.home() / "sentinel" / "memory"
    db_path = Path.home() / "sentinel" / "sentinel_memory.db"

    indexer = SemanticIndexer(
        db_path=str(db_path),
        model_name="all-MiniLM-L6-v2",
        chunk_size=400,
        chunk_overlap=80
    )

    print()
    print("=" * 70)
    print("INDEXING MEMORY FILES")
    print("=" * 70)
    print()

    # Index all memory files
    index_all_memory_files(memory_dir, indexer)

    # Test queries
    test_queries = [
        "What are Sentinel's goals and purpose?",
        "Tell me about the music generation system",
        "What tasks are pending or in progress?",
        "What skills does Sentinel have?",
    ]

    print("\n" + "=" * 70)
    print("TESTING SEARCH MODES")
    print("=" * 70)

    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 70)

        # Test BM25 search
        print("\n📝 BM25 Search (keyword-based):")
        try:
            bm25_results = indexer.search_bm25(query, top_k=3)
            if bm25_results:
                for r in bm25_results:
                    print(f"  [{r.rank}] Score: {r.score:.3f} | {Path(r.file_path).name}")
                    print(f"      {r.chunk_text[:150]}...")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  ⚠️  BM25 search error: {e}")

        # Test Vector search
        print("\n🧠 Vector Search (semantic similarity):")
        try:
            vector_results = indexer.search_vector(query, top_k=3)
            if vector_results:
                for r in vector_results:
                    print(f"  [{r.rank}] Score: {r.score:.3f} | {Path(r.file_path).name}")
                    print(f"      {r.chunk_text[:150]}...")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  ⚠️  Vector search error: {e}")

        # Test Hybrid search
        print("\n🔬 Hybrid Search (BM25 + Vector):")
        try:
            hybrid_results = indexer.search_hybrid(query, top_k=3)
            if hybrid_results:
                for r in hybrid_results:
                    print(f"  [{r.rank}] Score: {r.score:.3f} | {Path(r.file_path).name}")
                    print(f"      {r.chunk_text[:150]}...")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  ⚠️  Hybrid search error: {e}")

        print()

    # Test recent context
    print("\n" + "=" * 70)
    print("RECENT CONTEXT (Last 2 Days)")
    print("=" * 70)
    print()

    try:
        recent = indexer.get_recent_context(days=2)
        print(f"Found {len(recent)} recent chunks")

        if recent:
            print("\nMost recent chunks:")
            for chunk in recent[:5]:
                print(f"\n  • {Path(chunk.file_path).name} (index {chunk.chunk_index})")
                print(f"    Created: {chunk.created_at}")
                print(f"    {chunk.chunk_text[:100]}...")
    except Exception as e:
        print(f"⚠️  Error getting recent context: {e}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print(f"Database: {db_path}")
    print(f"Memory dir: {memory_dir}")
    print()


if __name__ == "__main__":
    main()
