"""
Database connection and initialization for Sentinel memory system.

Provides async SQLite operations with connection pooling and schema management.
"""

import aiosqlite
from pathlib import Path
from typing import Optional, Any
import json
from datetime import datetime

from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class Database:
    """Async SQLite database manager for Sentinel memory."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file (defaults to config.SQLITE_DB_PATH)
        """
        self.db_path = db_path or config.SQLITE_DB_PATH
        self.connection: Optional[aiosqlite.Connection] = None
        self._initialized = False

    async def connect(self) -> None:
        """Establish database connection."""
        if self.connection is not None:
            logger.warning("Database already connected")
            return

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = await aiosqlite.connect(str(self.db_path))
        self.connection.row_factory = aiosqlite.Row  # Return rows as dictionaries

        # Enable foreign keys
        await self.connection.execute("PRAGMA foreign_keys = ON")

        # Enable WAL mode for better concurrency
        await self.connection.execute("PRAGMA journal_mode = WAL")

        logger.info("Database connected", db_path=str(self.db_path))

    async def close(self) -> None:
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("Database connection closed")

    async def initialize_schema(self) -> None:
        """
        Initialize database schema from schema.sql file.

        Creates all tables, indexes, and initial data if they don't exist.
        """
        if not self.connection:
            await self.connect()

        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        # Read and execute schema
        schema_sql = schema_path.read_text()

        # Split by statement and execute each one
        # SQLite doesn't support executing multiple statements at once via executescript in async
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

        for statement in statements:
            try:
                await self.connection.execute(statement)
            except Exception as e:
                logger.error("Failed to execute schema statement", error=str(e), statement=statement[:100])
                raise

        await self.connection.commit()

        self._initialized = True
        logger.info("Database schema initialized", tables_created=True)

    async def get_schema_version(self) -> int:
        """
        Get current schema version.

        Returns:
            Current schema version number
        """
        if not self.connection:
            await self.connect()

        try:
            cursor = await self.connection.execute(
                "SELECT MAX(version) as version FROM schema_version"
            )
            row = await cursor.fetchone()
            return row['version'] if row and row['version'] else 0
        except Exception:
            return 0

    async def execute(self, query: str, params: Optional[tuple] = None) -> aiosqlite.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Cursor object
        """
        if not self.connection:
            await self.connect()

        if params:
            return await self.connection.execute(query, params)
        return await self.connection.execute(query)

    async def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        if not self.connection:
            await self.connect()

        await self.connection.executemany(query, params_list)
        await self.connection.commit()

    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[dict]:
        """
        Fetch a single row.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Dictionary representing the row, or None if no results
        """
        cursor = await self.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> list[dict]:
        """
        Fetch all rows.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            List of dictionaries representing rows
        """
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def insert(self, table: str, data: dict) -> str:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Dictionary of column->value pairs

        Returns:
            ID of inserted row
        """
        if not self.connection:
            await self.connect()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = await self.connection.execute(query, tuple(data.values()))
        await self.connection.commit()

        return cursor.lastrowid

    async def update(self, table: str, data: dict, where: str, params: tuple) -> int:
        """
        Update rows in a table.

        Args:
            table: Table name
            data: Dictionary of column->value pairs to update
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for WHERE clause

        Returns:
            Number of rows affected
        """
        if not self.connection:
            await self.connect()

        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"

        all_params = tuple(data.values()) + params
        cursor = await self.connection.execute(query, all_params)
        await self.connection.commit()

        return cursor.rowcount

    async def delete(self, table: str, where: str, params: tuple) -> int:
        """
        Delete rows from a table.

        Args:
            table: Table name
            where: WHERE clause (without 'WHERE' keyword)
            params: Parameters for WHERE clause

        Returns:
            Number of rows deleted
        """
        if not self.connection:
            await self.connect()

        query = f"DELETE FROM {table} WHERE {where}"
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()

        return cursor.rowcount

    async def commit(self) -> None:
        """Commit current transaction."""
        if self.connection:
            await self.connection.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self.connection:
            await self.connection.rollback()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        if not self._initialized:
            await self.initialize_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Get the singleton database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


# Helper functions for JSON serialization
def json_serialize(obj: Any) -> str:
    """Serialize object to JSON string for database storage."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return json.dumps(obj)


def json_deserialize(s: Optional[str]) -> Any:
    """Deserialize JSON string from database."""
    if s is None:
        return None
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s
