"""
Test script for Phase 1: Core Memory System

Run this to validate the memory system implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import Database
from src.memory.operations import MemoryOperations
from src.memory.markdown_manager import MarkdownManager
from src.memory.session_logger import SessionLogger
from src.memory.models import Session, Message, MemoryEntry, Topic
from src.utils.logging_config import init_logging
from src.utils.config import config

logger = init_logging()


async def test_database_connection():
    """Test 1: Database connection and schema initialization."""
    logger.info("Test 1: Database Connection")

    db = Database(config.SQLITE_DB_PATH)

    try:
        await db.connect()
        logger.info("✓ Database connected")

        await db.initialize_schema()
        logger.info("✓ Schema initialized")

        version = await db.get_schema_version()
        logger.info(f"✓ Schema version: {version}")

        await db.close()
        logger.info("✓ Database closed")

        return True
    except Exception as e:
        logger.error("✗ Database test failed", error=str(e))
        return False


async def test_memory_operations():
    """Test 2: Memory CRUD operations."""
    logger.info("\nTest 2: Memory Operations")

    async with Database() as db:
        ops = MemoryOperations(db)

        try:
            # Create a session
            session = Session(
                adapter="cli",
                user_id="test_user",
                metadata={"test": True}
            )
            await ops.create_session(session)
            logger.info(f"✓ Session created: {session.id[:8]}")

            # Create messages
            msg1 = Message(
                session_id=session.id,
                role="user",
                content="Hello, Sentinel!"
            )
            await ops.create_message(msg1)
            logger.info(f"✓ User message created")

            msg2 = Message(
                session_id=session.id,
                role="assistant",
                content="Hello! How can I help you today?"
            )
            await ops.create_message(msg2)
            logger.info(f"✓ Assistant message created")

            # Retrieve messages
            messages = await ops.get_session_messages(session.id)
            logger.info(f"✓ Retrieved {len(messages)} messages")

            # Create memory entry
            memory = MemoryEntry(
                title="Test Decision",
                content="Decided to use Python for the memory system",
                entry_type="decision",
                importance=8,
                source_session_id=session.id,
                tags=["technical", "architecture"]
            )
            await ops.create_memory(memory)
            logger.info(f"✓ Memory entry created: {memory.id[:8]}")

            # Search memories
            memories = await ops.search_memories(entry_type="decision")
            logger.info(f"✓ Found {len(memories)} decision memories")

            # Create topic
            topic = Topic(
                id="test-topic",
                name="Test Topic",
                description="A topic for testing"
            )
            await ops.create_topic(topic)
            logger.info(f"✓ Topic created: {topic.id}")

            # Link memory to topic
            await ops.link_memory_to_topic(memory.id, topic.id)
            logger.info(f"✓ Memory linked to topic")

            # Get topic memories
            topic_memories = await ops.get_topic_memories(topic.id)
            logger.info(f"✓ Retrieved {len(topic_memories)} memories for topic")

            return True

        except Exception as e:
            logger.error("✗ Memory operations test failed", error=str(e))
            return False


async def test_markdown_manager():
    """Test 3: Markdown file management."""
    logger.info("\nTest 3: Markdown Manager")

    md = MarkdownManager()

    try:
        # Test daily log creation
        log_path = md.create_daily_log()
        logger.info(f"✓ Daily log created: {log_path.name}")

        # Test appending to daily log
        md.append_to_daily_log("Test session started", section="Sessions")
        logger.info("✓ Content appended to daily log")

        # Test reading files
        soul_content = md.read_soul()
        logger.info(f"✓ Soul.md read ({len(soul_content)} chars)")

        user_content = md.read_user()
        logger.info(f"✓ User.md read ({len(user_content)} chars)")

        memory_content = md.read_memory()
        logger.info(f"✓ Memory.md read ({len(memory_content)} chars)")

        agents_content = md.read_agents()
        logger.info(f"✓ Agents.md read ({len(agents_content)} chars)")

        # Test adding a decision
        md.add_decision(
            title="Test Markdown Decision",
            context="Testing the markdown manager",
            decision="Add test decision to memory.md",
            rationale="To verify the system works",
            tags=["test"]
        )
        logger.info("✓ Decision added to memory.md")

        # Test creating topic file
        topic_path = md.create_topic_file(
            "test-topic-md",
            "Test Topic Markdown",
            "A test topic for markdown"
        )
        logger.info(f"✓ Topic file created: {topic_path.name}")

        return True

    except Exception as e:
        logger.error("✗ Markdown manager test failed", error=str(e))
        return False


async def test_session_logger():
    """Test 4: Session logging system."""
    logger.info("\nTest 4: Session Logger")

    async with SessionLogger() as session_logger:
        try:
            # Start a session
            session = await session_logger.start_session(
                adapter="cli",
                user_id="test_user"
            )
            logger.info(f"✓ Session started: {session.id[:8]}")

            # Log messages
            await session_logger.log_user_message("What's the weather?")
            logger.info("✓ User message logged")

            await session_logger.log_assistant_message(
                "I don't have access to weather data yet, but that's a great feature idea!",
                token_count=25
            )
            logger.info("✓ Assistant message logged")

            # Get conversation history
            history = await session_logger.get_conversation_history()
            logger.info(f"✓ Retrieved conversation history ({len(history)} messages)")

            # Get context window
            context = await session_logger.get_context_window()
            logger.info(f"✓ Retrieved context window ({len(context)} messages)")

            # End session
            await session_logger.end_session()
            logger.info("✓ Session ended")

            return True

        except Exception as e:
            logger.error("✗ Session logger test failed", error=str(e))
            return False


async def test_full_workflow():
    """Test 5: Complete workflow integration."""
    logger.info("\nTest 5: Full Workflow Integration")

    async with SessionLogger() as session_logger:
        try:
            # Start session
            session = await session_logger.start_session(
                adapter="cli",
                user_id="integration_test"
            )

            # Simulate conversation
            await session_logger.log_user_message(
                "I've decided to implement the memory system using SQLite and Markdown"
            )

            await session_logger.log_assistant_message(
                "That's a great architectural decision! The hybrid approach gives you "
                "both the portability of Markdown and the query power of SQLite. "
                "Would you like me to remember this decision?"
            )

            await session_logger.log_user_message("Yes, please remember it")

            # Create a memory entry from the conversation
            memory = MemoryEntry(
                title="Hybrid Memory System Architecture",
                content="Using SQLite for querying and Markdown for portability. "
                        "Allows Obsidian integration while maintaining database capabilities.",
                entry_type="decision",
                importance=9,
                source_session_id=session.id,
                tags=["architecture", "memory-system", "database"]
            )

            ops = MemoryOperations(session_logger.db)
            await ops.create_memory(memory)

            # Also add to markdown
            md = session_logger.markdown
            md.add_decision(
                title="Hybrid Memory System Architecture",
                context="Need a memory system that is both portable and queryable",
                decision="Use SQLite + Markdown hybrid approach",
                rationale="Combines portability with query power, enables Obsidian integration",
                impact="Enables rich memory features while keeping data accessible",
                tags=["architecture", "memory-system"]
            )

            await session_logger.log_assistant_message(
                "I've saved this decision to both the database and memory.md. "
                "I'll remember this architectural choice for future reference."
            )

            # End session
            await session_logger.end_session()

            logger.info("✓ Full workflow completed successfully")
            logger.info(f"  - Session with {session.message_count} messages")
            logger.info(f"  - Memory entry created and stored")
            logger.info(f"  - Decision added to memory.md")
            logger.info(f"  - Daily log updated")

            return True

        except Exception as e:
            logger.error("✗ Full workflow test failed", error=str(e))
            return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Core Memory System Tests")
    logger.info("=" * 60)

    # Display configuration
    logger.info("\nConfiguration:")
    logger.info(f"  Database: {config.SQLITE_DB_PATH}")
    logger.info(f"  Memory Dir: {config.MEMORY_DIR}")
    logger.info(f"  Daily Logs: {config.DAILY_DIR}")
    logger.info("")

    results = []

    # Run tests
    results.append(("Database Connection", await test_database_connection()))
    results.append(("Memory Operations", await test_memory_operations()))
    results.append(("Markdown Manager", await test_markdown_manager()))
    results.append(("Session Logger", await test_session_logger()))
    results.append(("Full Workflow", await test_full_workflow()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! Phase 1 is complete.")
        logger.info("\nYou can now:")
        logger.info("  1. Explore the memory/ directory to see generated files")
        logger.info("  2. Check the SQLite database for stored data")
        logger.info("  3. Proceed to Phase 2: Slack Router Implementation")
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed. Please review errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
