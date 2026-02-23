"""
Notification system for delivering heartbeat alerts.

Handles formatting and sending notifications through Slack and other channels.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, time as dt_time
from slack_sdk.web.async_client import AsyncWebClient

from ..utils.logging_config import get_logger
from ..utils.config import config
from ..adapters.slack_formatter import SlackFormatter

logger = get_logger(__name__)


class Notifier:
    """
    Manages notification delivery across multiple channels.

    Handles:
    - Notification formatting
    - Priority-based routing
    - Deduplication
    - Do-not-disturb hours
    - Multi-channel delivery (Slack primary)
    """

    def __init__(self, slack_client: Optional[AsyncWebClient] = None):
        """
        Initialize notifier.

        Args:
            slack_client: Slack web client for sending messages
        """
        self.slack_client = slack_client
        self.formatter = SlackFormatter()

        # Notification settings
        self.notification_channel = config.SLACK_NOTIFICATION_CHANNEL or None
        self.dnd_start = self._parse_time(config.NOTIFICATION_DND_START)
        self.dnd_end = self._parse_time(config.NOTIFICATION_DND_END)

        # Track sent notifications for deduplication
        self.sent_notifications: Dict[str, datetime] = {}
        self.dedup_window_minutes = 60  # Don't resend same alert within 1 hour

        logger.info(
            "Notifier initialized",
            channel=self.notification_channel,
            dnd_enabled=bool(self.dnd_start and self.dnd_end)
        )

    async def send_heartbeat_summary(
        self,
        heartbeat_results: Dict[str, Any],
        send_to: Optional[str] = None
    ) -> None:
        """
        Send heartbeat summary with all alerts.

        Args:
            heartbeat_results: Results from heartbeat orchestrator
            send_to: Optional channel/user to send to (overrides default)
        """
        alerts = heartbeat_results.get("alerts", [])
        summary = heartbeat_results.get("summary", {})

        if not alerts:
            logger.debug("No alerts to send")
            return

        # Check do-not-disturb hours
        if self._is_dnd_active():
            # Only send urgent alerts during DND
            urgent_alerts = [a for a in alerts if a.get("priority") == "urgent"]
            if not urgent_alerts:
                logger.info("Suppressing non-urgent alerts during DND hours")
                return
            alerts = urgent_alerts

        # Deduplicate alerts
        alerts = self._deduplicate_alerts(alerts)

        if not alerts:
            logger.debug("All alerts deduplicated")
            return

        # Group alerts by priority
        urgent = [a for a in alerts if a.get("priority") == "urgent"]
        normal = [a for a in alerts if a.get("priority") == "normal"]
        low = [a for a in alerts if a.get("priority") == "low"]

        # Send to Slack
        if self.slack_client:
            await self._send_slack_summary(
                urgent=urgent,
                normal=normal,
                low=low,
                summary=summary,
                send_to=send_to
            )

        logger.info(
            "Heartbeat summary sent",
            total_alerts=len(alerts),
            urgent=len(urgent),
            normal=len(normal),
            low=len(low)
        )

    async def send_alert(
        self,
        alert: Dict[str, Any],
        send_to: Optional[str] = None
    ) -> None:
        """
        Send a single alert.

        Args:
            alert: Alert dictionary
            send_to: Optional channel/user to send to
        """
        # Check if already sent recently
        alert_key = self._get_alert_key(alert)
        if self._is_duplicate(alert_key):
            logger.debug("Skipping duplicate alert", alert_key=alert_key)
            return

        # Check DND for non-urgent alerts
        if alert.get("priority") != "urgent" and self._is_dnd_active():
            logger.debug("Suppressing alert during DND hours", priority=alert.get("priority"))
            return

        # Send to Slack
        if self.slack_client:
            await self._send_slack_alert(alert, send_to=send_to)

        # Mark as sent
        self.sent_notifications[alert_key] = datetime.now()

        logger.info(
            "Alert sent",
            title=alert.get("title"),
            priority=alert.get("priority")
        )

    async def _send_slack_summary(
        self,
        urgent: List[Dict[str, Any]],
        normal: List[Dict[str, Any]],
        low: List[Dict[str, Any]],
        summary: Dict[str, Any],
        send_to: Optional[str] = None
    ) -> None:
        """Send heartbeat summary to Slack."""
        channel = send_to or self.notification_channel
        if not channel:
            logger.warning("No Slack channel configured for notifications")
            return

        # Build message blocks
        blocks = []

        # Header
        total_alerts = len(urgent) + len(normal) + len(low)
        icon = ":rotating_light:" if urgent else ":bell:"

        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{icon} Heartbeat Summary ({total_alerts} alerts)"
            }
        })

        # Summary stats
        stats_text = []
        if summary.get("successful_monitors"):
            stats_text.append(f"✅ {summary['successful_monitors']} monitors active")
        if summary.get("failed_monitors"):
            stats_text.append(f"❌ {summary['failed_monitors']} monitors failed")

        if stats_text:
            blocks.append(self.formatter.create_context_block(stats_text))

        # Urgent alerts
        if urgent:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 Urgent ({len(urgent)})*"
                }
            })

            for alert in urgent[:5]:  # Limit to 5
                blocks.append(self._format_alert_block(alert))

        # Normal alerts
        if normal:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔔 Normal ({len(normal)})*"
                }
            })

            for alert in normal[:5]:  # Limit to 5
                blocks.append(self._format_alert_block(alert))

        # Low priority (just count)
        if low:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ℹ️ Low Priority: {len(low)} items*"
                }
            })

        # Send message
        try:
            await self.slack_client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Heartbeat Summary: {total_alerts} alerts"
            )
        except Exception as e:
            logger.error("Failed to send Slack summary", error=str(e), exc_info=True)

    async def _send_slack_alert(
        self,
        alert: Dict[str, Any],
        send_to: Optional[str] = None
    ) -> None:
        """Send single alert to Slack."""
        channel = send_to or self.notification_channel
        if not channel:
            logger.warning("No Slack channel configured for notifications")
            return

        blocks = [self._format_alert_block(alert)]

        try:
            await self.slack_client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=alert.get("title", "Alert")
            )
        except Exception as e:
            logger.error("Failed to send Slack alert", error=str(e), exc_info=True)

    def _format_alert_block(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert as Slack block."""
        priority = alert.get("priority", "normal")
        source = alert.get("source", "unknown")

        # Priority icon
        icon = {
            "urgent": "🚨",
            "normal": "🔔",
            "low": "ℹ️"
        }.get(priority, "📌")

        # Format text
        text = f"{icon} *{alert.get('title', 'Alert')}*\n"
        text += f"_{source.title()}_\n\n"
        text += alert.get('message', '')

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def _get_alert_key(self, alert: Dict[str, Any]) -> str:
        """Generate unique key for alert deduplication."""
        return f"{alert.get('source')}:{alert.get('title')}"

    def _is_duplicate(self, alert_key: str) -> bool:
        """Check if alert was recently sent."""
        if alert_key not in self.sent_notifications:
            return False

        last_sent = self.sent_notifications[alert_key]
        age_minutes = (datetime.now() - last_sent).total_seconds() / 60

        return age_minutes < self.dedup_window_minutes

    def _deduplicate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate alerts."""
        deduplicated = []

        for alert in alerts:
            alert_key = self._get_alert_key(alert)
            if not self._is_duplicate(alert_key):
                deduplicated.append(alert)
                # Mark as sent
                self.sent_notifications[alert_key] = datetime.now()

        return deduplicated

    def _is_dnd_active(self) -> bool:
        """Check if currently in do-not-disturb hours."""
        if not self.dnd_start or not self.dnd_end:
            return False

        now = datetime.now().time()

        # Handle overnight DND (e.g., 22:00 - 07:00)
        if self.dnd_start > self.dnd_end:
            return now >= self.dnd_start or now <= self.dnd_end
        # Handle same-day DND (e.g., 12:00 - 13:00)
        else:
            return self.dnd_start <= now <= self.dnd_end

    def _parse_time(self, time_str: Optional[str]) -> Optional[dt_time]:
        """Parse time string (HH:MM) into time object."""
        if not time_str:
            return None

        try:
            parts = time_str.split(':')
            return dt_time(hour=int(parts[0]), minute=int(parts[1]))
        except Exception as e:
            logger.warning("Failed to parse time", time_str=time_str, error=str(e))
            return None
