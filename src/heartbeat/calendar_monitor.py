"""
Google Calendar monitor for checking upcoming meetings and events.

Uses Calendar API to fetch events and detect meetings that need preparation.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base_monitor import BaseMonitor, Alert
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class CalendarMonitor(BaseMonitor):
    """
    Monitor for Google Calendar upcoming events.

    Checks for:
    - Meetings happening today
    - Meetings happening in the next 24 hours
    - Meetings that might need preparation
    - Calendar conflicts
    """

    def __init__(self):
        """Initialize Calendar monitor."""
        super().__init__("calendar")
        self.service = None
        self.credentials = None

        # Preparation time threshold (minutes before meeting)
        self.prep_warning_minutes = config.CALENDAR_PREP_WARNING_MINUTES or 60

    async def initialize(self) -> None:
        """Initialize Calendar API connection."""
        logger.info("Initializing Calendar monitor...")

        try:
            # Get credentials (reuse Gmail token if available)
            creds = None
            token_path = config.GOOGLE_TOKEN_PATH
            credentials_path = config.GOOGLE_CREDENTIALS_PATH

            # Load saved credentials
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing Calendar credentials...")
                    creds.refresh(Request())
                else:
                    logger.info("Starting Calendar OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.credentials = creds

            # Build Calendar service
            self.service = build('calendar', 'v3', credentials=creds)

            logger.info("Calendar monitor initialized")

        except Exception as e:
            logger.error("Failed to initialize Calendar monitor", error=str(e), exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Clean up Calendar resources."""
        logger.info("Cleaning up Calendar monitor...")
        self.service = None
        self.credentials = None

    async def check(self) -> Dict[str, Any]:
        """
        Check Calendar for upcoming events.

        Returns:
            Dictionary with alerts and event data
        """
        if not self.service:
            raise RuntimeError("Calendar monitor not initialized")

        alerts = []
        events_data = []

        try:
            # Fetch events for today and next 24 hours
            now = datetime.utcnow()
            end_time = now + timedelta(hours=24)

            logger.debug("Fetching calendar events...")

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=20,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            logger.debug("Calendar events found", count=len(events))

            # Process each event
            for event in events:
                event_data = self._parse_event(event)
                events_data.append(event_data)

                # Check if event needs alerts
                event_alerts = self._check_event_priority(event_data)
                alerts.extend([alert.to_dict() for alert in event_alerts])

            # Check for conflicts
            conflicts = self._detect_conflicts(events_data)
            for conflict in conflicts:
                alerts.append(conflict.to_dict())

            logger.info(
                "Calendar check completed",
                events_count=len(events),
                alerts_count=len(alerts)
            )

            return {
                "alerts": alerts,
                "data": {
                    "events_count": len(events),
                    "events": events_data
                },
                "metadata": {
                    "time_range": {
                        "start": now.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            }

        except Exception as e:
            logger.error("Calendar check failed", error=str(e), exc_info=True)
            raise

    def _parse_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Calendar API event into structured data.

        Args:
            event: Calendar API event object

        Returns:
            Parsed event data
        """
        # Get start/end times
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        # Parse datetime
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

        # Get attendees
        attendees = event.get('attendees', [])
        attendee_emails = [a.get('email') for a in attendees]

        return {
            "id": event.get('id'),
            "summary": event.get('summary', 'No Title'),
            "description": event.get('description', ''),
            "start": start_dt,
            "end": end_dt,
            "duration_minutes": (end_dt - start_dt).total_seconds() / 60,
            "location": event.get('location', ''),
            "attendees": attendee_emails,
            "attendee_count": len(attendees),
            "html_link": event.get('htmlLink', '')
        }

    def _check_event_priority(self, event: Dict[str, Any]) -> List[Alert]:
        """
        Check if event needs alerts.

        Args:
            event: Parsed event data

        Returns:
            List of alerts for this event
        """
        alerts = []
        now = datetime.now(event['start'].tzinfo)
        time_until_event = (event['start'] - now).total_seconds() / 60

        # Alert if meeting is very soon (within prep warning time)
        if 0 < time_until_event <= self.prep_warning_minutes:
            priority = "urgent" if time_until_event <= 15 else "normal"

            alerts.append(self.create_alert(
                title=f"Meeting Soon: {event['summary']}",
                message=self._format_event_message(event, time_until_event),
                priority=priority,
                metadata={
                    "event_id": event['id'],
                    "minutes_until": int(time_until_event),
                    "attendee_count": event['attendee_count']
                }
            ))

        # Alert for meetings with many attendees
        elif event['attendee_count'] >= 5 and time_until_event <= 120:
            alerts.append(self.create_alert(
                title=f"Large Meeting: {event['summary']}",
                message=self._format_event_message(event, time_until_event),
                priority="normal",
                metadata={
                    "event_id": event['id'],
                    "attendee_count": event['attendee_count'],
                    "reason": "large_meeting"
                }
            ))

        return alerts

    def _format_event_message(self, event: Dict[str, Any], minutes_until: float) -> str:
        """
        Format event details into alert message.

        Args:
            event: Parsed event data
            minutes_until: Minutes until event starts

        Returns:
            Formatted message
        """
        lines = []

        # Time info
        if minutes_until < 60:
            lines.append(f"Starting in {int(minutes_until)} minutes")
        else:
            hours = int(minutes_until / 60)
            lines.append(f"Starting in {hours} hour{'s' if hours > 1 else ''}")

        # Time and duration
        start_time = event['start'].strftime("%I:%M %p")
        lines.append(f"Time: {start_time} ({int(event['duration_minutes'])} min)")

        # Attendees
        if event['attendee_count'] > 0:
            lines.append(f"Attendees: {event['attendee_count']}")

        # Location
        if event['location']:
            lines.append(f"Location: {event['location']}")

        # Description (first line only)
        if event['description']:
            desc_line = event['description'].split('\n')[0][:100]
            lines.append(f"Notes: {desc_line}")

        return '\n'.join(lines)

    def _detect_conflicts(self, events: List[Dict[str, Any]]) -> List[Alert]:
        """
        Detect overlapping calendar events.

        Args:
            events: List of parsed events

        Returns:
            List of conflict alerts
        """
        conflicts = []

        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                event1 = events[i]
                event2 = events[j]

                # Check for overlap
                if (event1['start'] < event2['end'] and
                    event2['start'] < event1['end']):

                    conflict_alert = self.create_alert(
                        title="Calendar Conflict Detected",
                        message=(
                            f"Overlapping meetings:\n"
                            f"1. {event1['summary']} ({event1['start'].strftime('%I:%M %p')})\n"
                            f"2. {event2['summary']} ({event2['start'].strftime('%I:%M %p')})"
                        ),
                        priority="urgent",
                        metadata={
                            "event1_id": event1['id'],
                            "event2_id": event2['id'],
                            "conflict_type": "overlap"
                        }
                    )
                    conflicts.append(conflict_alert)

        return conflicts
