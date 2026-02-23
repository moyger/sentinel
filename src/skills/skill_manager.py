"""
Skill manager for high-level skill operations.

Provides convenient API for listing, searching, executing, and managing skills.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

import structlog

from .skill_registry import SkillRegistry, SkillMetadata
from .skill_executor import SkillExecutor, ExecutionResult

logger = structlog.get_logger(__name__)


class SkillManager:
    """High-level skill management API."""

    def __init__(self, skills_dir: Optional[Path] = None, timeout: int = 30):
        """
        Initialize skill manager.

        Args:
            skills_dir: Path to skills directory (defaults to .claude/skills/)
            timeout: Default execution timeout in seconds
        """
        self.registry = SkillRegistry(skills_dir)
        self.executor = SkillExecutor(self.registry, timeout)

        # Discover skills on initialization
        self.refresh()

        logger.info("skill_manager_initialized",
                   total_skills=len(self.registry.skills))

    def refresh(self) -> int:
        """
        Refresh skill registry.

        Returns:
            Number of skills discovered
        """
        count = self.registry.discover_skills()
        logger.info("skills_refreshed", count=count)
        return count

    def list_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """
        List all skills.

        Args:
            category: Optional category filter

        Returns:
            List of SkillMetadata
        """
        return self.registry.list_skills(category)

    def search_skills(self, query: str) -> List[SkillMetadata]:
        """
        Search skills by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        return self.registry.search_skills(query)

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        Get skill by name.

        Args:
            name: Skill name

        Returns:
            SkillMetadata or None
        """
        return self.registry.get_skill(name)

    async def execute_skill(
        self,
        skill_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute a skill.

        Args:
            skill_name: Skill name
            parameters: Skill parameters (default: {})
            timeout: Execution timeout (uses default if not specified)

        Returns:
            ExecutionResult
        """
        params = parameters or {}
        return await self.executor.execute_skill_safe(skill_name, params, timeout)

    def get_skill_help(self, skill_name: str) -> Optional[str]:
        """
        Get help text for a skill.

        Args:
            skill_name: Skill name

        Returns:
            Help text or None
        """
        return self.executor.get_skill_help(skill_name)

    def validate_skill(self, skill_name: str) -> tuple[bool, List[str]]:
        """
        Validate a skill.

        Args:
            skill_name: Skill name

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        return self.registry.validate_skill(skill_name)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get skill statistics.

        Returns:
            Dictionary of statistics
        """
        return self.registry.get_stats()

    def list_categories(self) -> List[str]:
        """
        List all skill categories.

        Returns:
            List of category names
        """
        stats = self.get_stats()
        return sorted(stats.get('categories', {}).keys())

    def print_skill_list(self, category: Optional[str] = None):
        """
        Print formatted list of skills.

        Args:
            category: Optional category filter
        """
        skills = self.list_skills(category)

        if not skills:
            print("No skills found.")
            return

        print(f"\n{'='*70}")
        print(f"Available Skills ({len(skills)})")
        print(f"{'='*70}\n")

        current_category = None
        for skill in skills:
            # Print category header
            if skill.category != current_category:
                if current_category is not None:
                    print()
                print(f"[{skill.category.upper()}]")
                current_category = skill.category

            # Print skill info
            print(f"  {skill.name} (v{skill.version})")
            print(f"    {skill.description}")
            if skill.tags:
                print(f"    Tags: {', '.join(skill.tags)}")
            print()

    def print_skill_details(self, skill_name: str):
        """
        Print detailed information about a skill.

        Args:
            skill_name: Skill name
        """
        skill = self.get_skill(skill_name)
        if not skill:
            print(f"Skill '{skill_name}' not found.")
            return

        print(f"\n{'='*70}")
        print(f"Skill: {skill.name}")
        print(f"{'='*70}\n")

        print(f"Version:     {skill.version}")
        print(f"Author:      {skill.author}")
        print(f"Category:    {skill.category}")
        print(f"Description: {skill.description}")

        if skill.tags:
            print(f"Tags:        {', '.join(skill.tags)}")

        if skill.requirements:
            print(f"\nRequirements:")
            for req in skill.requirements:
                print(f"  - {req}")

        if skill.parameters:
            print(f"\nParameters:")
            for param_name, param_def in skill.parameters.items():
                required = "required" if param_def.get('required') else "optional"
                default = param_def.get('default')
                default_str = f" (default: {default})" if default else ""
                print(f"  {param_name} ({param_def.get('type')}, {required}){default_str}")
                print(f"    {param_def.get('description')}")

        print(f"\nLocation:    {skill.skill_dir}")

        # Validation status
        is_valid, issues = self.validate_skill(skill_name)
        print(f"\nValidation:  {'✅ VALID' if is_valid else '❌ INVALID'}")
        if issues:
            for issue in issues:
                print(f"  - {issue}")

        print()


# CLI functions for testing

async def cli_execute_skill(skill_name: str, parameters: Dict[str, Any]):
    """Execute a skill from CLI."""
    manager = SkillManager()

    print(f"\nExecuting skill: {skill_name}")
    print(f"Parameters: {parameters}\n")

    result = await manager.execute_skill(skill_name, parameters)

    print(f"{'='*70}")
    print(f"Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"{'='*70}\n")

    if result.success:
        print(f"Output:\n{result.output}")
    else:
        print(f"Error: {result.error}")

    print(f"\nExecution time: {result.execution_time:.2f}s")
    if result.timeout:
        print("⚠️  Execution timed out")

    print()


def cli_list_skills(category: Optional[str] = None):
    """List skills from CLI."""
    manager = SkillManager()
    manager.print_skill_list(category)


def cli_skill_details(skill_name: str):
    """Show skill details from CLI."""
    manager = SkillManager()
    manager.print_skill_details(skill_name)


def cli_skill_stats():
    """Show skill statistics from CLI."""
    manager = SkillManager()
    stats = manager.get_stats()

    print(f"\n{'='*70}")
    print(f"Skill Statistics")
    print(f"{'='*70}\n")

    print(f"Total Skills: {stats['total_skills']}\n")

    if stats['categories']:
        print("Skills by Category:")
        for category, count in sorted(stats['categories'].items()):
            print(f"  {category}: {count}")

    print()
