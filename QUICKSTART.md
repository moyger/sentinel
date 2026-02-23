# Sentinel - Quick Start Guide

Get Sentinel up and running in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Installation

### 1. Run Setup Script

```bash
./scripts/setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create `.env` from template
- Set up directory structure

### 2. Configure API Keys

Edit `.env` and add your credentials:

```bash
# Required for core functionality
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional - for Slack integration (Phase 2)
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_APP_TOKEN=xapp-xxxxx

# Optional - for Heartbeat (Phase 3)
GOOGLE_CREDENTIALS_FILE=./config/google_credentials.json
ASANA_ACCESS_TOKEN=xxxxx
```

### 3. Test the System

```bash
source venv/bin/activate
./scripts/test_phase1.sh
```

You should see:
```
🎉 All tests passed! Phase 1 is complete.
```

## Basic Usage

### Using the Session Logger

```python
import asyncio
from src.memory.session_logger import SessionLogger

async def main():
    async with SessionLogger() as logger:
        # Start a conversation
        session = await logger.start_session(
            adapter="cli",
            user_id="demo_user"
        )

        # Log some messages
        await logger.log_user_message("What's the weather?")
        await logger.log_assistant_message("I can help with that!")

        # Get conversation history
        history = await logger.get_conversation_history()
        print(f"Conversation has {len(history)} messages")

        # End the session
        await logger.end_session()

asyncio.run(main())
```

### Working with Memory

```python
from src.memory.operations import MemoryOperations
from src.memory.database import get_database
from src.memory.models import MemoryEntry

async def save_memory():
    db = get_database()
    await db.connect()
    await db.initialize_schema()

    ops = MemoryOperations(db)

    # Create a memory entry
    memory = MemoryEntry(
        title="API Key Location",
        content="API keys are stored in .env file",
        entry_type="fact",
        importance=7,
        tags=["configuration", "security"]
    )

    await ops.create_memory(memory)
    print(f"Memory saved: {memory.id}")

    # Search for memories
    facts = await ops.search_memories(entry_type="fact")
    print(f"Found {len(facts)} facts in memory")

    await db.close()

asyncio.run(save_memory())
```

### Managing Markdown Files

```python
from src.memory.markdown_manager import MarkdownManager

md = MarkdownManager()

# Add a decision to memory.md
md.add_decision(
    title="Use SQLite + Markdown",
    context="Need hybrid storage for memory system",
    decision="Use SQLite for queries, Markdown for portability",
    rationale="Best of both worlds",
    tags=["architecture"]
)

# Create a topic file
md.create_topic_file(
    topic_id="project-ideas",
    topic_name="Project Ideas",
    description="Cool project ideas to explore"
)

# Add to daily log
md.append_to_daily_log(
    "Completed Phase 1 implementation!",
    section="Key Events"
)
```

## Project Structure

```
sentinel/
├── memory/              # Human-readable memory files
│   ├── soul.md         # Your identity and values
│   ├── user.md         # Your preferences
│   ├── memory.md       # Decisions and history
│   ├── agents.md       # Agent behavior rules
│   ├── daily/          # Daily logs
│   └── topics/         # Topic files
│
├── src/
│   ├── memory/         # Core memory system
│   ├── adapters/       # Communication adapters (Phase 2)
│   ├── heartbeat/      # Proactive monitoring (Phase 3)
│   ├── skills/         # Skill management (Phase 4)
│   └── utils/          # Shared utilities
│
├── config/             # Configuration files
├── logs/               # Application logs
├── tests/              # Test suite
└── scripts/            # Helper scripts
```

## Customizing Sentinel

### 1. Update Your Identity (soul.md)

Edit `memory/soul.md` to capture your:
- Core values
- Personality traits
- Working style
- Aspirations

### 2. Set Your Preferences (user.md)

Edit `memory/user.md` to configure:
- Communication style
- Notification preferences
- Work schedule
- Tools and platforms

### 3. Configure Agent Behavior (agents.md)

Edit `memory/agents.md` to define:
- What the agent should/shouldn't do
- Proactivity levels
- Interaction patterns

## Common Tasks

### View Configuration

```bash
python -c "from src.utils.config import config; print(config.display_config())"
```

### Check Database

```bash
sqlite3 memory/sentinel.db ".tables"
```

### View Daily Logs

```bash
ls -la memory/daily/
cat memory/daily/$(date +%Y-%m-%d).md
```

### Run Specific Test

```python
python tests/test_memory_system.py
```

## Troubleshooting

### "No module named 'src'"

Make sure you're in the project root and virtual environment is activated:
```bash
cd /path/to/sentinel
source venv/bin/activate
```

### "Database is locked"

Close any other connections to the database:
```bash
# Find processes using the database
lsof memory/sentinel.db

# Or just remove the lock file
rm memory/sentinel.db-journal
```

### "API key not found"

Ensure your `.env` file has the required keys:
```bash
cat .env | grep ANTHROPIC_API_KEY
```

## Next Steps

Once Phase 1 is working:

1. **Phase 2: Slack Integration**
   - Set up Slack app
   - Implement Socket Mode connection
   - Add message routing

2. **Phase 3: Heartbeat**
   - Configure Google Workspace
   - Set up Asana integration
   - Implement proactive monitoring

3. **Phase 4: Skills**
   - Create custom skills
   - Build skill execution framework
   - Test with Claude Agent SDK

## Resources

- [PRD.md](PRD.md) - Full product requirements
- [TASKS.md](TASKS.md) - Detailed task breakdown
- [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) - Phase 1 summary
- [README.md](README.md) - Complete documentation

## Getting Help

- Check logs: `tail -f logs/sentinel.log`
- Run tests: `./scripts/test_phase1.sh`
- Review config: `python -c "from src.utils.config import config; print(config.display_config())"`

---

**Ready to start?** Run `./scripts/setup.sh` and begin!
