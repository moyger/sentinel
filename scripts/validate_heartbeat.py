#!/usr/bin/env python
"""
Validate heartbeat system initialization.

This script checks if all heartbeat components can be imported and
initialized without errors (without requiring actual API credentials).
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def validate_imports():
    """Validate all imports work."""
    print("=" * 60)
    print("HEARTBEAT SYSTEM VALIDATION")
    print("=" * 60)
    print()

    try:
        print("📦 Importing core components...")
        from src.heartbeat.scheduler import HeartbeatScheduler
        from src.heartbeat.orchestrator import HeartbeatOrchestrator
        from src.heartbeat.base_monitor import BaseMonitor, Alert
        from src.heartbeat.notifier import Notifier
        from src.heartbeat.reasoning_engine import ReasoningEngine
        print("   ✅ Core components imported")

        print("\n📦 Importing monitors...")
        from src.heartbeat.gmail_monitor import GmailMonitor
        from src.heartbeat.calendar_monitor import CalendarMonitor
        from src.heartbeat.asana_monitor import AsanaMonitor
        print("   ✅ Monitors imported")

        print("\n📦 Importing main application...")
        from src.heartbeat.heartbeat_app import HeartbeatApp
        print("   ✅ Main application imported")

        print("\n📦 Importing dependencies...")
        from src.memory.session_logger import SessionLogger
        from src.utils.config import config
        from src.utils.logging_config import get_logger
        print("   ✅ Dependencies imported")

        print("\n🔧 Testing component initialization...")

        # Test alert creation
        print("   • Testing Alert creation...")
        alert = Alert(
            title="Test Alert",
            message="Test message",
            priority="urgent",
            source="test"
        )
        assert alert.title == "Test Alert"
        print("     ✅ Alert creation works")

        # Test orchestrator
        print("   • Testing Orchestrator...")
        session_logger = SessionLogger()
        await session_logger.initialize()
        orchestrator = HeartbeatOrchestrator(session_logger)
        status = orchestrator.get_status()
        assert "registered_monitors" in status
        await session_logger.close()
        print("     ✅ Orchestrator works")

        # Test notifier (without Slack client)
        print("   • Testing Notifier...")
        notifier = Notifier(slack_client=None)
        assert notifier is not None
        print("     ✅ Notifier works")

        # Test reasoning engine (creation only, no API calls)
        print("   • Testing Reasoning Engine...")
        engine = ReasoningEngine()
        assert engine is not None
        print("     ✅ Reasoning Engine works")

        # Test scheduler (creation only, not starting)
        print("   • Testing Scheduler...")
        async def dummy_callback():
            pass
        scheduler = HeartbeatScheduler(dummy_callback)
        assert scheduler.interval_minutes > 0
        print("     ✅ Scheduler works")

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION CHECKS PASSED")
        print("=" * 60)
        print()
        print("The heartbeat system is properly installed and configured.")
        print("To run with actual API credentials, configure your .env file")
        print("and run: ./scripts/run_heartbeat.sh")
        print()

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ VALIDATION FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await validate_imports()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
