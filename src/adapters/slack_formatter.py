"""
Slack message formatting utilities.

Converts between Markdown and Slack's mrkdwn format,
and provides helpers for creating Slack blocks.
"""

import re
from typing import List, Dict, Any, Optional


class SlackFormatter:
    """Formatter for Slack messages."""

    @staticmethod
    def markdown_to_slack(text: str) -> str:
        """
        Convert Markdown to Slack mrkdwn format.

        Args:
            text: Markdown formatted text

        Returns:
            Slack mrkdwn formatted text
        """
        # Bold: **text** or __text__ -> *text*
        text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
        text = re.sub(r'__(.+?)__', r'*\1*', text)

        # Italic: *text* or _text_ -> _text_
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text)

        # Code: `text` -> `text` (same)
        # Already compatible

        # Code blocks: ```text``` -> ```text``` (same)
        # Already compatible

        # Links: [text](url) -> <url|text>
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<\2|\1>', text)

        # Strikethrough: ~~text~~ -> ~text~
        text = re.sub(r'~~(.+?)~~', r'~\1~', text)

        return text

    @staticmethod
    def create_text_block(text: str) -> Dict[str, Any]:
        """
        Create a Slack text block.

        Args:
            text: Block text

        Returns:
            Slack block object
        """
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    @staticmethod
    def create_code_block(code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a Slack code block.

        Args:
            code: Code content
            language: Optional language hint

        Returns:
            Slack block object
        """
        formatted_code = f"```{language}\n{code}\n```" if language else f"```\n{code}\n```"

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": formatted_code
            }
        }

    @staticmethod
    def create_divider() -> Dict[str, str]:
        """
        Create a divider block.

        Returns:
            Slack divider block
        """
        return {"type": "divider"}

    @staticmethod
    def create_context_block(elements: List[str]) -> Dict[str, Any]:
        """
        Create a context block (gray text at bottom).

        Args:
            elements: List of text elements

        Returns:
            Slack context block
        """
        return {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": element}
                for element in elements
            ]
        }

    @staticmethod
    def create_button(text: str, action_id: str, value: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an interactive button.

        Args:
            text: Button text
            action_id: Unique action identifier
            value: Optional value to pass when clicked

        Returns:
            Slack button element
        """
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text
            },
            "action_id": action_id
        }

        if value:
            button["value"] = value

        return button

    @staticmethod
    def create_actions_block(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an actions block with buttons/selects.

        Args:
            elements: List of action elements (buttons, selects, etc.)

        Returns:
            Slack actions block
        """
        return {
            "type": "actions",
            "elements": elements
        }

    @staticmethod
    def format_error_message(error: str) -> List[Dict[str, Any]]:
        """
        Format an error message with blocks.

        Args:
            error: Error message

        Returns:
            List of Slack blocks
        """
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":warning: *Error*\n{error}"
                }
            }
        ]

    @staticmethod
    def format_success_message(message: str) -> List[Dict[str, Any]]:
        """
        Format a success message with blocks.

        Args:
            message: Success message

        Returns:
            List of Slack blocks
        """
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: {message}"
                }
            }
        ]

    @staticmethod
    def truncate_text(text: str, max_length: int = 3000) -> str:
        """
        Truncate text to Slack's length limits.

        Args:
            text: Text to truncate
            max_length: Maximum length (default 3000 for text blocks)

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[:max_length - 20] + "\n\n_[Truncated...]_"

    @staticmethod
    def split_long_message(text: str, max_length: int = 3000) -> List[str]:
        """
        Split long messages into chunks that fit Slack's limits.

        Args:
            text: Text to split
            max_length: Maximum length per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # If paragraph itself is too long, split it
                if len(paragraph) > max_length:
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence + '. '
                        else:
                            current_chunk += sentence + '. '
                else:
                    current_chunk = paragraph + '\n\n'
            else:
                current_chunk += paragraph + '\n\n'

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    @staticmethod
    def format_thinking_indicator() -> str:
        """
        Format a "thinking" indicator message.

        Returns:
            Thinking indicator text
        """
        return "_Thinking..._"

    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text

        Returns:
            List of code blocks with language and content
        """
        # Pattern to match ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                'language': language or 'plaintext',
                'code': code.strip()
            })

        return code_blocks
