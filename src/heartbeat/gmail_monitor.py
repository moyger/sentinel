"""
Gmail monitor for checking unread and priority emails.

Uses Gmail API to fetch unread emails and identify urgent/important messages.
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

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailMonitor(BaseMonitor):
    """
    Monitor for Gmail unread messages and priority emails.

    Checks for:
    - Unread emails
    - Emails from important senders
    - Emails with urgent keywords in subject
    """

    def __init__(self):
        """Initialize Gmail monitor."""
        super().__init__("gmail")
        self.service = None
        self.credentials = None
        self.user_email = None

        # Priority detection configuration
        self.urgent_keywords = [
            "urgent", "asap", "important", "critical", "deadline",
            "emergency", "immediate", "action required", "time-sensitive"
        ]
        self.important_senders = config.GMAIL_IMPORTANT_SENDERS or []

    async def initialize(self) -> None:
        """Initialize Gmail API connection."""
        logger.info("Initializing Gmail monitor...")

        try:
            # Get credentials
            creds = None
            token_path = config.GOOGLE_TOKEN_PATH
            credentials_path = config.GOOGLE_CREDENTIALS_PATH

            # Load saved credentials if they exist
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing Gmail credentials...")
                    creds.refresh(Request())
                else:
                    logger.info("Starting Gmail OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.credentials = creds

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)

            # Get user email
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')

            logger.info(
                "Gmail monitor initialized",
                user_email=self.user_email
            )

        except Exception as e:
            logger.error("Failed to initialize Gmail monitor", error=str(e), exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Clean up Gmail resources."""
        logger.info("Cleaning up Gmail monitor...")
        self.service = None
        self.credentials = None

    async def check(self) -> Dict[str, Any]:
        """
        Check Gmail for unread and priority emails.

        Returns:
            Dictionary with alerts and email data
        """
        if not self.service:
            raise RuntimeError("Gmail monitor not initialized")

        alerts = []
        emails_data = []

        try:
            # Fetch unread messages
            logger.debug("Fetching unread emails...")

            results = self.service.users().messages().list(
                userId='me',
                labelIds=['UNREAD'],
                maxResults=50  # Check last 50 unread
            ).execute()

            messages = results.get('messages', [])

            logger.debug("Unread emails found", count=len(messages))

            # Process each message
            for msg in messages:
                try:
                    # Get full message details
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_data = self._parse_email(message)
                    emails_data.append(email_data)

                    # Check if this is a priority email
                    alert = self._check_priority(email_data)
                    if alert:
                        alerts.append(alert.to_dict())

                except Exception as e:
                    logger.warning(
                        "Failed to process email",
                        email_id=msg['id'],
                        error=str(e)
                    )
                    continue

            # Create summary alert if many unread emails
            if len(messages) >= 10:
                summary_alert = self.create_alert(
                    title=f"{len(messages)} Unread Emails",
                    message=f"You have {len(messages)} unread emails in your inbox.",
                    priority="normal",
                    metadata={"unread_count": len(messages)}
                )
                alerts.append(summary_alert.to_dict())

            logger.info(
                "Gmail check completed",
                unread_count=len(messages),
                priority_alerts=len(alerts)
            )

            return {
                "alerts": alerts,
                "data": {
                    "unread_count": len(messages),
                    "emails": emails_data[:10]  # Return top 10
                },
                "metadata": {
                    "user_email": self.user_email,
                    "total_processed": len(messages)
                }
            }

        except Exception as e:
            logger.error("Gmail check failed", error=str(e), exc_info=True)
            raise

    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail API message into structured data.

        Args:
            message: Gmail API message object

        Returns:
            Parsed email data
        """
        headers = message.get('payload', {}).get('headers', [])

        # Extract key headers
        subject = ""
        sender = ""
        date = ""

        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')

            if name == 'subject':
                subject = value
            elif name == 'from':
                sender = value
            elif name == 'date':
                date = value

        # Get snippet (preview text)
        snippet = message.get('snippet', '')

        return {
            "id": message.get('id'),
            "thread_id": message.get('threadId'),
            "subject": subject,
            "sender": sender,
            "date": date,
            "snippet": snippet
        }

    def _check_priority(self, email: Dict[str, Any]) -> Optional[Alert]:
        """
        Check if email is high priority.

        Args:
            email: Parsed email data

        Returns:
            Alert if priority, None otherwise
        """
        subject = email.get('subject', '').lower()
        sender = email.get('sender', '').lower()

        # Check for urgent keywords in subject
        for keyword in self.urgent_keywords:
            if keyword in subject:
                return self.create_alert(
                    title=f"Urgent Email: {email['subject'][:50]}",
                    message=f"From: {email['sender']}\n\n{email['snippet'][:200]}...",
                    priority="urgent",
                    metadata={
                        "email_id": email['id'],
                        "sender": email['sender'],
                        "detected_keyword": keyword
                    }
                )

        # Check for important senders
        for important_sender in self.important_senders:
            if important_sender.lower() in sender:
                return self.create_alert(
                    title=f"Email from {email['sender']}",
                    message=f"Subject: {email['subject']}\n\n{email['snippet'][:200]}...",
                    priority="normal",
                    metadata={
                        "email_id": email['id'],
                        "sender": email['sender'],
                        "reason": "important_sender"
                    }
                )

        return None
