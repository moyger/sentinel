"""
Main heartbeat application.

Coordinates all components: scheduler, orchestrator, monitors,
reasoning engine, and notification delivery.
"""

import asyncio
from typing import Optional
from slack_sdk.web.async_client import AsyncWebClient

from .scheduler import HeartbeatScheduler
from .orchestrator import HeartbeatOrchestrator
from .gmail_monitor import GmailMonitor
from .calendar_monitor import CalendarMonitor
from .asana_monitor import AsanaMonitor
from .notifier import Notifier
from .reasoning_engine import ReasoningEngine

from ..memory.session_logger import SessionLogger
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class HeartbeatApp:
    """
    Main heartbeat application.

    Manages the complete proactive monitoring system:
    - Scheduled execution
    - Data source monitoring
    - Intelligent reasoning
    - Notification delivery
    """

    def __init__(self):
        """Initialize heartbeat application."""
        # Core components
        self.session_logger = SessionLogger()
        self.orchestrator = HeartbeatOrchestrator(self.session_logger)
        self.scheduler: Optional[HeartbeatScheduler] = None

        # Monitors
        self.gmail_monitor: Optional[GmailMonitor] = None
        self.calendar_monitor: Optional[CalendarMonitor] = None
        self.asana_monitor: Optional[AsanaMonitor] = None

        # Intelligence and notifications
        self.reasoning_engine = ReasoningEngine()
        self.notifier: Optional[Notifier] = None

        # Slack client for notifications
        self.slack_client: Optional[AsyncWebClient] = None

        logger.info("Heartbeat app initialized")

    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing heartbeat app...")

        # Initialize session logger
        await self.session_logger.initialize()

        # Initialize Slack client if token available
        if config.SLACK_BOT_TOKEN:
            self.slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)
            self.notifier = Notifier(slack_client=self.slack_client)
            logger.info("Slack notifications enabled")
        else:
            logger.warning("No Slack token - notifications disabled")

        # Initialize monitors based on configuration
        if config.GOOGLE_CREDENTIALS_PATH:
            try:
                self.gmail_monitor = GmailMonitor()
                await self.gmail_monitor.initialize()
                self.orchestrator.register_monitor("gmail", self.gmail_monitor)
                logger.info("Gmail monitor enabled")
            except Exception as e:
                logger.warning("Failed to initialize Gmail monitor", error=str(e))

            try:
                self.calendar_monitor = CalendarMonitor()
                await self.calendar_monitor.initialize()
                self.orchestrator.register_monitor("calendar", self.calendar_monitor)
                logger.info("Calendar monitor enabled")
            except Exception as e:
                logger.warning("Failed to initialize Calendar monitor", error=str(e))
        else:
            logger.warning("No Google credentials - Gmail/Calendar disabled")

        if config.ASANA_ACCESS_TOKEN:
            try:
                self.asana_monitor = AsanaMonitor()
                await self.asana_monitor.initialize()
                self.orchestrator.register_monitor("asana", self.asana_monitor)
                logger.info("Asana monitor enabled")
            except Exception as e:
                logger.warning("Failed to initialize Asana monitor", error=str(e))
        else:
            logger.warning("No Asana token - Asana monitor disabled")

        # Create scheduler
        self.scheduler = HeartbeatScheduler(self._on_heartbeat)

        logger.info("Heartbeat app initialization complete")

    async def start(self) -> None:
        """Start the heartbeat application."""
        logger.info("=" * 60)
        logger.info("SENTINEL HEARTBEAT SYSTEM")
        logger.info("=" * 60)

        # Display configuration
        status = self.orchestrator.get_status()
        logger.info("Active monitors", monitors=status['registered_monitors'])
        logger.info("Heartbeat interval", minutes=config.HEARTBEAT_INTERVAL_MINUTES)

        if self.notifier:
            logger.info("Notifications enabled", channel=config.SLACK_NOTIFICATION_CHANNEL)
        else:
            logger.info("Notifications disabled")

        logger.info("")

        # Start scheduler
        if self.scheduler:
            await self.scheduler.start()

            # Keep running
            try:
                while self.scheduler.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                await self.stop()

    async def stop(self) -> None:
        """Stop the heartbeat application."""
        logger.info("Stopping heartbeat app...")

        # Stop scheduler
        if self.scheduler:
            await self.scheduler.stop()

        # Cleanup monitors
        if self.gmail_monitor:
            await self.gmail_monitor.cleanup()
        if self.calendar_monitor:
            await self.calendar_monitor.cleanup()
        if self.asana_monitor:
            await self.asana_monitor.cleanup()

        # Close session logger
        await self.session_logger.close()

        logger.info("Heartbeat app stopped")

    async def _on_heartbeat(self) -> None:
        """
        Callback executed on each heartbeat cycle.

        This is the main orchestration logic that:
        1. Runs all monitors
        2. Analyzes results with reasoning engine
        3. Sends notifications
        """
        try:
            # Execute heartbeat cycle
            results = await self.orchestrator.execute_heartbeat()

            # Analyze with reasoning engine if we have alerts
            if results.get("alerts"):
                logger.info("Running reasoning engine...")
                analysis = await self.reasoning_engine.analyze_heartbeat(results)

                # Add analysis to results
                if analysis.get("has_insights"):
                    results["analysis"] = analysis.get("analysis")

            # Send notifications
            if self.notifier and results.get("alerts"):
                await self.notifier.send_heartbeat_summary(results)

            # Log to memory system
            await self._log_heartbeat_to_memory(results)

            logger.info("Heartbeat cycle completed successfully")

        except Exception as e:
            logger.error("Heartbeat callback failed", error=str(e), exc_info=True)

    async def _log_heartbeat_to_memory(self, results: Dict) -> None:
        """
        Log heartbeat results to memory system.

        Args:
            results: Heartbeat execution results
        """
        try:
            # Create a memory entry for significant heartbeats
            alerts = results.get("alerts", [])
            if not alerts:
                return

            summary = results.get("summary", {})
            analysis = results.get("analysis", "")

            # Format heartbeat summary
            memory_content = f"Heartbeat scan completed:\n"
            memory_content += f"- Alerts: {len(alerts)}\n"
            memory_content += f"- Urgent: {summary.get('alerts_by_priority', {}).get('urgent', 0)}\n"

            if analysis:
                memory_content += f"\nAnalysis:\n{analysis[:300]}..."

            # Log to session (using a special heartbeat session)
            # This creates a record in the database
            session = await self.session_logger.get_or_create_session(
                adapter="heartbeat",
                channel_id="system",
                user_id="sentinel"
            )

            # Log as system message
            await self.session_logger.log_assistant_message(
                message=memory_content,
                session_id=session.id
            )

        except Exception as e:
            logger.warning("Failed to log heartbeat to memory", error=str(e))


async def main():
    """Main entry point for heartbeat app."""
    from ..utils.logging_config import init_logging

    # Initialize logging
    init_logging()

    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors detected:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease check your .env file")
        return

    # Create and start app
    app = HeartbeatApp()

    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
    finally:
        await app.stop()

    logger.info("Heartbeat system terminated")


if __name__ == "__main__":
    asyncio.run(main())
