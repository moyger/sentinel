"""
Slack client for Socket Mode connection.

Handles real-time communication with Slack using Socket Mode,
integrating with the memory system for persistent conversations.
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from ..memory.session_logger import SessionLogger
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class SlackClient:
    """
    Slack Socket Mode client with memory integration.

    Manages real-time Slack connections, routes messages to handlers,
    and integrates with the session logger for persistent memory.
    """

    def __init__(
        self,
        session_logger: Optional[SessionLogger] = None,
        message_handler: Optional[Callable] = None
    ):
        """
        Initialize Slack client.

        Args:
            session_logger: SessionLogger instance for memory persistence
            message_handler: Async callable to handle incoming messages
        """
        self.session_logger = session_logger or SessionLogger()
        self.message_handler = message_handler

        # Initialize Slack Bolt app
        self.app = AsyncApp(
            token=config.SLACK_BOT_TOKEN,
            signing_secret=config.SLACK_SIGNING_SECRET
        )

        # Web client for API calls
        self.client: AsyncWebClient = self.app.client

        # Socket mode handler (will be initialized in start())
        self.socket_handler: Optional[AsyncSocketModeHandler] = None

        # Connection state
        self.is_connected = False
        self.is_running = False

        # Register event handlers
        self._register_handlers()

        logger.info("Slack client initialized")

    def _register_handlers(self) -> None:
        """Register Slack event handlers."""

        # Handle direct messages
        @self.app.event("message")
        async def handle_message_events(event, say, client):
            """Handle incoming message events."""
            await self._handle_message(event, say, client)

        # Handle app mentions in channels
        @self.app.event("app_mention")
        async def handle_app_mention(event, say, client):
            """Handle @mentions of the bot."""
            await self._handle_mention(event, say, client)

        # Handle app home opened
        @self.app.event("app_home_opened")
        async def handle_app_home_opened(event, client):
            """Handle when user opens app home."""
            logger.info("App home opened", user=event.get("user"))

        logger.debug("Slack event handlers registered")

    async def _handle_message(self, event: Dict[str, Any], say: Callable, client: AsyncWebClient) -> None:
        """
        Handle incoming message events.

        Args:
            event: Slack event payload
            say: Function to send messages
            client: Slack web client
        """
        # Ignore bot messages and message changes
        if event.get("subtype") in ["bot_message", "message_changed", "message_deleted"]:
            return

        # Ignore messages from this bot
        if event.get("bot_id"):
            return

        # Extract message details
        user_id = event.get("user")
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")  # Use thread_ts if in thread, else message ts
        text = event.get("text", "").strip()

        logger.info(
            "Message received",
            user=user_id,
            channel=channel_id,
            thread=thread_ts,
            text_preview=text[:50]
        )

        # Get or create session for this thread
        session = await self.session_logger.get_or_create_session(
            adapter="slack",
            channel_id=f"{channel_id}:{thread_ts}",  # Unique per thread
            user_id=user_id
        )

        # Log user message
        await self.session_logger.log_user_message(
            content=text,
            session_id=session.id,
            metadata={
                "channel_id": channel_id,
                "thread_ts": thread_ts,
                "ts": event.get("ts"),
                "user_id": user_id
            }
        )

        # Process message with handler
        if self.message_handler:
            try:
                # Show typing indicator
                await self._send_typing_indicator(channel_id)

                # Get conversation context
                context = await self.session_logger.get_context_window(session.id)

                # Call message handler
                response = await self.message_handler(
                    message=text,
                    context=context,
                    session_id=session.id
                )

                # Send response
                if response:
                    await self._send_message(
                        channel=channel_id,
                        text=response,
                        thread_ts=thread_ts
                    )

                    # Log assistant response
                    await self.session_logger.log_assistant_message(
                        content=response,
                        session_id=session.id,
                        metadata={
                            "channel_id": channel_id,
                            "thread_ts": thread_ts
                        }
                    )

            except Exception as e:
                logger.error("Error handling message", error=str(e), exc_info=True)
                await say(
                    text="I encountered an error processing your message. Please try again.",
                    thread_ts=thread_ts
                )

    async def _handle_mention(self, event: Dict[str, Any], say: Callable, client: AsyncWebClient) -> None:
        """
        Handle app mention events.

        Args:
            event: Slack event payload
            say: Function to send messages
            client: Slack web client
        """
        # Extract mention details
        user_id = event.get("user")
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")
        text = event.get("text", "").strip()

        # Remove bot mention from text
        text = self._remove_bot_mention(text)

        logger.info(
            "App mentioned",
            user=user_id,
            channel=channel_id,
            thread=thread_ts,
            text_preview=text[:50]
        )

        # Get or create session
        session = await self.session_logger.get_or_create_session(
            adapter="slack",
            channel_id=f"{channel_id}:{thread_ts}",
            user_id=user_id
        )

        # Log user message
        await self.session_logger.log_user_message(
            content=text,
            session_id=session.id,
            metadata={
                "channel_id": channel_id,
                "thread_ts": thread_ts,
                "ts": event.get("ts"),
                "user_id": user_id,
                "mention": True
            }
        )

        # Process with handler
        if self.message_handler:
            try:
                await self._send_typing_indicator(channel_id)

                context = await self.session_logger.get_context_window(session.id)

                response = await self.message_handler(
                    message=text,
                    context=context,
                    session_id=session.id
                )

                if response:
                    await say(text=response, thread_ts=thread_ts)

                    await self.session_logger.log_assistant_message(
                        content=response,
                        session_id=session.id,
                        metadata={
                            "channel_id": channel_id,
                            "thread_ts": thread_ts
                        }
                    )

            except Exception as e:
                logger.error("Error handling mention", error=str(e), exc_info=True)
                await say(
                    text="I encountered an error processing your mention. Please try again.",
                    thread_ts=thread_ts
                )

    def _remove_bot_mention(self, text: str) -> str:
        """
        Remove bot mention from message text.

        Args:
            text: Message text

        Returns:
            Text with bot mention removed
        """
        # Remove <@BOTID> pattern
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()

    async def _send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Slack.

        Args:
            channel: Channel ID
            text: Message text
            thread_ts: Thread timestamp (for threading)
            blocks: Optional Slack blocks for rich formatting

        Returns:
            Slack API response
        """
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts,
                blocks=blocks
            )

            logger.debug("Message sent", channel=channel, thread=thread_ts)
            return response

        except SlackApiError as e:
            logger.error("Failed to send message", error=str(e), channel=channel)
            raise

    async def _send_typing_indicator(self, channel: str) -> None:
        """
        Send typing indicator to show bot is processing.

        Args:
            channel: Channel ID
        """
        try:
            # Note: Slack doesn't have a built-in typing indicator for bots
            # This is a placeholder for future implementation
            pass
        except Exception as e:
            logger.debug("Failed to send typing indicator", error=str(e))

    async def start(self) -> None:
        """Start the Slack Socket Mode connection."""
        if self.is_running:
            logger.warning("Slack client already running")
            return

        try:
            # Initialize session logger
            await self.session_logger.initialize()

            # Create socket mode handler
            self.socket_handler = AsyncSocketModeHandler(
                app=self.app,
                app_token=config.SLACK_APP_TOKEN
            )

            logger.info("Starting Slack Socket Mode connection...")

            # Start the handler (this will block)
            await self.socket_handler.start_async()

            self.is_connected = True
            self.is_running = True

            logger.info("Slack Socket Mode connection established")

        except Exception as e:
            logger.error("Failed to start Slack client", error=str(e), exc_info=True)
            self.is_connected = False
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the Slack Socket Mode connection."""
        if not self.is_running:
            logger.warning("Slack client not running")
            return

        try:
            logger.info("Stopping Slack Socket Mode connection...")

            if self.socket_handler:
                await self.socket_handler.close_async()

            await self.session_logger.close()

            self.is_connected = False
            self.is_running = False

            logger.info("Slack Socket Mode connection closed")

        except Exception as e:
            logger.error("Error stopping Slack client", error=str(e), exc_info=True)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
