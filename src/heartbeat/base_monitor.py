"""
Base monitor interface for all data source monitors.

Provides a common interface that all monitors (Gmail, Calendar, Asana, Slack)
must implement for consistency and reliability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Alert:
    """Represents a single alert from a monitor."""

    def __init__(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        source: str = "",
        metadata: Dict[str, Any] = None
    ):
        """
        Create an alert.

        Args:
            title: Alert title
            message: Alert message/description
            priority: Priority level ("urgent", "normal", "low")
            source: Source monitor name
            metadata: Additional alert data
        """
        self.title = title
        self.message = message
        self.priority = priority
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseMonitor(ABC):
    """
    Abstract base class for all data source monitors.

    Each monitor (Gmail, Calendar, Asana, Slack) should inherit from this
    class and implement the check() method.
    """

    def __init__(self, name: str):
        """
        Initialize base monitor.

        Args:
            name: Monitor name (e.g., "gmail", "calendar")
        """
        self.name = name
        self.last_check: datetime = None
        self.last_result: Dict[str, Any] = None
        self.enabled = True

        logger.info("Monitor created", monitor=self.name)

    @abstractmethod
    async def check(self) -> Dict[str, Any]:
        """
        Perform monitoring check.

        This method should:
        1. Connect to the data source
        2. Fetch relevant data
        3. Analyze the data for important items
        4. Return results with alerts

        Returns:
            Dictionary with structure:
            {
                "alerts": [Alert.to_dict(), ...],
                "data": {...},  # Raw or processed data
                "metadata": {...}  # Additional context
            }
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the monitor (authentication, setup, etc.).

        This method is called once during startup to prepare the monitor.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources (close connections, etc.).

        This method is called during shutdown.
        """
        pass

    def create_alert(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """
        Create an alert from this monitor.

        Args:
            title: Alert title
            message: Alert message
            priority: Priority level
            metadata: Additional data

        Returns:
            Alert instance
        """
        return Alert(
            title=title,
            message=message,
            priority=priority,
            source=self.name,
            metadata=metadata
        )

    def is_enabled(self) -> bool:
        """Check if monitor is enabled."""
        return self.enabled

    def enable(self) -> None:
        """Enable the monitor."""
        self.enabled = True
        logger.info("Monitor enabled", monitor=self.name)

    def disable(self) -> None:
        """Disable the monitor."""
        self.enabled = False
        logger.info("Monitor disabled", monitor=self.name)

    def get_last_check(self) -> datetime:
        """Get timestamp of last check."""
        return self.last_check

    def get_last_result(self) -> Dict[str, Any]:
        """Get results from last check."""
        return self.last_result

    async def _run_check(self) -> Dict[str, Any]:
        """
        Internal method to run check with metadata tracking.

        Returns:
            Check results
        """
        if not self.enabled:
            logger.debug("Monitor disabled, skipping check", monitor=self.name)
            return {
                "alerts": [],
                "data": {},
                "metadata": {"status": "disabled"}
            }

        start_time = datetime.now()

        try:
            logger.debug("Running check", monitor=self.name)
            result = await self.check()

            self.last_check = start_time
            self.last_result = result

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                "Check completed",
                monitor=self.name,
                alerts=len(result.get("alerts", [])),
                duration_seconds=duration
            )

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            logger.error(
                "Check failed",
                monitor=self.name,
                error=str(e),
                duration_seconds=duration,
                exc_info=True
            )

            raise
