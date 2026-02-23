"""
Heartbeat orchestrator that coordinates all monitoring tasks.

Manages the execution order and aggregation of results from all
data source monitors (Gmail, Calendar, Asana, Slack).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.logging_config import get_logger
from ..utils.config import config
from ..memory.session_logger import SessionLogger

logger = get_logger(__name__)


class HeartbeatOrchestrator:
    """
    Orchestrates heartbeat monitoring across all data sources.

    Coordinates Gmail, Calendar, Asana, and Slack monitoring,
    aggregates findings, and triggers appropriate notifications.
    """

    def __init__(self, session_logger: SessionLogger):
        """
        Initialize heartbeat orchestrator.

        Args:
            session_logger: Session logger for recording heartbeat activity
        """
        self.session_logger = session_logger
        self.monitors: Dict[str, Any] = {}
        self.last_run: Optional[datetime] = None

        logger.info("Heartbeat orchestrator initialized")

    def register_monitor(self, name: str, monitor: Any) -> None:
        """
        Register a data source monitor.

        Args:
            name: Monitor name (e.g., "gmail", "calendar")
            monitor: Monitor instance with async check() method
        """
        self.monitors[name] = monitor
        logger.info("Monitor registered", monitor=name)

    async def execute_heartbeat(self) -> Dict[str, Any]:
        """
        Execute a complete heartbeat cycle.

        Runs all registered monitors, aggregates results,
        and prepares notifications.

        Returns:
            Dictionary with heartbeat results
        """
        start_time = datetime.now()
        results = {
            "timestamp": start_time.isoformat(),
            "monitors": {},
            "alerts": [],
            "summary": {}
        }

        logger.info("Executing heartbeat cycle...")

        # Run all monitors
        for name, monitor in self.monitors.items():
            try:
                logger.info("Running monitor", monitor=name)
                monitor_result = await monitor.check()

                results["monitors"][name] = {
                    "status": "success",
                    "data": monitor_result
                }

                # Extract alerts from monitor result
                if "alerts" in monitor_result:
                    for alert in monitor_result["alerts"]:
                        alert["source"] = name
                        results["alerts"].append(alert)

                logger.info(
                    "Monitor completed",
                    monitor=name,
                    alerts=len(monitor_result.get("alerts", []))
                )

            except Exception as e:
                logger.error(
                    "Monitor failed",
                    monitor=name,
                    error=str(e),
                    exc_info=True
                )

                results["monitors"][name] = {
                    "status": "error",
                    "error": str(e)
                }

        # Generate summary
        results["summary"] = self._generate_summary(results)

        # Update last run time
        self.last_run = start_time

        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration

        logger.info(
            "Heartbeat cycle completed",
            total_alerts=len(results["alerts"]),
            duration_seconds=duration
        )

        return results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary of heartbeat results.

        Args:
            results: Raw heartbeat results

        Returns:
            Summary dictionary
        """
        summary = {
            "total_monitors": len(self.monitors),
            "successful_monitors": 0,
            "failed_monitors": 0,
            "total_alerts": len(results["alerts"]),
            "alerts_by_priority": {
                "urgent": 0,
                "normal": 0,
                "low": 0
            },
            "alerts_by_source": {}
        }

        # Count monitor statuses
        for monitor_name, monitor_result in results["monitors"].items():
            if monitor_result["status"] == "success":
                summary["successful_monitors"] += 1
            else:
                summary["failed_monitors"] += 1

        # Analyze alerts
        for alert in results["alerts"]:
            # Count by priority
            priority = alert.get("priority", "normal")
            if priority in summary["alerts_by_priority"]:
                summary["alerts_by_priority"][priority] += 1

            # Count by source
            source = alert.get("source", "unknown")
            summary["alerts_by_source"][source] = \
                summary["alerts_by_source"].get(source, 0) + 1

        return summary

    def get_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status.

        Returns:
            Status dictionary
        """
        return {
            "registered_monitors": list(self.monitors.keys()),
            "monitor_count": len(self.monitors),
            "last_run": self.last_run.isoformat() if self.last_run else None
        }
