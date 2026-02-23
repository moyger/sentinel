# Sentinel - Implementation Tasks

This document breaks down the Sentinel implementation into 4 phases: Core Memory Setup, Slack Router Implementation, Heartbeat Loop, and MCP Integration.

---

## Phase 1: Core Memory Setup

### Database & Schema
- [x] Design SQLite database schema for session indexing
- [x] Design SQLite schema for RAG (vector embeddings/semantic search)
- [x] Implement database connection and initialization module
- [ ] Create database migration system for schema updates
- [ ] Add database backup and recovery utilities

### Core Markdown Files
- [x] Create `soul.md` template (identity, values, evolving personality)
- [x] Create `user.md` template (static preferences, user context)
- [x] Create `memory.md` template (major decisions, historical context)
- [x] Create `agents.md` template (global behavioral boundaries for personas)
- [x] Set up `daily/` folder structure for chronological session logs

### Memory Management Python Modules
- [x] Build memory CRUD operations module (create, read, update, delete)
- [x] Implement Markdown file parser and updater
- [x] Create session logging system that writes to both SQLite and Markdown
- [ ] Build memory retrieval system with semantic search capability
- [ ] Implement memory summarization for long-term storage
- [x] Add memory indexing for efficient querying

### Obsidian Integration
- [x] Configure directory structure compatible with Obsidian vault
- [x] Implement Markdown formatting that preserves Obsidian features (links, tags)
- [ ] Add support for bidirectional links between memory files
- [x] Create topic-based organization in `memory/topics/` folder
- [ ] Test Obsidian vault sync and compatibility

### Daily Log System
- [x] Implement daily log rotation (create new file per day)
- [ ] Build daily debrief generation system
- [x] Add automatic archiving of old daily logs
- [ ] Create daily summary extraction for `memory.md`

---

## Phase 2: Slack Router Implementation

### Slack App Configuration
- [ ] Create Slack app and configure OAuth scopes
- [ ] Set up Socket Mode for real-time connection
- [ ] Configure app credentials and environment variables
- [ ] Add workspace installation and permissions

### Message Routing & Handling
- [ ] Implement Socket Mode connection handler
- [ ] Build message event listener and router
- [ ] Add support for direct messages (DMs)
- [ ] Add support for channel mentions
- [ ] Implement thread detection and routing
- [ ] Create message parsing utilities (extract user, channel, thread info)

### Thread Persistence & Context
- [ ] Build thread context storage in SQLite
- [ ] Implement context retrieval for ongoing conversations
- [ ] Add thread-to-memory linking (save important threads to memory)
- [ ] Create thread summarization for long conversations
- [ ] Implement context window management (token limits)

### Response Formatting
- [ ] Build Slack-specific message formatter (blocks, attachments)
- [ ] Add markdown-to-Slack conversion utilities
- [ ] Implement code block formatting
- [ ] Add support for interactive elements (buttons, menus) if needed
- [ ] Create typing indicators for long-running operations

### Error Handling & Reliability
- [ ] Implement connection error handling and auto-reconnection
- [ ] Add rate limiting to respect Slack API limits
- [ ] Build retry mechanism with exponential backoff
- [ ] Implement message queue for failed sends
- [ ] Add comprehensive logging for debugging
- [ ] Create health check monitoring for Slack connection

---

## Phase 3: Heartbeat Loop

### Scheduled Execution Framework
- [ ] Design heartbeat scheduling system (30-minute intervals)
- [ ] Implement background task scheduler using Claude Agent SDK
- [ ] Build heartbeat orchestrator that coordinates all monitoring tasks
- [ ] Add configuration for heartbeat frequency and monitoring targets
- [ ] Implement graceful shutdown and restart mechanisms

### Gmail Integration
- [ ] Set up Gmail API authentication (OAuth 2.0)
- [ ] Implement email fetching and filtering
- [ ] Build email parsing (extract subject, sender, body, attachments)
- [ ] Add unread email detection
- [ ] Create priority email detection (urgent keywords, important senders)
- [ ] Implement email summarization for quick review

### Google Calendar Integration
- [ ] Set up Google Calendar API authentication
- [ ] Implement event fetching (today, upcoming week)
- [ ] Build meeting prep detection (check for empty prep docs)
- [ ] Add calendar event parsing (time, attendees, location, description)
- [ ] Create upcoming meeting alerts (time-based notifications)
- [ ] Implement calendar conflict detection

### Asana Integration
- [ ] Set up Asana API authentication
- [ ] Implement task fetching (assigned to user, due soon)
- [ ] Build task parsing (title, due date, project, priority)
- [ ] Add overdue task detection
- [ ] Create task prioritization based on due dates and importance
- [ ] Implement task status tracking

### Slack Monitoring (Proactive)
- [ ] Implement Slack channel monitoring for mentions
- [ ] Add direct message monitoring for unread messages
- [ ] Build message urgency detection (keywords, sender importance)
- [ ] Create notification aggregation (avoid spam)

### Notification & Alert System
- [ ] Build notification formatter for different alert types
- [ ] Implement multi-channel notification delivery (Slack, terminal)
- [ ] Add notification priority system (urgent, normal, low)
- [ ] Create notification deduplication (avoid duplicate alerts)
- [ ] Implement notification scheduling (don't disturb hours)
- [ ] Add notification history and tracking

### Proactive Reasoning Engine
- [ ] Build reasoning module that analyzes all data sources
- [ ] Implement decision tree for when to send alerts
- [ ] Add context-aware suggestions (based on calendar + email + tasks)
- [ ] Create proactive action templates (draft messages, create prep docs)
- [ ] Implement learning from user feedback on notifications

### Heartbeat Configuration & Management
- [ ] Create heartbeat configuration file (enable/disable sources, frequency)
- [ ] Build heartbeat status dashboard/CLI command
- [ ] Add heartbeat logging and performance monitoring
- [ ] Implement error recovery for failed heartbeat cycles

---

## Phase 4: MCP Integration

### Claude Agent SDK Setup
- [ ] Install and configure Claude Agent SDK
- [ ] Set up API authentication and credentials
- [ ] Implement Claude Code integration for agent execution
- [ ] Configure model selection and parameters
- [ ] Add token usage tracking and cost monitoring

### Skill Discovery & Loading
- [ ] Build skill discovery system (scan `.claude/skills/` directory)
- [ ] Implement skill metadata parser (read `SKILL.md` files)
- [ ] Create skill registry (index all available skills)
- [ ] Add skill dependency resolution
- [ ] Implement dynamic skill loading at runtime

### Skill Execution Framework
- [ ] Build skill execution engine with proper isolation
- [ ] Implement skill parameter validation and parsing
- [ ] Add skill timeout and resource limits
- [ ] Create skill result handling and formatting
- [ ] Implement skill chaining (use output of one skill as input to another)
- [ ] Add skill execution logging and debugging

### Skill Templates & Documentation
- [ ] Create `SKILL.md` template with standard format
- [ ] Build example skills (e.g., web search, file operations, calculations)
- [ ] Write skill development documentation
- [ ] Create skill testing guide
- [ ] Add skill best practices and security guidelines

### Skill Testing & Validation
- [ ] Build skill testing framework (unit tests for skills)
- [ ] Implement skill validation (check SKILL.md format, required fields)
- [ ] Add skill sandbox for safe testing
- [ ] Create skill regression testing suite
- [ ] Implement skill performance benchmarking

### Error Handling & Security
- [ ] Implement skill error handling and graceful failures
- [ ] Add skill execution logging for debugging
- [ ] Create skill permission system (what each skill can access)
- [ ] Implement skill input sanitization (prevent injection attacks)
- [ ] Add skill output validation (ensure safe outputs)

---

## Additional Setup Tasks

### Project Infrastructure
- [x] Create `requirements.txt` or `pyproject.toml` with all dependencies
- [x] Set up virtual environment configuration
- [x] Create `.env.template` file with required environment variables
- [x] Add `.env` to `.gitignore` for security
- [x] Set up logging configuration (log levels, file rotation)

### Development Tools
- [ ] Build CLI for local testing and development
- [ ] Create debugging utilities (inspect memory, test skills manually)
- [x] Add configuration validation (check all required settings)
- [ ] Implement health check system (verify all integrations are working)

### Documentation
- [x] Write setup instructions (README.md)
- [x] Create configuration guide (how to set up API keys, Slack app, etc.)
- [ ] Document memory system usage
- [ ] Document skill development process
- [ ] Add troubleshooting guide

### Testing
- [ ] Set up pytest configuration
- [x] Write unit tests for core memory operations
- [ ] Write integration tests for Slack router
- [ ] Write tests for heartbeat monitoring
- [x] Create end-to-end test scenarios

---

## Progress Tracking

**Phase 1:** 17/24 tasks completed (71%)
**Phase 2:** 0/25 tasks completed (0%)
**Phase 3:** 0/28 tasks completed (0%)
**Phase 4:** 0/22 tasks completed (0%)
**Additional:** 8/11 tasks completed (73%)

**Total Progress:** 25/110 tasks completed (23%)
