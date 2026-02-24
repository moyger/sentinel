"""
Memory Manager for Sentinel.

Handles distillation of daily logs into durable facts and core memory updates.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date

from .semantic_indexer import SemanticIndexer


@dataclass
class MemoryProposal:
    """Proposed update to a memory file."""
    file_path: str
    section: str
    action: str  # 'append', 'update', 'replace'
    content: str
    confidence: float  # 0-1


@dataclass
class DistillationResult:
    """Result of memory distillation."""
    date_processed: str
    facts_extracted: int
    proposals: List[MemoryProposal]
    topics_created: List[str]
    applied: bool


class MemoryManager:
    """
    Manages memory distillation and core file updates.

    Capabilities:
    - Extract facts from daily logs
    - Propose updates to core memory files
    - Create new topics automatically
    - Backup and version control
    """

    def __init__(
        self,
        memory_dir: Path,
        indexer: SemanticIndexer
    ):
        """
        Initialize memory manager.

        Args:
            memory_dir: Path to memory directory
            indexer: Semantic indexer instance
        """
        self.memory_dir = memory_dir
        self.indexer = indexer
        self.core_files = {
            "soul": memory_dir / "soul.md",
            "memory": memory_dir / "memory.md",
            "user": memory_dir / "user.md",
            "agents": memory_dir / "agents.md"
        }

    def distill_daily_log(
        self,
        log_date: Optional[date] = None,
        dry_run: bool = False
    ) -> DistillationResult:
        """
        Distill a daily log into durable facts.

        Args:
            log_date: Date to process (defaults to today)
            dry_run: If True, only show proposals without applying

        Returns:
            Distillation result
        """
        if log_date is None:
            log_date = date.today()

        # Read daily log
        daily_log_path = self.memory_dir / "daily" / f"{log_date.isoformat()}.md"

        if not daily_log_path.exists():
            print(f"⚠️  Daily log not found: {daily_log_path}")
            return DistillationResult(
                date_processed=log_date.isoformat(),
                facts_extracted=0,
                proposals=[],
                topics_created=[],
                applied=False
            )

        print(f"🧹 Memory Janitor - Processing {log_date.isoformat()}")
        print("=" * 70)
        print()

        # Read log content
        with open(daily_log_path) as f:
            log_content = f.read()

        print(f"📖 Reading daily log... ({len(log_content.splitlines())} lines)")

        # Extract facts using pattern matching
        facts = self._extract_facts(log_content)

        print(f"🧠 Extracted {len(facts)} facts\n")

        # Generate proposals
        proposals = self._generate_proposals(facts, log_content)

        print(f"📝 Generated {len(proposals)} proposals\n")

        # Show proposals
        self._show_proposals(proposals)

        # Extract topics
        topics = self._extract_topics(log_content)

        # Apply if not dry run
        applied = False
        if not dry_run:
            print("\n" + "=" * 70)
            apply = input("Apply changes? [y/N]: ").strip().lower()
            if apply == 'y':
                self._apply_proposals(proposals)
                self._create_topics(topics)
                applied = True
                print("✅ Changes applied\n")
            else:
                print("❌ Changes discarded\n")

        return DistillationResult(
            date_processed=log_date.isoformat(),
            facts_extracted=len(facts),
            proposals=proposals,
            topics_created=topics,
            applied=applied
        )

    def _extract_facts(self, log_content: str) -> List[Dict[str, Any]]:
        """
        Extract durable facts from log content.

        Uses rule-based extraction patterns.
        """
        facts = []

        # Pattern: "I prefer X"
        preference_pattern = r"(?:I|i)\s+(?:prefer|like|enjoy|want)\s+(.+?)(?:\.|$)"
        for match in re.finditer(preference_pattern, log_content, re.MULTILINE):
            facts.append({
                "type": "preference",
                "content": match.group(1).strip(),
                "source": "daily_log"
            })

        # Pattern: "Decided to X"
        decision_pattern = r"(?:Decided|decided|Decision|decision):\s*(.+?)(?:\.|$)"
        for match in re.finditer(decision_pattern, log_content, re.MULTILINE):
            facts.append({
                "type": "decision",
                "content": match.group(1).strip(),
                "source": "daily_log"
            })

        # Pattern: "Learned that X"
        learning_pattern = r"(?:Learned|learned|Lesson|lesson):\s*(.+?)(?:\.|$)"
        for match in re.finditer(learning_pattern, log_content, re.MULTILINE):
            facts.append({
                "type": "learning",
                "content": match.group(1).strip(),
                "source": "daily_log"
            })

        # Pattern: "Built/Created/Implemented X"
        achievement_pattern = r"(?:Built|Created|Implemented|Completed)\s+(.+?)(?:\.|$)"
        for match in re.finditer(achievement_pattern, log_content, re.MULTILINE):
            facts.append({
                "type": "achievement",
                "content": match.group(1).strip(),
                "source": "daily_log"
            })

        # Pattern: Headers with "Complete", "Done", "Finished"
        completion_pattern = r"#+\s*(.+?(?:Complete|Done|Finished|✅))"
        for match in re.finditer(completion_pattern, log_content, re.MULTILINE):
            facts.append({
                "type": "completion",
                "content": match.group(1).strip(),
                "source": "daily_log"
            })

        return facts

    def _generate_proposals(
        self,
        facts: List[Dict[str, Any]],
        log_content: str
    ) -> List[MemoryProposal]:
        """
        Generate update proposals from extracted facts.
        """
        proposals = []

        # Group facts by type
        preferences = [f for f in facts if f["type"] == "preference"]
        decisions = [f for f in facts if f["type"] == "decision"]
        learnings = [f for f in facts if f["type"] == "learning"]
        achievements = [f for f in facts if f["type"] == "achievement"]
        completions = [f for f in facts if f["type"] == "completion"]

        # Preferences → user.md
        if preferences:
            for pref in preferences[:3]:  # Top 3
                proposals.append(MemoryProposal(
                    file_path="memory/user.md",
                    section="Preferences",
                    action="append",
                    content=f"- {pref['content']}",
                    confidence=0.7
                ))

        # Decisions → soul.md or memory.md
        if decisions:
            for dec in decisions[:2]:  # Top 2
                proposals.append(MemoryProposal(
                    file_path="memory/soul.md",
                    section="Values & Principles",
                    action="append",
                    content=f"- {dec['content']}",
                    confidence=0.6
                ))

        # Learnings → memory.md
        if learnings:
            for learn in learnings[:3]:
                proposals.append(MemoryProposal(
                    file_path="memory/memory.md",
                    section="Lessons",
                    action="append",
                    content=f"- {learn['content']}",
                    confidence=0.8
                ))

        # Achievements → memory.md
        if achievements or completions:
            all_achievements = achievements + completions
            for ach in all_achievements[:3]:
                proposals.append(MemoryProposal(
                    file_path="memory/memory.md",
                    section="Projects",
                    action="append",
                    content=f"- {ach['content']}",
                    confidence=0.75
                ))

        return proposals

    def _extract_topics(self, log_content: str) -> List[str]:
        """
        Extract potential topics from log content.

        Looks for:
        - Project names
        - Technology names
        - Repeated concepts
        """
        topics = []

        # Pattern: Headers (# Topic Name)
        header_pattern = r"^#+\s+(.+)$"
        for match in re.finditer(header_pattern, log_content, re.MULTILINE):
            header = match.group(1).strip()
            # Convert to topic slug
            topic_slug = re.sub(r'[^\w\s-]', '', header.lower())
            topic_slug = re.sub(r'[-\s]+', '-', topic_slug)
            if topic_slug and len(topic_slug) > 3:
                topics.append(topic_slug)

        # Deduplicate
        topics = list(set(topics))

        return topics[:5]  # Top 5

    def _show_proposals(self, proposals: List[MemoryProposal]):
        """Display proposals to user."""
        print("📝 Proposed updates:")
        print("=" * 70)

        grouped = {}
        for p in proposals:
            file_name = Path(p.file_path).name
            if file_name not in grouped:
                grouped[file_name] = []
            grouped[file_name].append(p)

        for file_name, file_proposals in grouped.items():
            print(f"\n[{file_name}]")
            for p in file_proposals:
                action_symbol = {
                    "append": "+",
                    "update": "~",
                    "replace": "!"
                }.get(p.action, "?")

                print(f"  {action_symbol} [{p.section}] {p.content.strip()[:70]}")

    def _apply_proposals(self, proposals: List[MemoryProposal]):
        """Apply proposed updates to memory files."""
        for proposal in proposals:
            file_path = self.memory_dir / Path(proposal.file_path).name

            if not file_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue

            # Backup first
            backup_path = file_path.with_suffix(f".md.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            with open(file_path) as f:
                backup_content = f.read()
            with open(backup_path, 'w') as f:
                f.write(backup_content)

            # Read current content
            with open(file_path) as f:
                content = f.read()

            # Find section
            section_pattern = rf"##\s+{re.escape(proposal.section)}"
            match = re.search(section_pattern, content, re.MULTILINE)

            if not match:
                # Section doesn't exist, create it
                content += f"\n## {proposal.section}\n\n{proposal.content}\n"
            else:
                # Find next section or end of file
                next_section = re.search(r"\n##\s+", content[match.end():])
                if next_section:
                    insert_pos = match.end() + next_section.start()
                else:
                    insert_pos = len(content)

                # Insert content
                if proposal.action == "append":
                    content = content[:insert_pos] + f"\n{proposal.content}\n" + content[insert_pos:]
                elif proposal.action == "update":
                    # Replace section content
                    section_end = insert_pos
                    section_start = match.end()
                    content = content[:section_start] + f"\n{proposal.content}\n" + content[section_end:]

            # Write updated content
            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✓ Updated {file_path.name}")

    def _create_topics(self, topic_slugs: List[str]):
        """Create topic files for new topics."""
        topics_dir = self.memory_dir / "topics"
        topics_dir.mkdir(exist_ok=True)

        for slug in topic_slugs:
            topic_file = topics_dir / f"{slug}.md"

            if topic_file.exists():
                continue  # Skip existing topics

            # Create topic file
            topic_content = f"""# {slug.replace('-', ' ').title()}

## Overview
<!-- High-level overview of this topic -->

## Key Information
<!-- Important facts, context, decisions -->

## Related
<!-- Links to other topics, projects, etc. -->

## History
- {datetime.now().date().isoformat()}: Topic created
"""

            with open(topic_file, 'w') as f:
                f.write(topic_content)

            print(f"✓ Created topic: {slug}.md")


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    from datetime import date

    # Initialize
    memory_dir = Path.home() / "sentinel" / "memory"
    db_path = Path.home() / "sentinel" / "sentinel_memory.db"

    indexer = SemanticIndexer(db_path=str(db_path))
    manager = MemoryManager(memory_dir, indexer)

    # Process today's log
    result = manager.distill_daily_log(
        log_date=date(2026, 2, 23),
        dry_run=False
    )

    print("\n" + "=" * 70)
    print("DISTILLATION COMPLETE")
    print("=" * 70)
    print(f"Facts extracted: {result.facts_extracted}")
    print(f"Proposals: {len(result.proposals)}")
    print(f"Topics created: {len(result.topics_created)}")
    print(f"Applied: {result.applied}")
