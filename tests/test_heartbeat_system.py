"""
Test suite for Heartbeat system.

Tests the core components without requiring real API credentials.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.heartbeat.scheduler import HeartbeatScheduler
from src.heartbeat.orchestrator import HeartbeatOrchestrator
from src.heartbeat.base_monitor import BaseMonitor, Alert
from src.heartbeat.notifier import Notifier
from src.heartbeat.reasoning_engine import ReasoningEngine
from src.memory.session_logger import SessionLogger


class MockMonitor(BaseMonitor):
    """Mock monitor for testing."""

    def __init__(self, name: str, alert_count: int = 0):
        super().__init__(name)
        self.alert_count = alert_count
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize mock monitor."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Cleanup mock monitor."""
        self.initialized = False

    async def check(self) -> dict:
        """Perform mock check."""
        alerts = []
        for i in range(self.alert_count):
            alert = self.create_alert(
                title=f"Test Alert {i+1}",
                message=f"This is test alert {i+1} from {self.name}",
                priority="normal" if i == 0 else "low"
            )
            alerts.append(alert.to_dict())

        return {
            "alerts": alerts,
            "data": {"test_data": f"Data from {self.name}"},
            "metadata": {"monitor": self.name}
        }


@pytest.mark.asyncio
async def test_alert_creation():
    """Test alert creation and serialization."""
    monitor = MockMonitor("test")

    alert = monitor.create_alert(
        title="Test Alert",
        message="Test message",
        priority="urgent",
        metadata={"key": "value"}
    )

    assert alert.title == "Test Alert"
    assert alert.message == "Test message"
    assert alert.priority == "urgent"
    assert alert.source == "test"
    assert alert.metadata["key"] == "value"

    # Test serialization
    alert_dict = alert.to_dict()
    assert alert_dict["title"] == "Test Alert"
    assert "timestamp" in alert_dict

    print("✅ Alert creation test passed")


@pytest.mark.asyncio
async def test_orchestrator():
    """Test heartbeat orchestrator."""
    # Create session logger
    session_logger = SessionLogger()
    await session_logger.initialize()

    # Create orchestrator
    orchestrator = HeartbeatOrchestrator(session_logger)

    # Register mock monitors
    monitor1 = MockMonitor("gmail", alert_count=2)
    monitor2 = MockMonitor("calendar", alert_count=1)
    monitor3 = MockMonitor("asana", alert_count=0)

    await monitor1.initialize()
    await monitor2.initialize()
    await monitor3.initialize()

    orchestrator.register_monitor("gmail", monitor1)
    orchestrator.register_monitor("calendar", monitor2)
    orchestrator.register_monitor("asana", monitor3)

    # Execute heartbeat
    results = await orchestrator.execute_heartbeat()

    # Verify results
    assert "monitors" in results
    assert "alerts" in results
    assert "summary" in results
    assert "timestamp" in results

    # Check monitors ran
    assert len(results["monitors"]) == 3
    assert results["monitors"]["gmail"]["status"] == "success"
    assert results["monitors"]["calendar"]["status"] == "success"
    assert results["monitors"]["asana"]["status"] == "success"

    # Check alerts collected
    assert len(results["alerts"]) == 3  # 2 from gmail + 1 from calendar
    assert results["alerts"][0]["source"] == "gmail"
    assert results["alerts"][2]["source"] == "calendar"

    # Check summary
    summary = results["summary"]
    assert summary["total_monitors"] == 3
    assert summary["successful_monitors"] == 3
    assert summary["failed_monitors"] == 0
    assert summary["total_alerts"] == 3

    # Cleanup
    await monitor1.cleanup()
    await monitor2.cleanup()
    await monitor3.cleanup()
    await session_logger.close()

    print("✅ Orchestrator test passed")


@pytest.mark.asyncio
async def test_notifier_deduplication():
    """Test notification deduplication."""
    notifier = Notifier(slack_client=None)  # No Slack client for testing

    # Create test alerts
    alert1 = {
        "source": "gmail",
        "title": "Test Alert",
        "message": "Test message",
        "priority": "normal"
    }

    alert2 = {
        "source": "gmail",
        "title": "Test Alert",  # Same title/source
        "message": "Different message",
        "priority": "normal"
    }

    alert3 = {
        "source": "calendar",
        "title": "Test Alert",  # Same title, different source
        "message": "Test message",
        "priority": "normal"
    }

    # Test deduplication
    alerts = [alert1, alert2, alert3]
    deduplicated = notifier._deduplicate_alerts(alerts)

    # Should keep alert1 and alert3 (different sources)
    # Should remove alert2 (duplicate of alert1)
    assert len(deduplicated) == 2
    assert deduplicated[0]["source"] == "gmail"
    assert deduplicated[1]["source"] == "calendar"

    print("✅ Notifier deduplication test passed")


@pytest.mark.asyncio
async def test_notifier_dnd():
    """Test do-not-disturb logic."""
    notifier = Notifier(slack_client=None)

    # Test with DND times
    notifier.dnd_start = datetime.strptime("22:00", "%H:%M").time()
    notifier.dnd_end = datetime.strptime("08:00", "%H:%M").time()

    # Just verify the method exists and runs
    # Actual DND logic depends on current time
    is_dnd = notifier._is_dnd_active()
    assert isinstance(is_dnd, bool)

    print("✅ Notifier DND test passed")


@pytest.mark.asyncio
async def test_scheduler_callback():
    """Test scheduler callback execution."""
    callback_executed = False
    callback_count = 0

    async def test_callback():
        nonlocal callback_executed, callback_count
        callback_executed = True
        callback_count += 1

    scheduler = HeartbeatScheduler(test_callback)

    # Test callback execution (without actually starting scheduler)
    await scheduler._execute_heartbeat()

    assert callback_executed is True
    assert callback_count == 1

    print("✅ Scheduler callback test passed")


@pytest.mark.asyncio
async def test_monitor_enable_disable():
    """Test monitor enable/disable functionality."""
    monitor = MockMonitor("test")
    await monitor.initialize()

    # Should be enabled by default
    assert monitor.is_enabled() is True

    # Disable
    monitor.disable()
    assert monitor.is_enabled() is False

    # Re-enable
    monitor.enable()
    assert monitor.is_enabled() is True

    await monitor.cleanup()

    print("✅ Monitor enable/disable test passed")


@pytest.mark.asyncio
async def test_reasoning_engine_mock():
    """Test reasoning engine with mocked Claude API."""

    # Mock the Claude API response
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a test analysis from Claude.")]
    mock_response.usage.total_tokens = 100

    with patch('src.heartbeat.reasoning_engine.AsyncAnthropic') as mock_anthropic:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        # Create engine
        engine = ReasoningEngine()

        # Test analysis
        heartbeat_results = {
            "alerts": [
                {
                    "title": "Test Alert",
                    "message": "Test message",
                    "priority": "urgent",
                    "source": "gmail"
                }
            ],
            "summary": {
                "total_alerts": 1,
                "alerts_by_priority": {"urgent": 1}
            },
            "monitors": {
                "gmail": {"status": "success"}
            }
        }

        result = await engine.analyze_heartbeat(heartbeat_results)

        assert result["has_insights"] is True
        assert "analysis" in result
        assert result["alert_count"] == 1

    print("✅ Reasoning engine mock test passed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("HEARTBEAT SYSTEM TESTS")
    print("=" * 60)
    print()

    try:
        # Run tests
        await test_alert_creation()
        await test_orchestrator()
        await test_notifier_deduplication()
        await test_notifier_dnd()
        await test_scheduler_callback()
        await test_monitor_enable_disable()
        await test_reasoning_engine_mock()

        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    asyncio.run(main())
