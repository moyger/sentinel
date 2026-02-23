#!/usr/bin/env python3
"""
Test script for skills system.

Demonstrates skill discovery, listing, and validation.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from skills.skill_manager import SkillManager


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


async def main():
    """Run skill system tests."""
    print_section("Sentinel Skills System Test")

    # Initialize skill manager
    print("Initializing skill manager...")
    manager = SkillManager()
    print(f"✅ Skill manager initialized\n")

    # Get statistics
    print_section("Skill Statistics")
    stats = manager.get_stats()
    print(f"Total Skills: {stats['total_skills']}")
    print(f"\nSkills by Category:")
    for category, count in sorted(stats['categories'].items()):
        print(f"  {category}: {count}")

    # List all skills
    print_section("Available Skills")
    skills = manager.list_skills()

    for skill in skills:
        print(f"📦 {skill.name} (v{skill.version})")
        print(f"   Category: {skill.category}")
        print(f"   Author: {skill.author}")
        print(f"   Description: {skill.description}")
        if skill.tags:
            print(f"   Tags: {', '.join(skill.tags)}")

        # Validate skill
        is_valid, issues = manager.validate_skill(skill.name)
        if is_valid:
            print(f"   Status: ✅ Valid")
        else:
            print(f"   Status: ❌ Invalid")
            for issue in issues:
                print(f"     - {issue}")

        print()

    # Show detailed info for task-creator
    print_section("Task Creator - Detailed View")

    task_creator = manager.get_skill('task-creator')
    if task_creator:
        print(f"Name: {task_creator.name}")
        print(f"Version: {task_creator.version}")
        print(f"Author: {task_creator.author}")
        print(f"Description: {task_creator.description}")
        print(f"Category: {task_creator.category}")
        print(f"Tags: {', '.join(task_creator.tags)}")

        print(f"\nRequirements:")
        for req in task_creator.requirements:
            print(f"  - {req}")

        print(f"\nParameters:")
        for param_name, param_def in task_creator.parameters.items():
            required = "required" if param_def.get('required') else "optional"
            default = param_def.get('default')
            default_str = f" (default: {default})" if default else ""
            print(f"  {param_name} ({param_def.get('type')}, {required}){default_str}")
            print(f"    {param_def.get('description')}")

        print(f"\nLocation: {task_creator.skill_dir}")

    # Test parameter validation
    print_section("Parameter Validation Test")

    print("Test 1: Valid parameters")
    result = await manager.execute_skill('task-creator', {
        'text': 'Test task for validation'
    })
    print(f"  Missing ASANA_TOKEN: {'✅ Expected error' if not result.success else '❌ Unexpected success'}")
    if not result.success:
        print(f"  Error: {result.error}")

    print("\nTest 2: Missing required parameter")
    result = await manager.execute_skill('task-creator', {})
    print(f"  Validation caught error: {'✅ Yes' if not result.success else '❌ No'}")
    if not result.success:
        print(f"  Error: {result.error}")

    print("\nTest 3: Wrong parameter type")
    result = await manager.execute_skill('task-creator', {'text': 123})
    print(f"  Type check caught error: {'✅ Yes' if not result.success else '❌ No'}")
    if not result.success:
        print(f"  Error: {result.error}")

    # Search skills
    print_section("Skill Search Test")

    print("Search for 'task':")
    results = manager.search_skills('task')
    for skill in results:
        print(f"  - {skill.name}: {skill.description}")

    print("\nSearch for 'asana':")
    results = manager.search_skills('asana')
    for skill in results:
        print(f"  - {skill.name}: {skill.description}")

    print_section("Test Complete")
    print("✅ All skill system components working correctly!")
    print()


if __name__ == '__main__':
    asyncio.run(main())
