"""
Semantic Memory Indexer for Sentinel.

Provides:
- Text chunking with overlap
- Local embedding generation (sentence-transformers)
- Vector search with sqlite-vec
- Hybrid BM25 + Vector search
"""

import hashlib
import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Chunk:
    """Text chunk with metadata."""
    chunk_id: str
    file_path: str
    file_type: str
    chunk_text: str
    chunk_index: int
    token_count: int
    created_at: str
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Search result with score."""
    chunk_id: str
    file_path: str
    file_type: str
    chunk_text: str
    score: float
    rank: int


class SemanticIndexer:
    """
    Semantic memory indexer using sqlite-vec and sentence-transformers.

    Features:
    - Local embeddings (no API calls)
    - Hybrid BM25 + Vector search
    - Automatic chunking with overlap
    - File change detection
    """

    def __init__(
        self,
        db_path: str = "sentinel_memory.db",
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 400,
        chunk_overlap: int = 80
    ):
        """
        Initialize semantic indexer.

        Args:
            db_path: Path to SQLite database
            model_name: Sentence-transformers model name
            chunk_size: Chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize database
        self._init_db()

        # Load embedding model
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded (embedding dim: {self.embedding_dim})")

    def _init_db(self):
        """Initialize database with schema."""
        conn = sqlite3.connect(self.db_path)

        # Load sqlite-vec extension
        try:
            conn.enable_load_extension(True)
            # Try common installation paths
            vec_paths = [
                "vec0",  # If in system path
                "/opt/homebrew/lib/vec0.dylib",  # Homebrew on macOS
                str(Path.home() / ".local/lib/vec0.so"),  # User install
            ]

            loaded = False
            for vec_path in vec_paths:
                try:
                    conn.load_extension(vec_path)
                    loaded = True
                    print(f"✅ Loaded sqlite-vec from {vec_path}")
                    break
                except sqlite3.OperationalError:
                    continue

            if not loaded:
                print("⚠️  sqlite-vec extension not found, using pure Python fallback")
        except AttributeError:
            print("⚠️  SQLite extensions not supported, using pure Python fallback")

        # Load schema
        schema_path = Path(__file__).parent / "memory_index_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        # Execute schema (may fail on vec0 if extension not loaded)
        try:
            conn.executescript(schema_sql)
            print("✅ Database schema initialized")
        except sqlite3.OperationalError as e:
            if "no such module: vec0" in str(e):
                # Skip vec0 table, use numpy-based search instead
                print("⚠️  Skipping vec0 virtual table, using numpy fallback")
                # Execute schema without vec0
                schema_lines = schema_sql.split("\n")
                filtered_schema = []
                skip_block = False
                for line in schema_lines:
                    if "CREATE VIRTUAL TABLE" in line and "vec0" in line:
                        skip_block = True
                    if skip_block and ");" in line:
                        skip_block = False
                        continue
                    if not skip_block:
                        filtered_schema.append(line)

                conn.executescript("\n".join(filtered_schema))
                print("✅ Database schema initialized (without vec0)")
            else:
                raise

        conn.commit()
        conn.close()

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Simple word-based chunking (not perfect but fast).
        For production, use tiktoken for accurate token counting.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split into words (approximation of tokens)
        words = text.split()

        chunks = []
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            # Move forward with overlap
            start += (self.chunk_size - self.chunk_overlap)

            # Stop if we've covered all words
            if end >= len(words):
                break

        return chunks

    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from path."""
        path_str = str(file_path)

        if "soul.md" in path_str:
            return "soul"
        elif "memory.md" in path_str:
            return "memory"
        elif "user.md" in path_str:
            return "user"
        elif "/daily/" in path_str:
            return "daily"
        elif "/topics/" in path_str:
            return "topic"
        else:
            return "other"

    def index_file(self, file_path: Path) -> int:
        """
        Index a markdown file.

        Args:
            file_path: Path to file

        Returns:
            Number of chunks created
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check if file has changed
        file_hash = self._get_file_hash(file_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if already indexed
        cursor.execute(
            "SELECT file_hash FROM indexed_files WHERE file_path = ?",
            (str(file_path),)
        )
        result = cursor.fetchone()

        if result and result[0] == file_hash:
            print(f"⏭️  Skipping {file_path.name} (unchanged)")
            conn.close()
            return 0

        # Delete old chunks if re-indexing
        if result:
            print(f"🔄 Re-indexing {file_path.name}...")
            cursor.execute("DELETE FROM memory_chunks WHERE file_path = ?", (str(file_path),))
            # Also delete from vec table if it exists
            try:
                cursor.execute("DELETE FROM vec_memory_chunks WHERE chunk_id IN (SELECT chunk_id FROM memory_chunks WHERE file_path = ?)", (str(file_path),))
            except sqlite3.OperationalError:
                pass  # vec table might not exist

        # Read file content
        with open(file_path) as f:
            content = f.read()

        # Chunk text
        chunks = self.chunk_text(content)
        file_type = self._get_file_type(file_path)
        now = datetime.now().isoformat()

        # Generate embeddings for all chunks
        print(f"📝 Chunking {file_path.name}: {len(chunks)} chunks")
        print(f"🧠 Generating embeddings...")
        embeddings = self.model.encode(chunks, show_progress_bar=False)

        # Insert chunks
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())

            # Insert chunk
            cursor.execute("""
                INSERT INTO memory_chunks
                (chunk_id, file_path, file_type, chunk_text, chunk_index, token_count, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                str(file_path),
                file_type,
                chunk,
                idx,
                len(chunk.split()),  # Approximation
                now,
                now,
                json.dumps({})
            ))

            # Insert embedding (if vec table exists)
            try:
                cursor.execute("""
                    INSERT INTO vec_memory_chunks (chunk_id, embedding)
                    VALUES (?, ?)
                """, (chunk_id, embedding.tobytes()))
            except sqlite3.OperationalError:
                # Store embeddings in separate fallback table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings_fallback (
                        chunk_id TEXT PRIMARY KEY,
                        embedding BLOB NOT NULL
                    )
                """)
                cursor.execute("""
                    INSERT INTO embeddings_fallback (chunk_id, embedding)
                    VALUES (?, ?)
                """, (chunk_id, np.array(embedding, dtype=np.float32).tobytes()))

        # Update indexed_files
        cursor.execute("""
            INSERT OR REPLACE INTO indexed_files
            (file_path, file_hash, last_indexed, chunk_count)
            VALUES (?, ?, ?, ?)
        """, (str(file_path), file_hash, now, len(chunks)))

        conn.commit()
        conn.close()

        print(f"✅ Indexed {file_path.name}: {len(chunks)} chunks")
        return len(chunks)

    def search_bm25(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        BM25 full-text search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                mc.chunk_id,
                mc.file_path,
                mc.file_type,
                mc.chunk_text,
                fts.rank AS score
            FROM fts_memory_chunks fts
            JOIN memory_chunks mc ON fts.chunk_id = mc.chunk_id
            WHERE fts_memory_chunks MATCH ?
            ORDER BY fts.rank
            LIMIT ?
        """, (query, top_k))

        results = []
        for rank, row in enumerate(cursor.fetchall(), 1):
            results.append(SearchResult(
                chunk_id=row[0],
                file_path=row[1],
                file_type=row[2],
                chunk_text=row[3],
                score=float(row[4]),
                rank=rank
            ))

        conn.close()
        return results

    def search_vector(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Vector similarity search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try vec0 search first
        try:
            cursor.execute("""
                SELECT
                    mc.chunk_id,
                    mc.file_path,
                    mc.file_type,
                    mc.chunk_text,
                    vec_distance_cosine(vec.embedding, ?) AS score
                FROM vec_memory_chunks vec
                JOIN memory_chunks mc ON vec.chunk_id = mc.chunk_id
                ORDER BY score ASC
                LIMIT ?
            """, (query_embedding.tobytes(), top_k))

            results = []
            for rank, row in enumerate(cursor.fetchall(), 1):
                results.append(SearchResult(
                    chunk_id=row[0],
                    file_path=row[1],
                    file_type=row[2],
                    chunk_text=row[3],
                    score=1 - float(row[4]),  # Convert distance to similarity
                    rank=rank
                ))

            conn.close()
            return results

        except sqlite3.OperationalError:
            # Fallback to numpy-based search
            cursor.execute("SELECT chunk_id, embedding FROM embeddings_fallback")
            rows = cursor.fetchall()

            # Compute similarities
            similarities = []
            for chunk_id, embedding_bytes in rows:
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                similarities.append((chunk_id, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunk_ids = [x[0] for x in similarities[:top_k]]

            # Fetch chunk details
            placeholders = ",".join(["?"] * len(top_chunk_ids))
            cursor.execute(f"""
                SELECT chunk_id, file_path, file_type, chunk_text
                FROM memory_chunks
                WHERE chunk_id IN ({placeholders})
            """, top_chunk_ids)

            chunk_map = {row[0]: row for row in cursor.fetchall()}

            # Build results in order
            results = []
            for rank, (chunk_id, score) in enumerate(similarities[:top_k], 1):
                if chunk_id in chunk_map:
                    row = chunk_map[chunk_id]
                    results.append(SearchResult(
                        chunk_id=row[0],
                        file_path=row[1],
                        file_type=row[2],
                        chunk_text=row[3],
                        score=float(score),
                        rank=rank
                    ))

            conn.close()
            return results

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Hybrid BM25 + Vector search with score fusion.

        Args:
            query: Search query
            top_k: Number of results
            bm25_weight: Weight for BM25 scores (0-1)
            vector_weight: Weight for vector scores (0-1)

        Returns:
            List of search results sorted by combined score
        """
        # Get both sets of results
        bm25_results = self.search_bm25(query, top_k * 2)
        vector_results = self.search_vector(query, top_k * 2)

        # Normalize scores to 0-1 range
        def normalize_scores(results: List[SearchResult]) -> Dict[str, float]:
            if not results:
                return {}

            scores = [r.score for r in results]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score

            if score_range == 0:
                return {r.chunk_id: 1.0 for r in results}

            return {
                r.chunk_id: (r.score - min_score) / score_range
                for r in results
            }

        bm25_scores = normalize_scores(bm25_results)
        vector_scores = normalize_scores(vector_results)

        # Combine scores
        all_chunk_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        combined_scores = {}

        for chunk_id in all_chunk_ids:
            bm25_score = bm25_scores.get(chunk_id, 0.0)
            vector_score = vector_scores.get(chunk_id, 0.0)
            combined_scores[chunk_id] = (
                bm25_weight * bm25_score +
                vector_weight * vector_score
            )

        # Sort by combined score
        sorted_chunk_ids = sorted(
            combined_scores.keys(),
            key=lambda x: combined_scores[x],
            reverse=True
        )[:top_k]

        # Fetch chunk details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(sorted_chunk_ids))
        cursor.execute(f"""
            SELECT chunk_id, file_path, file_type, chunk_text
            FROM memory_chunks
            WHERE chunk_id IN ({placeholders})
        """, sorted_chunk_ids)

        chunk_map = {row[0]: row for row in cursor.fetchall()}
        conn.close()

        # Build final results
        results = []
        for rank, chunk_id in enumerate(sorted_chunk_ids, 1):
            if chunk_id in chunk_map:
                row = chunk_map[chunk_id]
                results.append(SearchResult(
                    chunk_id=row[0],
                    file_path=row[1],
                    file_type=row[2],
                    chunk_text=row[3],
                    score=combined_scores[chunk_id],
                    rank=rank
                ))

        return results

    def get_recent_context(self, days: int = 2) -> List[Chunk]:
        """
        Get recent chunks (e.g., last 2 days of daily logs).

        Args:
            days: Number of days to look back

        Returns:
            List of recent chunks
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, file_path, file_type, chunk_text, chunk_index, token_count, created_at, metadata
            FROM memory_chunks
            WHERE datetime(created_at) >= datetime('now', ? || ' days')
            ORDER BY created_at DESC
        """, (f"-{days}",))

        results = []
        for row in cursor.fetchall():
            results.append(Chunk(
                chunk_id=row[0],
                file_path=row[1],
                file_type=row[2],
                chunk_text=row[3],
                chunk_index=row[4],
                token_count=row[5],
                created_at=row[6],
                metadata=json.loads(row[7]) if row[7] else {}
            ))

        conn.close()
        return results


# Example usage
if __name__ == "__main__":
    # Initialize indexer
    indexer = SemanticIndexer(
        db_path="test_memory.db",
        chunk_size=400,
        chunk_overlap=80
    )

    # Test with a sample file
    test_file = Path("memory/soul.md")
    if test_file.exists():
        indexer.index_file(test_file)

        # Test search
        results = indexer.search_hybrid("what are sentinel's goals?", top_k=5)

        print("\n" + "=" * 70)
        print("SEARCH RESULTS")
        print("=" * 70)
        for r in results:
            print(f"\n[{r.rank}] Score: {r.score:.3f} | {r.file_type}")
            print(f"    {r.chunk_text[:200]}...")
