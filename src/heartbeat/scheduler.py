"""
Heartbeat scheduler for running monitoring tasks at regular intervals.

Uses APScheduler for reliable background task execution.
"""

import asyncio
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class HeartbeatScheduler:
    """
    Manages scheduled execution of heartbeat monitoring tasks.

    The scheduler runs at configurable intervals (default 30 minutes)
    and triggers the heartbeat orchestrator to check all data sources.
    """

    def __init__(self, heartbeat_callback: Callable):
        """
        Initialize heartbeat scheduler.

        Args:
            heartbeat_callback: Async function to call on each heartbeat
        """
        self.callback = heartbeat_callback
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.interval_minutes = config.HEARTBEAT_INTERVAL_MINUTES
        self.is_running = False

        logger.info(
            "Heartbeat scheduler initialized",
            interval_minutes=self.interval_minutes
        )

    async def start(self) -> None:
        """Start the heartbeat scheduler."""
        if self.is_running:
            logger.warning("Heartbeat scheduler already running")
            return

        logger.info("Starting heartbeat scheduler...")

        # Create scheduler
        self.scheduler = AsyncIOScheduler()

        # Add heartbeat job
        self.scheduler.add_job(
            self._execute_heartbeat,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="heartbeat",
            name="Heartbeat Monitor",
            replace_existing=True,
            max_instances=1  # Prevent overlapping executions
        )

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info(
            "Heartbeat scheduler started",
            next_run=self.scheduler.get_jobs()[0].next_run_time
        )

        # Run first heartbeat immediately
        await self._execute_heartbeat()

    async def stop(self) -> None:
        """Stop the heartbeat scheduler."""
        if not self.is_running:
            logger.warning("Heartbeat scheduler not running")
            return

        logger.info("Stopping heartbeat scheduler...")

        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None

        self.is_running = False
        logger.info("Heartbeat scheduler stopped")

    async def _execute_heartbeat(self) -> None:
        """
        Execute a single heartbeat cycle.

        This method is called by the scheduler at regular intervals.
        """
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info("HEARTBEAT CYCLE STARTED")
        logger.info("=" * 60)
        logger.info("Timestamp", timestamp=start_time.isoformat())

        try:
            # Call the heartbeat callback
            await self.callback()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                "Heartbeat cycle completed",
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            logger.error(
                "Heartbeat cycle failed",
                error=str(e),
                duration_seconds=duration,
                exc_info=True
            )

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get the next scheduled run time.

        Returns:
            Next run time, or None if not running
        """
        if not self.scheduler or not self.is_running:
            return None

        jobs = self.scheduler.get_jobs()
        if jobs:
            return jobs[0].next_run_time

        return None

    def trigger_now(self) -> None:
        """Trigger an immediate heartbeat (in addition to scheduled runs)."""
        if not self.scheduler or not self.is_running:
            logger.warning("Cannot trigger heartbeat - scheduler not running")
            return

        logger.info("Manually triggering heartbeat...")
        self.scheduler.modify_job("heartbeat", next_run_time=datetime.now())
