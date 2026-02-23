"""
Data models for Sentinel memory system.

Pydantic models for type-safe memory operations.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


class Session(BaseModel):
    """Conversation session model."""
    id: str = Field(default_factory=generate_uuid)
    adapter: str  # 'slack', 'cli', 'terminal'
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    message_count: int = 0
    status: str = "active"  # 'active', 'archived', 'completed'
    metadata: Optional[dict[str, Any]] = None
    daily_log_path: Optional[str] = None


class Message(BaseModel):
    """Individual message within a session."""
    id: str = Field(default_factory=generate_uuid)
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    token_count: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


class MemoryEntry(BaseModel):
    """Key decisions, facts, and context extracted from conversations."""
    id: str = Field(default_factory=generate_uuid)
    title: str
    content: str
    entry_type: str  # 'fact', 'decision', 'preference', 'context', 'skill'
    importance: int = 5  # 1-10 scale
    source_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: Optional[list[str]] = None
    markdown_path: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class Topic(BaseModel):
    """Topic for organizing memories."""
    id: str  # Slug-based ID (e.g., 'work-projects')
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    markdown_path: Optional[str] = None


class Alert(BaseModel):
    """Proactive notification from heartbeat."""
    id: str = Field(default_factory=generate_uuid)
    heartbeat_log_id: Optional[str] = None
    alert_type: str  # 'email', 'meeting', 'task', 'message'
    source: str  # 'gmail', 'calendar', 'asana', 'slack'
    title: str
    description: Optional[str] = None
    urgency: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    sent_at: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class HeartbeatLog(BaseModel):
    """Log of heartbeat monitoring run."""
    id: str = Field(default_factory=generate_uuid)
    run_at: datetime = Field(default_factory=datetime.now)
    monitors_checked: list[str]
    alerts_sent: int = 0
    issues_found: int = 0
    duration_seconds: Optional[float] = None
    status: str = "completed"  # 'completed', 'failed', 'partial'
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class Skill(BaseModel):
    """Skill definition and metadata."""
    id: str  # Skill name/identifier
    name: str
    description: Optional[str] = None
    skill_path: str  # Path to .claude/skills/{skill_name}
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    metadata: Optional[dict[str, Any]] = None


class SkillExecution(BaseModel):
    """Log of skill execution."""
    id: str = Field(default_factory=generate_uuid)
    skill_id: str
    session_id: Optional[str] = None
    input_params: Optional[dict[str, Any]] = None
    output_result: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.now)
    duration_seconds: Optional[float] = None
    status: str = "success"  # 'success', 'failed', 'timeout'
    error_message: Optional[str] = None


class DailySummary(BaseModel):
    """Daily summary of activity."""
    date: str  # YYYY-MM-DD format
    summary: str
    sessions_count: int = 0
    messages_count: int = 0
    alerts_count: int = 0
    key_events: Optional[list[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    markdown_path: Optional[str] = None
