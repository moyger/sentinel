# Sentinel - Agentic Second Brain

An autonomous AI agent powered by Claude Code and the Claude Agent SDK, featuring memory, proactive monitoring, and multi-surface interaction capabilities.

## Overview

Sentinel replicates the groundbreaking agentic capabilities of OpenClaw (Memory, Heartbeat, Adapters, Skills) with a focus on security through custom, local-only implementation. Built on Claude Code as the primary reasoning engine.

### Key Features

- **Hybrid Memory System**: Markdown portability + SQLite query power with Obsidian integration
- **Proactive Heartbeat**: Autonomous monitoring of Gmail, Calendar, Asana, and Slack
- **Multi-Surface Adapters**: Slack (Socket Mode) and Terminal CLI interaction
- **Local Skill Registry**: Secure, local-only capabilities in `.claude/skills/`

## Project Structure

```
sentinel/
├── .claude/
│   ├── commands/          # Custom slash commands
│   ├── rules/             # Agent behavioral rules
│   └── skills/            # Local skill definitions
├── memory/
│   ├── daily/             # Daily session logs
│   ├── topics/            # Topic-based memory organization
│   ├── soul.md            # Identity and personality
│   ├── user.md            # User preferences and context
│   ├── memory.md          # Major decisions and history
│   └── agents.md          # Agent behavioral boundaries
├── src/
│   ├── memory/            # Memory system implementation
│   ├── adapters/          # Interface adapters (Slack, CLI)
│   ├── heartbeat/         # Proactive monitoring engine
│   ├── skills/            # Skill management system
│   └── utils/             # Shared utilities
├── config/                # Configuration files
├── logs/                  # Application logs
├── scripts/               # Helper scripts
├── .env                   # Environment variables (create from template)
├── requirements.txt       # Python dependencies
├── PRD.md                 # Product Requirements Document
└── TASKS.md               # Implementation task breakdown

```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Slack workspace (for Slack adapter)
- Google Cloud project (for Gmail/Calendar integration)
- Asana account (for task monitoring)

### Installation

1. **Clone the repository**
   ```bash
   cd sentinel
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env and fill in your API keys and configuration
   ```

5. **Set up Google Workspace credentials**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API and Google Calendar API
   - Download OAuth credentials JSON
   - Save as `config/google_credentials.json`

6. **Set up Slack app**
   - Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
   - Enable Socket Mode
   - Install to your workspace
   - Copy Bot Token, App Token, and Signing Secret to `.env`

### Configuration

Edit `.env` to configure:

- **Anthropic Claude API**: `ANTHROPIC_API_KEY`
- **Slack**: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`
- **Google**: `GOOGLE_CREDENTIALS_FILE`, `GMAIL_USER_EMAIL`, `GOOGLE_CALENDAR_ID`
- **Asana**: `ASANA_ACCESS_TOKEN`, `ASANA_WORKSPACE_GID`
- **Heartbeat**: Interval, enabled monitors, quiet hours
- **Logging**: Log level, file paths, rotation settings

See [.env.template](.env.template) for all available options.

## Usage

### Running Sentinel

```bash
# Start the Slack adapter (coming soon)
python -m src.adapters.slack_bot

# Run heartbeat monitoring (coming soon)
python -m src.heartbeat.runner

# Interactive CLI (coming soon)
python -m src.adapters.cli
```

### Testing Configuration

```bash
# Validate configuration
python -c "from src.utils.config import config; errors = config.validate(); print('✓ Valid' if not errors else f'Errors: {errors}')"

# Display current config (secrets masked)
python -c "from src.utils.config import config; print(config.display_config())"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_memory.py
```

## Development Roadmap

See [TASKS.md](TASKS.md) for detailed implementation tasks organized by phase:

1. **Phase 1: Core Memory Setup** - Hybrid storage, core files, Obsidian integration
2. **Phase 2: Slack Router** - Socket Mode, thread persistence, message routing
3. **Phase 3: Heartbeat Loop** - Scheduled monitoring, proactive notifications
4. **Phase 4: MCP Integration** - Skill discovery, execution framework

## Architecture

### Memory System
Combines Markdown files (human-editable, portable) with SQLite (queryable, structured):
- Core files: `soul.md`, `user.md`, `memory.md`, `agents.md`
- Session logs in `daily/` with automatic rotation
- Topic-based organization in `topics/`
- Optional Obsidian vault sync for local editing

### Heartbeat System
Runs every 30 minutes (configurable) to:
- Check Gmail for urgent emails
- Monitor Calendar for upcoming meetings without prep
- Review Asana tasks (overdue, high-priority)
- Scan Slack for mentions/DMs
- Send intelligent notifications via Slack

### Adapters
- **Slack (Socket Mode)**: Real-time messaging with thread persistence
- **Terminal CLI**: Direct interaction for high-bandwidth tasks

### Skills
Local-only capabilities stored in `.claude/skills/`:
- Each skill = directory with `SKILL.md` + scripts
- No public registries (security first)
- Executed via Claude Agent SDK

## Security

- **No public skill marketplaces**: All skills are local and audited
- **Environment variables**: Secrets in `.env` (never committed)
- **Minimal dependencies**: Curated dependencies to reduce attack surface
- **Local-first**: Memory and skills stored locally, not in cloud

## Contributing

This is a personal agentic system. For your own implementation:
1. Fork the repository
2. Follow setup instructions
3. Customize `soul.md`, `user.md`, and skills to your needs
4. Contribute improvements via pull requests

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [OpenClaw](https://github.com/openclaw/openclaw)
- Powered by [Anthropic Claude](https://www.anthropic.com/claude)
- Built with [Claude Code](https://code.claude.com/)

## Support

- Documentation: See [PRD.md](PRD.md) for detailed architecture
- Issues: Report bugs and feature requests via GitHub Issues
- Tasks: Track progress in [TASKS.md](TASKS.md)

---

**Status**: 🚧 Under active development - Phase 1 (Infrastructure Setup) complete
