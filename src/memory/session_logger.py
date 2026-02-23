"""
Session logging system for Sentinel.

Manages conversation sessions, logs messages to both SQLite and Markdown,
and handles session lifecycle.
"""

from datetime import datetime
from typing import Optional, Any
from pathlib import Path

from .database import Database, get_database
from .operations import MemoryOperations
from .markdown_manager import MarkdownManager
from .models import Session, Message
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class SessionLogger:
    """Manages conversation sessions and message logging."""

    def __init__(
        self,
        db: Optional[Database] = None,
        markdown_manager: Optional[MarkdownManager] = None
    ):
        """
        Initialize session logger.

        Args:
            db: Database instance (defaults to singleton)
            markdown_manager: MarkdownManager instance
        """
        self.db = db or get_database()
        self.ops = MemoryOperations(self.db)
        self.markdown = markdown_manager or MarkdownManager()
        self._current_session: Optional[Session] = None

    # ========== Session Management ==========

    async def start_session(
        self,
        adapter: str,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Session:
        """
        Start a new conversation session.

        Args:
            adapter: Adapter type ('slack', 'cli', 'terminal')
            channel_id: Optional channel/thread ID
            user_id: Optional user identifier
            metadata: Optional metadata

        Returns:
            Created session
        """
        # Create daily log for today if it doesn't exist
        daily_log_path = self.markdown.create_daily_log()

        session = Session(
            adapter=adapter,
            channel_id=channel_id,
            user_id=user_id,
            metadata=metadata,
            daily_log_path=str(daily_log_path)
        )

        await self.ops.create_session(session)

        # Log to daily markdown
        session_entry = self._format_session_start(session)
        self.markdown.append_to_daily_log(session_entry, section="Sessions")

        self._current_session = session
        logger.info("Session started", session_id=session.id, adapter=adapter)

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        return await self.ops.get_session(session_id)

    async def get_or_create_session(
        self,
        adapter: str,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Session:
        """
        Get existing active session or create new one.

        Args:
            adapter: Adapter type
            channel_id: Optional channel/thread ID
            user_id: Optional user identifier

        Returns:
            Session (existing or new)
        """
        # Try to find existing active session
        active_sessions = await self.ops.get_active_sessions(adapter=adapter)

        for session in active_sessions:
            if session.channel_id == channel_id and session.user_id == user_id:
                self._current_session = session
                logger.debug("Using existing session", session_id=session.id)
                return session

        # No existing session, create new one
        return await self.start_session(adapter, channel_id, user_id)

    async def end_session(self, session_id: Optional[str] = None) -> None:
        """
        End a conversation session.

        Args:
            session_id: Session ID (defaults to current session)
        """
        if session_id is None and self._current_session:
            session_id = self._current_session.id

        if not session_id:
            logger.warning("No session to end")
            return

        await self.ops.update_session(
            session_id,
            status='completed',
            last_activity=datetime.now()
        )

        # Log to daily markdown
        session = await self.ops.get_session(session_id)
        if session:
            session_summary = self._format_session_end(session)
            self.markdown.append_to_daily_log(session_summary, section="Sessions")

        if self._current_session and self._current_session.id == session_id:
            self._current_session = None

        logger.info("Session ended", session_id=session_id)

    async def archive_old_sessions(self, days_old: int = 7) -> int:
        """
        Archive sessions older than specified days.

        Args:
            days_old: Number of days after which to archive

        Returns:
            Number of sessions archived
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days_old)
        cutoff_str = cutoff.isoformat()

        # Get old active sessions
        rows = await self.db.fetch_all(
            """SELECT id FROM sessions
               WHERE status = 'active' AND last_activity < ?""",
            (cutoff_str,)
        )

        count = 0
        for row in rows:
            await self.ops.update_session(row['id'], status='archived')
            count += 1

        logger.info("Sessions archived", count=count, days_old=days_old)
        return count

    # ========== Message Logging ==========

    async def log_message(
        self,
        content: str,
        role: str = "user",
        session_id: Optional[str] = None,
        token_count: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Message:
        """
        Log a message to the current or specified session.

        Args:
            content: Message content
            role: Message role ('user', 'assistant', 'system')
            session_id: Optional session ID (defaults to current)
            token_count: Optional token count
            metadata: Optional metadata

        Returns:
            Created message
        """
        # Determine session
        if session_id is None:
            if self._current_session:
                session_id = self._current_session.id
            else:
                raise ValueError("No active session. Call start_session() first.")

        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata
        )

        await self.ops.create_message(message)

        # Log to daily markdown
        await self._append_message_to_daily_log(message, session_id)

        # Check if session should be rotated
        session = await self.ops.get_session(session_id)
        if session and session.message_count >= config.MEMORY_MAX_SESSION_LENGTH:
            logger.info("Session reached max length, ending", session_id=session_id)
            await self.end_session(session_id)

        logger.debug("Message logged", message_id=message.id, role=role, session_id=session_id)

        return message

    async def log_user_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Message:
        """
        Log a user message.

        Args:
            content: Message content
            session_id: Optional session ID
            metadata: Optional metadata

        Returns:
            Created message
        """
        return await self.log_message(content, role="user", session_id=session_id, metadata=metadata)

    async def log_assistant_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        token_count: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> Message:
        """
        Log an assistant message.

        Args:
            content: Message content
            session_id: Optional session ID
            token_count: Optional token count
            metadata: Optional metadata

        Returns:
            Created message
        """
        return await self.log_message(
            content,
            role="assistant",
            session_id=session_id,
            token_count=token_count,
            metadata=metadata
        )

    async def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[Message]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID (defaults to current)
            limit: Optional limit on number of messages

        Returns:
            List of messages
        """
        if session_id is None and self._current_session:
            session_id = self._current_session.id

        if not session_id:
            return []

        return await self.ops.get_session_messages(session_id, limit=limit)

    async def get_context_window(
        self,
        session_id: Optional[str] = None,
        max_messages: int = 50
    ) -> list[dict[str, str]]:
        """
        Get conversation context formatted for Claude API.

        Args:
            session_id: Session ID (defaults to current)
            max_messages: Maximum number of recent messages

        Returns:
            List of message dicts with 'role' and 'content'
        """
        messages = await self.get_conversation_history(session_id, limit=max_messages)

        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
            if msg.role in ["user", "assistant"]  # Filter out system messages
        ]

    # ========== Daily Log Integration ==========

    async def _append_message_to_daily_log(self, message: Message, session_id: str) -> None:
        """
        Append message to daily log in Markdown.

        Args:
            message: Message to log
            session_id: Session ID
        """
        session = await self.ops.get_session(session_id)
        if not session or not session.daily_log_path:
            return

        # Format message for markdown
        timestamp = message.timestamp.strftime("%H:%M:%S")
        role_prefix = "👤" if message.role == "user" else "🤖" if message.role == "assistant" else "⚙️"

        # Truncate long messages for daily log
        content = message.content
        if len(content) > 500:
            content = content[:497] + "..."

        entry = f"**[{timestamp}]** {role_prefix} {content}\n"

        # Find session section in daily log
        daily_log_path = Path(session.daily_log_path)
        if daily_log_path.exists():
            current = self.markdown.read_file(daily_log_path)

            # Find or create session subsection
            session_header = f"### Session {session_id[:8]}"
            if session_header not in current:
                # Add new session subsection
                session_start = f"\n{session_header} ({session.adapter})\n\n{entry}"
                self.markdown.append_to_daily_log(session_start, section="Sessions")
            else:
                # Append to existing session
                pattern = f"({session_header}.*?)(?=\n### |(?=\n## )|(?=\Z))"
                import re
                match = re.search(pattern, current, flags=re.DOTALL)
                if match:
                    session_section = match.group(1)
                    updated_section = session_section.rstrip() + f"\n{entry}"
                    updated = current.replace(session_section, updated_section)
                    self.markdown.write_file(daily_log_path, updated)

    def _format_session_start(self, session: Session) -> str:
        """Format session start for daily log."""
        timestamp = session.started_at.strftime("%H:%M:%S")
        return f"\n### Session {session.id[:8]} ({session.adapter})\n**Started:** {timestamp}\n"

    def _format_session_end(self, session: Session) -> str:
        """Format session end summary."""
        duration = (session.last_activity - session.started_at).total_seconds() / 60
        return f"**Ended:** {session.last_activity.strftime('%H:%M:%S')} ({session.message_count} messages, {duration:.1f} min)\n"

    # ========== Utility Methods ==========

    @property
    def current_session(self) -> Optional[Session]:
        """Get current active session."""
        return self._current_session

    async def initialize(self) -> None:
        """Initialize session logger (connect to database)."""
        if not self.db.connection:
            await self.db.connect()
            await self.db.initialize_schema()
        logger.info("Session logger initialized")

    async def close(self) -> None:
        """Close session logger."""
        if self._current_session:
            await self.end_session()
        await self.db.close()
        logger.info("Session logger closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
