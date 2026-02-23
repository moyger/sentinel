"""
Markdown file management for Sentinel memory system.

Provides utilities for reading, parsing, updating, and syncing Markdown files
with the SQLite database.
"""

from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import re

from ..utils.config import config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MarkdownManager:
    """Manager for core Markdown memory files."""

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Initialize Markdown manager.

        Args:
            memory_dir: Path to memory directory (defaults to config.MEMORY_DIR)
        """
        self.memory_dir = memory_dir or config.MEMORY_DIR
        self.soul_path = self.memory_dir / "soul.md"
        self.user_path = self.memory_dir / "user.md"
        self.memory_path = self.memory_dir / "memory.md"
        self.agents_path = self.memory_dir / "agents.md"
        self.daily_dir = self.memory_dir / "daily"
        self.topics_dir = self.memory_dir / "topics"

        # Ensure directories exist
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.topics_dir.mkdir(parents=True, exist_ok=True)

    # ========== Core File Operations ==========

    def read_file(self, file_path: Path) -> str:
        """
        Read a Markdown file.

        Args:
            file_path: Path to file

        Returns:
            File contents as string
        """
        if not file_path.exists():
            logger.warning("Markdown file not found", path=str(file_path))
            return ""

        return file_path.read_text(encoding='utf-8')

    def write_file(self, file_path: Path, content: str) -> None:
        """
        Write content to a Markdown file.

        Args:
            file_path: Path to file
            content: Content to write
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        logger.debug("Markdown file written", path=str(file_path))

    def update_timestamp(self, content: str) -> str:
        """
        Update the "Last updated" timestamp in Markdown content.

        Args:
            content: Markdown content

        Returns:
            Updated content with new timestamp
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Replace existing timestamp
        updated = re.sub(
            r'\*Last updated:.*?\*',
            f'*Last updated: {today}*',
            content,
            flags=re.IGNORECASE
        )

        # If no timestamp found, add one at the end
        if updated == content:
            if not content.endswith('\n'):
                content += '\n'
            updated = content + f'\n---\n\n*Last updated: {today}*\n'

        return updated

    # ========== Soul.md Operations ==========

    def read_soul(self) -> str:
        """Read soul.md file."""
        return self.read_file(self.soul_path)

    def update_soul(self, section: str, content: str) -> None:
        """
        Update a section in soul.md.

        Args:
            section: Section name (e.g., "Core Values", "Working Style")
            content: New content for the section
        """
        current = self.read_soul()

        # Find section and update
        pattern = rf'(## {re.escape(section)}.*?)(?=\n## |\Z)'
        replacement = f'## {section}\n\n{content}\n'

        updated = re.sub(pattern, replacement, current, flags=re.DOTALL)

        # If section not found, append it
        if updated == current:
            updated += f'\n\n## {section}\n\n{content}\n'

        updated = self.update_timestamp(updated)
        self.write_file(self.soul_path, updated)
        logger.info("Soul.md updated", section=section)

    # ========== User.md Operations ==========

    def read_user(self) -> str:
        """Read user.md file."""
        return self.read_file(self.user_path)

    def update_user_preference(self, section: str, key: str, value: str) -> None:
        """
        Update a specific preference in user.md.

        Args:
            section: Section name (e.g., "Communication Preferences")
            key: Preference key
            value: New value
        """
        current = self.read_user()

        # Find the section
        section_pattern = rf'(## {re.escape(section)}.*?)(?=\n## |\Z)'
        section_match = re.search(section_pattern, current, flags=re.DOTALL)

        if section_match:
            section_content = section_match.group(1)

            # Update the key-value pair
            key_pattern = rf'(\*\*{re.escape(key)}:\*\*)(.*?)(?=\n|$)'
            if re.search(key_pattern, section_content):
                new_section = re.sub(key_pattern, rf'\1 {value}', section_content)
                updated = current.replace(section_content, new_section)
            else:
                # Add new key
                new_section = section_content.rstrip() + f'\n- **{key}:** {value}\n'
                updated = current.replace(section_content, new_section)
        else:
            # Add new section
            updated = current + f'\n\n## {section}\n\n- **{key}:** {value}\n'

        updated = self.update_timestamp(updated)
        self.write_file(self.user_path, updated)
        logger.info("User.md updated", section=section, key=key)

    # ========== Memory.md Operations ==========

    def read_memory(self) -> str:
        """Read memory.md file."""
        return self.read_file(self.memory_path)

    def add_decision(
        self,
        title: str,
        context: str,
        decision: str,
        rationale: str,
        alternatives: Optional[str] = None,
        impact: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> None:
        """
        Add a new decision to memory.md.

        Args:
            title: Decision title
            context: Why this decision was needed
            decision: What was decided
            rationale: Why this approach was chosen
            alternatives: What other options were evaluated
            impact: Expected or actual outcomes
            tags: Related tags
        """
        current = self.read_memory()
        date = datetime.now().strftime("%Y-%m-%d")

        # Build decision entry
        entry = f"\n#### {date} - {title}\n"
        entry += f"- **Context:** {context}\n"
        entry += f"- **Decision:** {decision}\n"
        entry += f"- **Rationale:** {rationale}\n"

        if alternatives:
            entry += f"- **Alternatives Considered:** {alternatives}\n"

        if impact:
            entry += f"- **Impact:** {impact}\n"

        entry += "- **Status:** Active\n"

        if tags:
            entry += f"- **Related:** {' '.join([f'#{tag}' for tag in tags])}\n"

        entry += "\n"

        # Find "Active Decisions" section and add entry
        active_pattern = r'(## Active Decisions.*?)((?=\n## )|(?=\n---)|(?=\Z))'
        match = re.search(active_pattern, current, flags=re.DOTALL)

        if match:
            section_start = match.group(1)
            # Add after section header
            updated = current.replace(
                section_start,
                section_start + "\n" + entry
            )
        else:
            # Create Active Decisions section
            updated = current + f'\n\n## Active Decisions\n{entry}'

        updated = self.update_timestamp(updated)
        self.write_file(self.memory_path, updated)
        logger.info("Decision added to memory.md", title=title)

    def add_lesson(self, category: str, topic: str, lesson: str) -> None:
        """
        Add a lesson learned to memory.md.

        Args:
            category: Lesson category (e.g., "Technical Lessons")
            topic: Lesson topic
            lesson: The lesson learned
        """
        current = self.read_memory()

        entry = f"\n1. **{topic}:** {lesson}\n"

        # Find the category section
        pattern = rf'(#### {re.escape(category)}.*?)(?=\n#### |(?=\n## )|(?=\n---)|(?=\Z))'
        match = re.search(pattern, current, flags=re.DOTALL)

        if match:
            section = match.group(1)
            updated = current.replace(section, section + entry)
        else:
            # Add new category under Lessons Learned
            lessons_pattern = r'(### Lessons Learned.*?)(?=\n## |(?=\n---)|(?=\Z))'
            lessons_match = re.search(lessons_pattern, current, flags=re.DOTALL)

            if lessons_match:
                section = lessons_match.group(1)
                new_section = section + f'\n\n#### {category}\n{entry}'
                updated = current.replace(section, new_section)
            else:
                updated = current + f'\n\n### Lessons Learned\n\n#### {category}\n{entry}'

        updated = self.update_timestamp(updated)
        self.write_file(self.memory_path, updated)
        logger.info("Lesson added to memory.md", category=category, topic=topic)

    # ========== Agents.md Operations ==========

    def read_agents(self) -> str:
        """Read agents.md file."""
        return self.read_file(self.agents_path)

    def update_agent_boundary(self, persona: str, boundary_type: str, items: list[str]) -> None:
        """
        Update agent boundaries in agents.md.

        Args:
            persona: Persona name (e.g., "Sentinel (Default)")
            boundary_type: "DO" or "DON'T"
            items: List of boundary items
        """
        current = self.read_agents()

        # Find persona section
        persona_pattern = rf'(### (?:Primary: |Specialist Persona: ){re.escape(persona)}.*?)(?=\n### |(?=\n## )|(?=\Z))'
        persona_match = re.search(persona_pattern, current, flags=re.DOTALL)

        if persona_match:
            persona_section = persona_match.group(1)

            # Update boundaries
            boundary_pattern = rf'(\*\*Boundaries:\*\*.*?)(?=\n\*\*|(?=\n---|)|(?=\n## )|(?=\Z))'
            boundary_match = re.search(boundary_pattern, persona_section, flags=re.DOTALL)

            if boundary_match:
                # Rebuild boundaries
                new_boundaries = "**Boundaries:**\n"
                for item in items:
                    new_boundaries += f"- {boundary_type}: {item}\n"

                updated_persona = re.sub(boundary_pattern, new_boundaries, persona_section)
                updated = current.replace(persona_section, updated_persona)
            else:
                updated = current
        else:
            updated = current

        updated = self.update_timestamp(updated)
        self.write_file(self.agents_path, updated)
        logger.info("Agent boundaries updated", persona=persona, type=boundary_type)

    # ========== Daily Log Operations ==========

    def get_daily_log_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get path for daily log file.

        Args:
            date: Date for log (defaults to today)

        Returns:
            Path to daily log file
        """
        if date is None:
            date = datetime.now()

        filename = f"{date.strftime('%Y-%m-%d')}.md"
        return self.daily_dir / filename

    def create_daily_log(self, date: Optional[datetime] = None) -> Path:
        """
        Create a new daily log file.

        Args:
            date: Date for log (defaults to today)

        Returns:
            Path to created file
        """
        if date is None:
            date = datetime.now()

        log_path = self.get_daily_log_path(date)

        if log_path.exists():
            logger.debug("Daily log already exists", path=str(log_path))
            return log_path

        # Create daily log template
        content = f"""# Daily Log - {date.strftime('%B %d, %Y')}

## Sessions

<!-- Conversation sessions for this day -->

## Key Events

<!-- Important events, decisions, or insights -->

-

## Alerts Sent

<!-- Proactive notifications sent -->

-

## Tasks Completed

<!-- Tasks completed today -->

-

## Notes

<!-- Additional notes or observations -->



---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        self.write_file(log_path, content)
        logger.info("Daily log created", date=date.strftime('%Y-%m-%d'))
        return log_path

    def append_to_daily_log(self, content: str, section: str = "Sessions", date: Optional[datetime] = None) -> None:
        """
        Append content to a daily log.

        Args:
            content: Content to append
            section: Section to append to
            date: Date for log (defaults to today)
        """
        log_path = self.get_daily_log_path(date)

        if not log_path.exists():
            log_path = self.create_daily_log(date)

        current = self.read_file(log_path)

        # Find section and append
        pattern = rf'(## {re.escape(section)}.*?)(?=\n## |(?=\n---)|(?=\Z))'
        match = re.search(pattern, current, flags=re.DOTALL)

        if match:
            section_content = match.group(1)
            new_section = section_content.rstrip() + f'\n\n{content}\n'
            updated = current.replace(section_content, new_section)
        else:
            updated = current + f'\n\n## {section}\n\n{content}\n'

        self.write_file(log_path, updated)
        logger.debug("Daily log updated", section=section, date=date.strftime('%Y-%m-%d') if date else 'today')

    # ========== Topic Operations ==========

    def create_topic_file(self, topic_id: str, topic_name: str, description: Optional[str] = None) -> Path:
        """
        Create a new topic Markdown file.

        Args:
            topic_id: Topic ID (slug)
            topic_name: Human-readable topic name
            description: Optional topic description

        Returns:
            Path to created file
        """
        filename = f"{topic_id}.md"
        topic_path = self.topics_dir / filename

        if topic_path.exists():
            logger.debug("Topic file already exists", topic=topic_id)
            return topic_path

        content = f"""# {topic_name}

{description or ''}

## Overview

<!-- High-level overview of this topic -->

## Key Information

<!-- Important facts, context, or references -->

-

## Related Memories

<!-- This section is auto-populated from the database -->

## Notes

<!-- Additional notes or observations -->



---

*Created: {datetime.now().strftime('%Y-%m-%d')}*
*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""

        self.write_file(topic_path, content)
        logger.info("Topic file created", topic=topic_id, path=str(topic_path))
        return topic_path

    def get_topic_path(self, topic_id: str) -> Path:
        """
        Get path for topic file.

        Args:
            topic_id: Topic ID

        Returns:
            Path to topic file
        """
        return self.topics_dir / f"{topic_id}.md"

    # ========== Utility Methods ==========

    def extract_section(self, content: str, section: str) -> Optional[str]:
        """
        Extract a specific section from Markdown content.

        Args:
            content: Full Markdown content
            section: Section heading to extract

        Returns:
            Section content or None if not found
        """
        pattern = rf'## {re.escape(section)}(.*?)(?=\n## |(?=\n---)|(?=\Z))'
        match = re.search(pattern, content, flags=re.DOTALL)

        if match:
            return match.group(1).strip()

        return None

    def list_daily_logs(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> list[Path]:
        """
        List daily log files within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of daily log paths
        """
        logs = sorted(self.daily_dir.glob("*.md"))

        if start_date or end_date:
            filtered = []
            for log in logs:
                # Extract date from filename
                try:
                    log_date = datetime.strptime(log.stem, "%Y-%m-%d")
                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue
                    filtered.append(log)
                except ValueError:
                    continue
            return filtered

        return logs
