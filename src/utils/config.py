"""
Configuration management for Sentinel.

Loads environment variables and provides typed access to configuration values.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration management."""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MEMORY_DIR = PROJECT_ROOT / "memory"
    DAILY_DIR = MEMORY_DIR / "daily"
    TOPICS_DIR = MEMORY_DIR / "topics"
    CONFIG_DIR = PROJECT_ROOT / "config"
    LOGS_DIR = PROJECT_ROOT / "logs"
    SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

    # Anthropic Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
    CLAUDE_TEMPERATURE: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))

    # Slack Configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN: str = os.getenv("SLACK_APP_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    SLACK_BOT_NAME: str = os.getenv("SLACK_BOT_NAME", "Sentinel")
    SLACK_BOT_EMOJI: str = os.getenv("SLACK_BOT_EMOJI", ":robot_face:")

    # Google Workspace APIs
    GOOGLE_CREDENTIALS_FILE: Path = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "./config/google_credentials.json"))
    GMAIL_USER_EMAIL: str = os.getenv("GMAIL_USER_EMAIL", "")
    GMAIL_CHECK_LABELS: list[str] = os.getenv("GMAIL_CHECK_LABELS", "INBOX,IMPORTANT").split(",")
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    # Asana API
    ASANA_ACCESS_TOKEN: str = os.getenv("ASANA_ACCESS_TOKEN", "")
    ASANA_WORKSPACE_GID: str = os.getenv("ASANA_WORKSPACE_GID", "")

    # Memory System
    OBSIDIAN_VAULT_PATH: Optional[Path] = Path(os.getenv("OBSIDIAN_VAULT_PATH")) if os.getenv("OBSIDIAN_VAULT_PATH") else None
    SQLITE_DB_PATH: Path = Path(os.getenv("SQLITE_DB_PATH", "./memory/sentinel.db"))
    MEMORY_MAX_SESSION_LENGTH: int = int(os.getenv("MEMORY_MAX_SESSION_LENGTH", "1000"))
    MEMORY_DAILY_LOG_RETENTION_DAYS: int = int(os.getenv("MEMORY_DAILY_LOG_RETENTION_DAYS", "90"))

    # Heartbeat Configuration
    HEARTBEAT_INTERVAL_MINUTES: int = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", "30"))
    HEARTBEAT_ENABLE_GMAIL: bool = os.getenv("HEARTBEAT_ENABLE_GMAIL", "true").lower() == "true"
    HEARTBEAT_ENABLE_CALENDAR: bool = os.getenv("HEARTBEAT_ENABLE_CALENDAR", "true").lower() == "true"
    HEARTBEAT_ENABLE_ASANA: bool = os.getenv("HEARTBEAT_ENABLE_ASANA", "true").lower() == "true"
    HEARTBEAT_ENABLE_SLACK: bool = os.getenv("HEARTBEAT_ENABLE_SLACK", "true").lower() == "true"
    HEARTBEAT_QUIET_HOURS_START: str = os.getenv("HEARTBEAT_QUIET_HOURS_START", "22:00")
    HEARTBEAT_QUIET_HOURS_END: str = os.getenv("HEARTBEAT_QUIET_HOURS_END", "08:00")
    HEARTBEAT_TIMEZONE: str = os.getenv("HEARTBEAT_TIMEZONE", "America/New_York")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_PATH: Path = Path(os.getenv("LOG_FILE_PATH", "./logs/sentinel.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Development Settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    ENABLE_TESTING_MODE: bool = os.getenv("ENABLE_TESTING_MODE", "false").lower() == "true"

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that all required configuration values are set.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required API keys
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")

        if not cls.SLACK_BOT_TOKEN:
            errors.append("SLACK_BOT_TOKEN is not set")

        if not cls.SLACK_APP_TOKEN:
            errors.append("SLACK_APP_TOKEN is not set")

        # Check paths exist
        cls.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        cls.DAILY_DIR.mkdir(parents=True, exist_ok=True)
        cls.TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

        return errors

    @classmethod
    def display_config(cls) -> str:
        """Return a formatted string showing current configuration (hiding secrets)."""
        def mask_secret(value: str) -> str:
            """Mask sensitive values."""
            if not value or len(value) < 8:
                return "****"
            return f"{value[:4]}...{value[-4:]}"

        config_lines = [
            "Sentinel Configuration",
            "=" * 50,
            f"Claude Model: {cls.CLAUDE_MODEL}",
            f"Max Tokens: {cls.CLAUDE_MAX_TOKENS}",
            f"Slack Bot Name: {cls.SLACK_BOT_NAME}",
            f"Heartbeat Interval: {cls.HEARTBEAT_INTERVAL_MINUTES} minutes",
            f"Log Level: {cls.LOG_LEVEL}",
            f"Debug Mode: {cls.DEBUG_MODE}",
            "",
            "API Keys:",
            f"  Anthropic: {mask_secret(cls.ANTHROPIC_API_KEY)}",
            f"  Slack Bot: {mask_secret(cls.SLACK_BOT_TOKEN)}",
            f"  Asana: {mask_secret(cls.ASANA_ACCESS_TOKEN)}",
            "",
            "Paths:",
            f"  Memory Dir: {cls.MEMORY_DIR}",
            f"  Database: {cls.SQLITE_DB_PATH}",
            f"  Logs: {cls.LOG_FILE_PATH}",
        ]

        return "\n".join(config_lines)


# Export singleton instance
config = Config()
