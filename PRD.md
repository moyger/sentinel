# Sentinel - Agentic Second Brain (Claude Code Core)

## 1. Vision & Strategy

Replicate the groundbreaking agentic capabilities of **OpenClaw** (Memory, Heartbeat, Adapters, Skills) using **Claude Code** and the **Claude Agent SDK** as the primary engine. This approach prioritizes security by building a custom solution that avoids the vulnerabilities found in large, unvetted open-source codebases and public skill marketplaces.

Openclaw repository: https://github.com/openclaw/openclaw

## 2. Component Architecture

### A. Memory System (The Foundation)

**Objective:** Create a hybrid storage layer that combines the portability of Markdown with the query power of SQLite.

- **Hybrid Storage Architecture:** Use Markdown-driven storage for portability, supplemented by a **SQLite database** for light RAG and session indexing.
- **Obsidian Integration:** Store Markdown files in an Obsidian vault for human-led editing and local searching while the agent is deployed remotely.
- **Core Files:**
    - `soul.md`: Captures identity, deep personal values, and evolving personality.
    - `user.md`: Stores static preferences and constant user context.
    - `memory.md`: Repository for major decisions and historical context.
    - `agents.md`: Defines global behavioral boundaries for specialist personas.
    - `daily/`: Folder for chronological session logs and daily debriefs.

### B. Heartbeat System (Proactive Engine)

**Objective:** Enable the agent to reason and act without user initiation.

- **Scheduled Reasoning:** Use the **Claude Agent SDK** to run a Python script as a scheduled job (e.g., every 30 minutes).
- **Continuous Monitoring:** The agent proactively checks data sources like Gmail, Google Calendar, Asana, and Slack.
- **Proactive Notifications:** The agent sends alerts for urgent items, such as empty prep docs for upcoming meetings, rather than just waiting for commands.

### C. Interface Adapters

**Objective:** Multi-surface interaction for mobile and desktop use.

- **Lean Adapter Focus:** Prioritize a single, robust platform (e.g., **Slack with Socket Mode**) to minimize the security attack surface.
- **Persistent Threads:** Ensure conversations maintain context over time through thread support.
- **Terminal CLI:** Direct interaction via Claude Code for high-bandwidth engineering tasks.

### D. Skill Registry (The Toolkit)

**Objective:** Secure, local-only capabilities that extend the agent's reach.

- **Local-Only Storage:** All skills are hosted in `.claude/skills/` to eliminate supply chain attack risks from public registries.
- **Structure:** Each skill is a directory with a `SKILL.md` instruction file and supporting scripts.

---

## 3. Implementation Process

1. **Clone OpenClaw Repo:** Use it as a structural blueprint (MIT Licensed).
2. **Analyze & Replicate:** Use Claude Code to analyze OpenClaw’s memory and heartbeat logic.
3. **One-Shot Build:** Direct Claude Code to build the minimalist core (SQLite + Markdown) adapted to your specific tech stack.
4. **Iterative Extension:** Repeat the process for heartbeat integrations, Slack adapters, and custom skills.