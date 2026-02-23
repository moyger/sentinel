"""
Tests for the skills system.

Tests skill discovery, registry, executor, and the Task Creator skill.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from skills.skill_registry import SkillRegistry
from skills.skill_executor import SkillExecutor
from skills.skill_manager import SkillManager


class TestSkillRegistry:
    """Test skill registry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = SkillRegistry()
        assert registry is not None
        assert registry.skills_dir.exists()

    def test_skill_discovery(self):
        """Test skill discovery finds skills."""
        registry = SkillRegistry()
        count = registry.discover_skills()

        assert count >= 1, "Should find at least the task-creator skill"
        assert len(registry.skills) == count

    def test_get_task_creator_skill(self):
        """Test retrieving task-creator skill."""
        registry = SkillRegistry()
        registry.discover_skills()

        skill = registry.get_skill('task-creator')
        assert skill is not None
        assert skill.name == 'task-creator'
        assert skill.version == '1.0.0'
        assert skill.category == 'automation'
        assert 'asana' in skill.tags

    def test_skill_metadata_parsing(self):
        """Test skill metadata is parsed correctly."""
        registry = SkillRegistry()
        registry.discover_skills()

        skill = registry.get_skill('task-creator')
        assert skill.description
        assert skill.author == 'Sentinel Team'
        assert len(skill.requirements) > 0
        assert len(skill.parameters) > 0

    def test_skill_parameters(self):
        """Test skill parameters are parsed correctly."""
        registry = SkillRegistry()
        registry.discover_skills()

        skill = registry.get_skill('task-creator')

        # Check required parameter
        assert 'text' in skill.parameters
        assert skill.parameters['text']['required'] is True
        assert skill.parameters['text']['type'] == 'string'

        # Check optional parameters
        assert 'project_gid' in skill.parameters
        assert skill.parameters['project_gid']['required'] is False

    def test_list_skills(self):
        """Test listing skills."""
        registry = SkillRegistry()
        registry.discover_skills()

        skills = registry.list_skills()
        assert len(skills) >= 1
        assert any(s.name == 'task-creator' for s in skills)

    def test_search_skills(self):
        """Test searching skills."""
        registry = SkillRegistry()
        registry.discover_skills()

        # Search by name
        results = registry.search_skills('task')
        assert len(results) >= 1

        # Search by tag
        results = registry.search_skills('asana')
        assert len(results) >= 1

    def test_validate_skill(self):
        """Test skill validation."""
        registry = SkillRegistry()
        registry.discover_skills()

        is_valid, issues = registry.validate_skill('task-creator')
        assert is_valid, f"Validation failed: {issues}"
        assert len(issues) == 0

    def test_get_stats(self):
        """Test registry statistics."""
        registry = SkillRegistry()
        registry.discover_skills()

        stats = registry.get_stats()
        assert stats['total_skills'] >= 1
        assert 'automation' in stats['categories']
        assert 'task-creator' in stats['skills_by_name']


class TestSkillExecutor:
    """Test skill executor functionality."""

    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        registry = SkillRegistry()
        registry.discover_skills()

        executor = SkillExecutor(registry)
        assert executor is not None
        assert executor.default_timeout == 30

    @pytest.mark.asyncio
    async def test_execute_nonexistent_skill(self):
        """Test executing non-existent skill."""
        registry = SkillRegistry()
        registry.discover_skills()

        executor = SkillExecutor(registry)
        result = await executor.execute_skill('nonexistent', {})

        assert result.success is False
        assert 'not found' in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_skill_missing_parameters(self):
        """Test executing skill with missing required parameters."""
        registry = SkillRegistry()
        registry.discover_skills()

        executor = SkillExecutor(registry)
        result = await executor.execute_skill('task-creator', {})

        assert result.success is False
        assert 'required parameter' in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_skill_invalid_parameter_type(self):
        """Test executing skill with wrong parameter type."""
        registry = SkillRegistry()
        registry.discover_skills()

        executor = SkillExecutor(registry)
        result = await executor.execute_skill('task-creator', {'text': 123})  # Should be string

        assert result.success is False
        assert 'wrong type' in result.error.lower()

    def test_get_skill_help(self):
        """Test getting skill help text."""
        registry = SkillRegistry()
        registry.discover_skills()

        executor = SkillExecutor(registry)
        help_text = executor.get_skill_help('task-creator')

        assert help_text is not None
        assert 'Task Creator' in help_text
        assert 'Parameters' in help_text


class TestSkillManager:
    """Test skill manager functionality."""

    def test_manager_initialization(self):
        """Test manager initializes and discovers skills."""
        manager = SkillManager()
        assert manager is not None
        assert len(manager.registry.skills) >= 1

    def test_list_skills(self):
        """Test listing skills through manager."""
        manager = SkillManager()
        skills = manager.list_skills()

        assert len(skills) >= 1
        assert any(s.name == 'task-creator' for s in skills)

    def test_list_skills_by_category(self):
        """Test filtering skills by category."""
        manager = SkillManager()
        skills = manager.list_skills(category='automation')

        assert len(skills) >= 1
        assert all(s.category == 'automation' for s in skills)

    def test_search_skills(self):
        """Test searching skills through manager."""
        manager = SkillManager()
        results = manager.search_skills('task')

        assert len(results) >= 1

    def test_get_skill(self):
        """Test getting skill by name."""
        manager = SkillManager()
        skill = manager.get_skill('task-creator')

        assert skill is not None
        assert skill.name == 'task-creator'

    def test_validate_skill(self):
        """Test validating skill through manager."""
        manager = SkillManager()
        is_valid, issues = manager.validate_skill('task-creator')

        assert is_valid
        assert len(issues) == 0

    def test_get_stats(self):
        """Test getting statistics."""
        manager = SkillManager()
        stats = manager.get_stats()

        assert stats['total_skills'] >= 1
        assert len(stats['categories']) >= 1

    def test_list_categories(self):
        """Test listing categories."""
        manager = SkillManager()
        categories = manager.list_categories()

        assert len(categories) >= 1
        assert 'automation' in categories

    @pytest.mark.asyncio
    async def test_execute_skill_safe(self):
        """Test safe skill execution (never raises)."""
        manager = SkillManager()

        # This should not raise even with invalid parameters
        result = await manager.execute_skill('task-creator', {})

        assert isinstance(result.success, bool)
        assert result.success is False  # Missing required params


class TestDateParser:
    """Test date parser from task-creator skill."""

    def test_date_parser_import(self):
        """Test date parser can be imported."""
        sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / 'task-creator'))

        from date_parser import parse_due_date, extract_task_parts

        assert parse_due_date is not None
        assert extract_task_parts is not None

    def test_parse_tomorrow(self):
        """Test parsing 'tomorrow'."""
        sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / 'task-creator'))
        from date_parser import parse_due_date
        from datetime import datetime, timedelta

        result = parse_due_date("Call client tomorrow")
        expected = (datetime.now().date() + timedelta(days=1)).isoformat()

        assert result == expected

    def test_extract_task_parts(self):
        """Test extracting task components."""
        sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / 'task-creator'))
        from date_parser import extract_task_parts

        text = "Finish presentation by next Friday\n\nNeed to add slides about AI"
        result = extract_task_parts(text)

        assert result['title'] == 'Finish presentation'
        assert 'AI' in result['description']
        assert result['due_date'] is not None


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
