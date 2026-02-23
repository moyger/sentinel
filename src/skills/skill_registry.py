"""
Skill registry for discovering and managing skills.

Scans .claude/skills/ directory, parses SKILL.md files, and builds a registry of available skills.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SkillMetadata:
    """Metadata for a skill parsed from SKILL.md."""

    name: str
    version: str
    author: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    parameters: Dict[str, dict] = field(default_factory=dict)
    skill_dir: Path = None
    skill_file: Path = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SkillRegistry:
    """Registry for discovering and managing skills."""

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize skill registry.

        Args:
            skills_dir: Path to skills directory (defaults to .claude/skills/)
        """
        if skills_dir is None:
            # Default to .claude/skills/ in project root
            project_root = Path(__file__).parent.parent.parent
            skills_dir = project_root / ".claude" / "skills"

        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, SkillMetadata] = {}

        logger.info("skill_registry_initialized", skills_dir=str(self.skills_dir))

    def discover_skills(self) -> int:
        """
        Discover all skills in the skills directory.

        Returns:
            Number of skills discovered
        """
        logger.info("discovering_skills", skills_dir=str(self.skills_dir))

        if not self.skills_dir.exists():
            logger.warning("skills_directory_not_found", path=str(self.skills_dir))
            return 0

        discovered_count = 0

        # Scan for skill directories
        for item in self.skills_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip template and hidden directories
            if item.name.startswith('.') or item.name in ['README.md', 'SKILL_TEMPLATE.md']:
                continue

            # Look for SKILL.md file
            skill_file = item / "SKILL.md"
            if not skill_file.exists():
                logger.warning("skill_missing_metadata", skill_dir=item.name)
                continue

            # Parse skill metadata
            try:
                metadata = self._parse_skill_metadata(skill_file, item)
                self.skills[metadata.name] = metadata
                discovered_count += 1
                logger.info("skill_discovered",
                           skill=metadata.name,
                           version=metadata.version,
                           category=metadata.category)
            except Exception as e:
                logger.error("skill_parse_failed",
                           skill_dir=item.name,
                           error=str(e))

        logger.info("skill_discovery_complete",
                   total_skills=discovered_count)

        return discovered_count

    def _parse_skill_metadata(self, skill_file: Path, skill_dir: Path) -> SkillMetadata:
        """
        Parse SKILL.md file to extract metadata.

        Args:
            skill_file: Path to SKILL.md file
            skill_dir: Path to skill directory

        Returns:
            SkillMetadata object
        """
        content = skill_file.read_text()

        # Extract YAML metadata block
        yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', content, re.DOTALL)
        if not yaml_match:
            raise ValueError(f"No YAML metadata found in {skill_file}")

        yaml_content = yaml_match.group(1)
        metadata_dict = yaml.safe_load(yaml_content)

        # Extract parameters from markdown table
        parameters = self._parse_parameters_table(content)

        # Get file timestamps
        stat = skill_file.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        updated_at = datetime.fromtimestamp(stat.st_mtime)

        return SkillMetadata(
            name=metadata_dict.get('name', skill_dir.name),
            version=metadata_dict.get('version', '1.0.0'),
            author=metadata_dict.get('author', 'Unknown'),
            description=metadata_dict.get('description', ''),
            category=metadata_dict.get('category', 'utility'),
            tags=metadata_dict.get('tags', []),
            requirements=self._extract_requirements(content),
            parameters=parameters,
            skill_dir=skill_dir,
            skill_file=skill_file,
            created_at=created_at,
            updated_at=updated_at
        )

    def _parse_parameters_table(self, content: str) -> Dict[str, dict]:
        """
        Parse parameters from markdown table.

        Args:
            content: SKILL.md file content

        Returns:
            Dictionary of parameter definitions
        """
        parameters = {}

        # Find parameters section
        params_section = re.search(
            r'## Parameters\s*\n\n(.*?)(?=\n## |\Z)',
            content,
            re.DOTALL
        )

        if not params_section:
            return parameters

        # Parse markdown table
        table_rows = re.findall(
            r'\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|',
            params_section.group(1)
        )

        for row in table_rows:
            param_name, param_type, required, description, default = row

            # Skip header row
            if param_name.lower() == 'parameter':
                continue

            parameters[param_name] = {
                'type': param_type,
                'required': required.lower() in ['yes', 'true'],
                'description': description,
                'default': default if default != '-' else None
            }

        return parameters

    def _extract_requirements(self, content: str) -> List[str]:
        """
        Extract requirements from SKILL.md.

        Args:
            content: SKILL.md file content

        Returns:
            List of requirements
        """
        requirements = []

        # Find requirements section
        req_section = re.search(
            r'## Requirements\s*\n\n(.*?)(?=\n## |\Z)',
            content,
            re.DOTALL
        )

        if not req_section:
            return requirements

        # Extract list items
        req_items = re.findall(r'- (.+)', req_section.group(1))
        requirements.extend(req_items)

        return requirements

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        Get skill metadata by name.

        Args:
            name: Skill name

        Returns:
            SkillMetadata or None if not found
        """
        return self.skills.get(name)

    def list_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """
        List all skills, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of SkillMetadata objects
        """
        skills = list(self.skills.values())

        if category:
            skills = [s for s in skills if s.category == category]

        return sorted(skills, key=lambda s: s.name)

    def search_skills(self, query: str) -> List[SkillMetadata]:
        """
        Search skills by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching SkillMetadata objects
        """
        query_lower = query.lower()
        results = []

        for skill in self.skills.values():
            # Search in name, description, and tags
            if (query_lower in skill.name.lower() or
                query_lower in skill.description.lower() or
                any(query_lower in tag.lower() for tag in skill.tags)):
                results.append(skill)

        return sorted(results, key=lambda s: s.name)

    def validate_skill(self, name: str) -> tuple[bool, List[str]]:
        """
        Validate a skill's structure and requirements.

        Args:
            name: Skill name

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        skill = self.get_skill(name)
        if not skill:
            return False, [f"Skill '{name}' not found"]

        issues = []

        # Check skill directory exists
        if not skill.skill_dir.exists():
            issues.append(f"Skill directory not found: {skill.skill_dir}")

        # Check SKILL.md exists
        if not skill.skill_file.exists():
            issues.append(f"SKILL.md not found: {skill.skill_file}")

        # Check for main script file (common patterns)
        script_patterns = [
            skill.skill_dir / f"{skill.name}.py",
            skill.skill_dir / "main.py",
            skill.skill_dir / "script.py",
        ]

        has_script = any(p.exists() for p in script_patterns)
        if not has_script:
            issues.append(f"No main script found (expected .py file in {skill.skill_dir})")

        # Validate metadata fields
        if not skill.name:
            issues.append("Skill name is required")

        if not skill.version:
            issues.append("Skill version is required")

        if not skill.description:
            issues.append("Skill description is required")

        # Validate category
        valid_categories = ['utility', 'communication', 'research', 'automation', 'analysis']
        if skill.category not in valid_categories:
            issues.append(f"Invalid category '{skill.category}' (must be one of {valid_categories})")

        is_valid = len(issues) == 0
        return is_valid, issues

    def refresh(self) -> int:
        """
        Refresh the skill registry by rediscovering all skills.

        Returns:
            Number of skills discovered
        """
        self.skills.clear()
        return self.discover_skills()

    def get_stats(self) -> Dict[str, any]:
        """
        Get registry statistics.

        Returns:
            Dictionary of statistics
        """
        categories = {}
        for skill in self.skills.values():
            categories[skill.category] = categories.get(skill.category, 0) + 1

        return {
            'total_skills': len(self.skills),
            'categories': categories,
            'skills_by_name': sorted(self.skills.keys())
        }
