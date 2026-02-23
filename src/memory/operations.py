"""
CRUD operations for Sentinel memory system.

Provides high-level operations for sessions, messages, memories, and other entities.
"""

from datetime import datetime, date
from typing import Optional, Any
import json

from .database import Database, json_serialize, json_deserialize
from .models import (
    Session, Message, MemoryEntry, Topic, Alert,
    HeartbeatLog, Skill, SkillExecution, DailySummary
)
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MemoryOperations:
    """High-level memory operations."""

    def __init__(self, db: Database):
        """
        Initialize memory operations.

        Args:
            db: Database instance
        """
        self.db = db

    # ========== Session Operations ==========

    async def create_session(self, session: Session) -> str:
        """
        Create a new conversation session.

        Args:
            session: Session model

        Returns:
            Session ID
        """
        data = {
            'id': session.id,
            'adapter': session.adapter,
            'channel_id': session.channel_id,
            'user_id': session.user_id,
            'started_at': session.started_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'message_count': session.message_count,
            'status': session.status,
            'metadata': json_serialize(session.metadata) if session.metadata else None,
            'daily_log_path': session.daily_log_path,
        }

        await self.db.insert('sessions', data)
        logger.info("Session created", session_id=session.id, adapter=session.adapter)
        return session.id

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session model or None
        """
        row = await self.db.fetch_one(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )
        if not row:
            return None

        return Session(
            id=row['id'],
            adapter=row['adapter'],
            channel_id=row['channel_id'],
            user_id=row['user_id'],
            started_at=datetime.fromisoformat(row['started_at']),
            last_activity=datetime.fromisoformat(row['last_activity']),
            message_count=row['message_count'],
            status=row['status'],
            metadata=json_deserialize(row['metadata']),
            daily_log_path=row['daily_log_path'],
        )

    async def update_session(self, session_id: str, **kwargs) -> None:
        """
        Update session fields.

        Args:
            session_id: Session ID
            **kwargs: Fields to update
        """
        # Convert datetime objects to ISO format
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                kwargs[key] = value.isoformat()
            elif isinstance(value, dict):
                kwargs[key] = json_serialize(value)

        await self.db.update('sessions', kwargs, 'id = ?', (session_id,))
        logger.debug("Session updated", session_id=session_id, fields=list(kwargs.keys()))

    async def get_active_sessions(self, adapter: Optional[str] = None) -> list[Session]:
        """
        Get all active sessions.

        Args:
            adapter: Optional filter by adapter type

        Returns:
            List of active sessions
        """
        if adapter:
            rows = await self.db.fetch_all(
                "SELECT * FROM sessions WHERE status = 'active' AND adapter = ? ORDER BY last_activity DESC",
                (adapter,)
            )
        else:
            rows = await self.db.fetch_all(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY last_activity DESC"
            )

        return [Session(
            id=row['id'],
            adapter=row['adapter'],
            channel_id=row['channel_id'],
            user_id=row['user_id'],
            started_at=datetime.fromisoformat(row['started_at']),
            last_activity=datetime.fromisoformat(row['last_activity']),
            message_count=row['message_count'],
            status=row['status'],
            metadata=json_deserialize(row['metadata']),
            daily_log_path=row['daily_log_path'],
        ) for row in rows]

    # ========== Message Operations ==========

    async def create_message(self, message: Message) -> str:
        """
        Create a new message in a session.

        Args:
            message: Message model

        Returns:
            Message ID
        """
        data = {
            'id': message.id,
            'session_id': message.session_id,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'token_count': message.token_count,
            'metadata': json_serialize(message.metadata) if message.metadata else None,
        }

        await self.db.insert('messages', data)

        # Update session message count and last activity
        await self.db.execute(
            """UPDATE sessions
               SET message_count = message_count + 1,
                   last_activity = ?
               WHERE id = ?""",
            (message.timestamp.isoformat(), message.session_id)
        )
        await self.db.commit()

        logger.debug("Message created", message_id=message.id, session_id=message.session_id, role=message.role)
        return message.id

    async def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[Message]:
        """
        Get messages for a session.

        Args:
            session_id: Session ID
            limit: Optional limit on number of messages
            offset: Number of messages to skip

        Returns:
            List of messages
        """
        query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC"
        params = [session_id]

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = await self.db.fetch_all(query, tuple(params))

        return [Message(
            id=row['id'],
            session_id=row['session_id'],
            role=row['role'],
            content=row['content'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            token_count=row['token_count'],
            metadata=json_deserialize(row['metadata']),
        ) for row in rows]

    # ========== Memory Entry Operations ==========

    async def create_memory(self, memory: MemoryEntry) -> str:
        """
        Create a new memory entry.

        Args:
            memory: MemoryEntry model

        Returns:
            Memory ID
        """
        data = {
            'id': memory.id,
            'title': memory.title,
            'content': memory.content,
            'entry_type': memory.entry_type,
            'importance': memory.importance,
            'source_session_id': memory.source_session_id,
            'created_at': memory.created_at.isoformat(),
            'updated_at': memory.updated_at.isoformat(),
            'tags': ','.join(memory.tags) if memory.tags else None,
            'markdown_path': memory.markdown_path,
            'metadata': json_serialize(memory.metadata) if memory.metadata else None,
        }

        await self.db.insert('memory_entries', data)
        logger.info("Memory created", memory_id=memory.id, type=memory.entry_type, title=memory.title)
        return memory.id

    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get memory entry by ID.

        Args:
            memory_id: Memory ID

        Returns:
            MemoryEntry model or None
        """
        row = await self.db.fetch_one(
            "SELECT * FROM memory_entries WHERE id = ?",
            (memory_id,)
        )
        if not row:
            return None

        return MemoryEntry(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            entry_type=row['entry_type'],
            importance=row['importance'],
            source_session_id=row['source_session_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            tags=row['tags'].split(',') if row['tags'] else None,
            markdown_path=row['markdown_path'],
            metadata=json_deserialize(row['metadata']),
        )

    async def update_memory(self, memory_id: str, **kwargs) -> None:
        """
        Update memory entry fields.

        Args:
            memory_id: Memory ID
            **kwargs: Fields to update
        """
        # Always update updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()

        # Convert data types
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                kwargs[key] = value.isoformat()
            elif isinstance(value, list) and key == 'tags':
                kwargs[key] = ','.join(value)
            elif isinstance(value, dict):
                kwargs[key] = json_serialize(value)

        await self.db.update('memory_entries', kwargs, 'id = ?', (memory_id,))
        logger.debug("Memory updated", memory_id=memory_id, fields=list(kwargs.keys()))

    async def search_memories(
        self,
        entry_type: Optional[str] = None,
        min_importance: Optional[int] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50
    ) -> list[MemoryEntry]:
        """
        Search memory entries by filters.

        Args:
            entry_type: Filter by entry type
            min_importance: Minimum importance level
            tags: Filter by tags
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        query = "SELECT * FROM memory_entries WHERE 1=1"
        params = []

        if entry_type:
            query += " AND entry_type = ?"
            params.append(entry_type)

        if min_importance:
            query += " AND importance >= ?"
            params.append(min_importance)

        if tags:
            # Simple tag matching (can be enhanced with full-text search)
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            query += f" AND ({tag_conditions})"
            params.extend([f"%{tag}%" for tag in tags])

        query += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        rows = await self.db.fetch_all(query, tuple(params))

        return [MemoryEntry(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            entry_type=row['entry_type'],
            importance=row['importance'],
            source_session_id=row['source_session_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            tags=row['tags'].split(',') if row['tags'] else None,
            markdown_path=row['markdown_path'],
            metadata=json_deserialize(row['metadata']),
        ) for row in rows]

    # ========== Topic Operations ==========

    async def create_topic(self, topic: Topic) -> str:
        """
        Create a new topic.

        Args:
            topic: Topic model

        Returns:
            Topic ID
        """
        data = {
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'created_at': topic.created_at.isoformat(),
            'updated_at': topic.updated_at.isoformat(),
            'markdown_path': topic.markdown_path,
        }

        await self.db.insert('topics', data)
        logger.info("Topic created", topic_id=topic.id, name=topic.name)
        return topic.id

    async def link_memory_to_topic(self, memory_id: str, topic_id: str) -> None:
        """
        Link a memory entry to a topic.

        Args:
            memory_id: Memory ID
            topic_id: Topic ID
        """
        try:
            await self.db.insert('memory_topics', {
                'memory_id': memory_id,
                'topic_id': topic_id
            })
            logger.debug("Memory linked to topic", memory_id=memory_id, topic_id=topic_id)
        except Exception as e:
            # Link might already exist
            logger.debug("Failed to link memory to topic", error=str(e))

    async def get_topic_memories(self, topic_id: str) -> list[MemoryEntry]:
        """
        Get all memories associated with a topic.

        Args:
            topic_id: Topic ID

        Returns:
            List of memory entries
        """
        rows = await self.db.fetch_all(
            """SELECT m.* FROM memory_entries m
               JOIN memory_topics mt ON m.id = mt.memory_id
               WHERE mt.topic_id = ?
               ORDER BY m.importance DESC, m.updated_at DESC""",
            (topic_id,)
        )

        return [MemoryEntry(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            entry_type=row['entry_type'],
            importance=row['importance'],
            source_session_id=row['source_session_id'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            tags=row['tags'].split(',') if row['tags'] else None,
            markdown_path=row['markdown_path'],
            metadata=json_deserialize(row['metadata']),
        ) for row in rows]

    # ========== Alert Operations ==========

    async def create_alert(self, alert: Alert) -> str:
        """
        Create a new alert.

        Args:
            alert: Alert model

        Returns:
            Alert ID
        """
        data = {
            'id': alert.id,
            'heartbeat_log_id': alert.heartbeat_log_id,
            'alert_type': alert.alert_type,
            'source': alert.source,
            'title': alert.title,
            'description': alert.description,
            'urgency': alert.urgency,
            'sent_at': alert.sent_at.isoformat(),
            'acknowledged': alert.acknowledged,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'metadata': json_serialize(alert.metadata) if alert.metadata else None,
        }

        await self.db.insert('alerts', data)
        logger.info("Alert created", alert_id=alert.id, type=alert.alert_type, urgency=alert.urgency)
        return alert.id

    async def acknowledge_alert(self, alert_id: str) -> None:
        """
        Mark an alert as acknowledged.

        Args:
            alert_id: Alert ID
        """
        await self.db.update('alerts', {
            'acknowledged': True,
            'acknowledged_at': datetime.now().isoformat()
        }, 'id = ?', (alert_id,))
        logger.debug("Alert acknowledged", alert_id=alert_id)

    async def get_unacknowledged_alerts(self, limit: int = 50) -> list[Alert]:
        """
        Get unacknowledged alerts.

        Args:
            limit: Maximum number of results

        Returns:
            List of alerts
        """
        rows = await self.db.fetch_all(
            """SELECT * FROM alerts
               WHERE acknowledged = 0
               ORDER BY urgency DESC, sent_at DESC
               LIMIT ?""",
            (limit,)
        )

        urgency_order = {'urgent': 4, 'high': 3, 'normal': 2, 'low': 1}

        return sorted([Alert(
            id=row['id'],
            heartbeat_log_id=row['heartbeat_log_id'],
            alert_type=row['alert_type'],
            source=row['source'],
            title=row['title'],
            description=row['description'],
            urgency=row['urgency'],
            sent_at=datetime.fromisoformat(row['sent_at']),
            acknowledged=bool(row['acknowledged']),
            acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
            metadata=json_deserialize(row['metadata']),
        ) for row in rows], key=lambda a: urgency_order.get(a.urgency, 0), reverse=True)
