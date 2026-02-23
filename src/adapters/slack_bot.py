"""
Main Slack bot application.

Integrates Slack client with Claude API for intelligent responses.
"""

import asyncio
from typing import List, Dict, Optional
from anthropic import AsyncAnthropic

from .slack_client import SlackClient
from .slack_formatter import SlackFormatter
from ..memory.session_logger import SessionLogger
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class SlackBot:
    """
    Main Slack bot with Claude integration.

    Handles incoming Slack messages, generates responses using Claude,
    and maintains conversation context through the memory system.
    """

    def __init__(self):
        """Initialize Slack bot."""
        self.session_logger = SessionLogger()
        self.slack_client = SlackClient(
            session_logger=self.session_logger,
            message_handler=self.handle_message
        )
        self.formatter = SlackFormatter()

        # Initialize Claude client
        self.claude = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

        logger.info("Slack bot initialized")

    async def handle_message(
        self,
        message: str,
        context: List[Dict[str, str]],
        session_id: str
    ) -> str:
        """
        Handle incoming message and generate response.

        Args:
            message: User message text
            context: Conversation context (previous messages)
            session_id: Session ID for this conversation

        Returns:
            Bot response text
        """
        try:
            logger.info("Processing message", session_id=session_id[:8], message_preview=message[:50])

            # Prepare system prompt
            system_prompt = self._build_system_prompt()

            # Prepare messages for Claude
            messages = context.copy()
            if not messages or messages[-1]["role"] != "user":
                messages.append({
                    "role": "user",
                    "content": message
                })

            # Call Claude API
            response = await self.claude.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                temperature=config.CLAUDE_TEMPERATURE,
                system=system_prompt,
                messages=messages
            )

            # Extract response text
            response_text = response.content[0].text

            # Format for Slack
            formatted_response = self.formatter.markdown_to_slack(response_text)

            # Truncate if too long
            if len(formatted_response) > 3000:
                chunks = self.formatter.split_long_message(formatted_response)
                formatted_response = chunks[0] + "\n\n_[Response truncated - too long]_"

            logger.info(
                "Response generated",
                session_id=session_id[:8],
                response_length=len(formatted_response),
                tokens_used=response.usage.total_tokens
            )

            return formatted_response

        except Exception as e:
            logger.error("Error generating response", error=str(e), exc_info=True)
            return "I encountered an error generating a response. Please try again."

    def _build_system_prompt(self) -> str:
        """
        Build system prompt for Claude.

        Returns:
            System prompt text
        """
        return """You are Sentinel, an AI assistant integrated with Slack.

You help users by:
- Answering questions clearly and concisely
- Maintaining context across conversations
- Being helpful, harmless, and honest

Communication style:
- Be conversational and friendly
- Use Slack markdown formatting when appropriate
- Keep responses concise (aim for 1-2 paragraphs unless more detail is requested)
- Use emojis sparingly and only when it enhances communication

You have access to conversation history and can remember previous interactions
within the current thread. Use this context to provide more relevant and
personalized responses.

If you're unsure about something, say so. If you make a mistake, acknowledge it.
"""

    async def start(self) -> None:
        """Start the Slack bot."""
        logger.info("Starting Slack bot...")

        try:
            # Initialize session logger
            await self.session_logger.initialize()

            # Start Slack client (this will block)
            await self.slack_client.start()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self.stop()
        except Exception as e:
            logger.error("Fatal error in Slack bot", error=str(e), exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the Slack bot."""
        logger.info("Stopping Slack bot...")

        try:
            await self.slack_client.stop()
            await self.session_logger.close()

            logger.info("Slack bot stopped")

        except Exception as e:
            logger.error("Error stopping Slack bot", error=str(e), exc_info=True)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.session_logger.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


async def main():
    """Main entry point for Slack bot."""
    # Configure logging
    from ..utils.logging_config import init_logging
    init_logging()

    logger.info("=" * 60)
    logger.info("SENTINEL SLACK BOT")
    logger.info("=" * 60)

    # Display configuration
    logger.info("Configuration:")
    logger.info(f"  Bot Name: {config.SLACK_BOT_NAME}")
    logger.info(f"  Claude Model: {config.CLAUDE_MODEL}")
    logger.info(f"  Database: {config.SQLITE_DB_PATH}")
    logger.info("")

    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors detected:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease check your .env file and fix these errors.")
        return

    logger.info("Configuration valid - starting bot...")
    logger.info("")

    # Create and start bot
    bot = SlackBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
    finally:
        await bot.stop()

    logger.info("Slack bot terminated")


if __name__ == "__main__":
    asyncio.run(main())
