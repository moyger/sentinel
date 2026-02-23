#!/usr/bin/env python
"""
Test Slack notifications for heartbeat system.

This script sends a test heartbeat notification to verify Slack integration works.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from slack_sdk.web.async_client import AsyncWebClient
from src.heartbeat.notifier import Notifier
from src.utils.config import config
from src.utils.logging_config import init_logging, get_logger

logger = get_logger(__name__)


async def test_slack_notifications():
    """Test sending notifications to Slack."""
    print("=" * 60)
    print("SLACK NOTIFICATION TEST")
    print("=" * 60)
    print()

    # Check configuration
    if not config.SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN not configured in .env")
        print("   Please add your Slack bot token to .env file")
        return False

    if not config.SLACK_NOTIFICATION_CHANNEL:
        print("⚠️  SLACK_NOTIFICATION_CHANNEL not configured")
        print("   Using DM to test (you can set a channel in .env)")
        print()

    # Initialize Slack client
    print(f"📱 Connecting to Slack...")
    slack_client = AsyncWebClient(token=config.SLACK_BOT_TOKEN)

    # Test connection
    try:
        auth_response = await slack_client.auth_test()
        bot_user = auth_response["user"]
        team = auth_response["team"]
        print(f"   ✅ Connected as @{bot_user} in {team}")
        print()
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return False

    # Create notifier
    notifier = Notifier(slack_client=slack_client)

    # Create test heartbeat results
    print("🧪 Creating test heartbeat results...")
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "alerts": [
            {
                "source": "gmail",
                "title": "Test Email Alert",
                "message": "This is a test urgent email notification from Sentinel.\n\nFrom: test@example.com\nSubject: Test Alert",
                "priority": "urgent",
                "metadata": {"test": True}
            },
            {
                "source": "calendar",
                "title": "Test Meeting Alert",
                "message": "Upcoming test meeting in 30 minutes\nTime: 2:00 PM (60 min)\nAttendees: 5",
                "priority": "normal",
                "metadata": {"test": True}
            },
            {
                "source": "asana",
                "title": "Test Task Alert",
                "message": "Test task due today\nProject: Testing\nPriority: High",
                "priority": "low",
                "metadata": {"test": True}
            }
        ],
        "summary": {
            "total_monitors": 3,
            "successful_monitors": 3,
            "failed_monitors": 0,
            "total_alerts": 3,
            "alerts_by_priority": {
                "urgent": 1,
                "normal": 1,
                "low": 1
            },
            "alerts_by_source": {
                "gmail": 1,
                "calendar": 1,
                "asana": 1
            }
        },
        "analysis": """
Your most urgent item is the test email from test@example.com that requires immediate attention.

You also have a meeting coming up in 30 minutes with 5 attendees - make sure you're prepared.

The task in your Testing project is due today but has lower priority compared to the email and meeting.

Recommendations:
• Address the urgent email first (5-10 min)
• Review meeting agenda before 2:00 PM
• Complete the testing task after the meeting
"""
    }

    # Determine target channel
    target = config.SLACK_NOTIFICATION_CHANNEL or None

    if target:
        print(f"📤 Sending test notification to {target}...")
    else:
        print("📤 Sending test notification (will use default behavior)...")

    # Send notification
    try:
        await notifier.send_heartbeat_summary(test_results, send_to=target)
        print("   ✅ Notification sent successfully!")
        print()
        print("=" * 60)
        print("✅ SLACK NOTIFICATION TEST PASSED")
        print("=" * 60)
        print()
        print("Check your Slack workspace to see the test notification.")
        print("It should include:")
        print("  • 3 alerts (1 urgent, 1 normal, 1 low)")
        print("  • Summary statistics")
        print("  • Formatted with Slack blocks")
        print()
        return True

    except Exception as e:
        print(f"   ❌ Failed to send notification: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 60)
        print("❌ SLACK NOTIFICATION TEST FAILED")
        print("=" * 60)
        print()
        print("Common issues:")
        print("  • Bot not invited to channel")
        print("  • Invalid channel name (should start with #)")
        print("  • Insufficient permissions")
        print()
        return False


async def main():
    """Main entry point."""
    # Initialize logging
    init_logging()

    success = await test_slack_notifications()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
