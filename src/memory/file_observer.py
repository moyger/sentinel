"""
File Observer for Sentinel Memory System.

Watches ~/sentinel/memory/ directory for changes and triggers reindexing.
"""

import time
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .semantic_indexer import SemanticIndexer


class MemoryFileHandler(FileSystemEventHandler):
    """
    Handler for memory file changes.

    Triggers reindexing when markdown files are created/modified.
    """

    def __init__(self, indexer: SemanticIndexer, debounce_seconds: float = 2.0):
        """
        Initialize file handler.

        Args:
            indexer: Semantic indexer instance
            debounce_seconds: Wait time before reindexing (avoid multiple triggers)
        """
        super().__init__()
        self.indexer = indexer
        self.debounce_seconds = debounce_seconds
        self.pending_files = {}  # file_path -> last_event_time

    def _should_index(self, file_path: str) -> bool:
        """Check if file should be indexed."""
        path = Path(file_path)

        # Only index markdown files
        if path.suffix != ".md":
            return False

        # Ignore temp files
        if path.name.startswith(".") or path.name.startswith("~"):
            return False

        # Only index files in memory directory
        if "/memory/" not in str(path):
            return False

        return True

    def _trigger_index(self, file_path: str):
        """Trigger indexing for a file (with debouncing)."""
        if not self._should_index(file_path):
            return

        current_time = time.time()
        last_event_time = self.pending_files.get(file_path, 0)

        # Debounce: only index if enough time has passed
        if current_time - last_event_time < self.debounce_seconds:
            self.pending_files[file_path] = current_time
            return

        # Index the file
        try:
            path = Path(file_path)
            if path.exists():
                print(f"\n🔍 Detected change: {path.name}")
                self.indexer.index_file(path)
                self.pending_files[file_path] = current_time
        except Exception as e:
            print(f"❌ Error indexing {file_path}: {e}")

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if not event.is_directory:
            self._trigger_index(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if not event.is_directory:
            self._trigger_index(event.src_path)


class MemoryObserver:
    """
    File system observer for memory directory.

    Watches for changes and automatically reindexes files.
    """

    def __init__(
        self,
        memory_dir: Path,
        indexer: SemanticIndexer,
        debounce_seconds: float = 2.0
    ):
        """
        Initialize memory observer.

        Args:
            memory_dir: Path to memory directory to watch
            indexer: Semantic indexer instance
            debounce_seconds: Debounce time for reindexing
        """
        self.memory_dir = memory_dir
        self.indexer = indexer
        self.observer = Observer()
        self.handler = MemoryFileHandler(indexer, debounce_seconds)

    def start(self):
        """Start watching memory directory."""
        if not self.memory_dir.exists():
            raise FileNotFoundError(f"Memory directory not found: {self.memory_dir}")

        print(f"👀 Watching {self.memory_dir} for changes...")
        self.observer.schedule(self.handler, str(self.memory_dir), recursive=True)
        self.observer.start()

    def stop(self):
        """Stop watching."""
        print("🛑 Stopping file observer...")
        self.observer.stop()
        self.observer.join()

    def run_forever(self):
        """Run observer indefinitely (blocking)."""
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def index_all_memory_files(memory_dir: Path, indexer: SemanticIndexer):
    """
    Index all existing markdown files in memory directory.

    Args:
        memory_dir: Path to memory directory
        indexer: Semantic indexer instance
    """
    if not memory_dir.exists():
        print(f"⚠️  Memory directory not found: {memory_dir}")
        return

    # Find all markdown files
    md_files = list(memory_dir.rglob("*.md"))

    print(f"\n📚 Found {len(md_files)} markdown files in {memory_dir}")
    print("=" * 70)

    total_chunks = 0
    for file_path in md_files:
        # Skip hidden files
        if file_path.name.startswith("."):
            continue

        try:
            chunks = indexer.index_file(file_path)
            total_chunks += chunks
        except Exception as e:
            print(f"❌ Error indexing {file_path.name}: {e}")

    print("=" * 70)
    print(f"✅ Indexed {len(md_files)} files, {total_chunks} total chunks\n")


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    # Initialize indexer
    memory_dir = Path.home() / "sentinel" / "memory"
    indexer = SemanticIndexer(
        db_path="sentinel_memory.db",
        chunk_size=400,
        chunk_overlap=80
    )

    # Index all existing files
    print("Starting initial indexing...")
    index_all_memory_files(memory_dir, indexer)

    # Start observer
    observer = MemoryObserver(memory_dir, indexer)

    print("\n" + "=" * 70)
    print("MEMORY OBSERVER RUNNING")
    print("=" * 70)
    print(f"Watching: {memory_dir}")
    print("Press Ctrl+C to stop\n")

    observer.run_forever()
