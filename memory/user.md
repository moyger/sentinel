# User - Static Preferences & Constant Context

This document stores static preferences and constant user context that rarely changes. Think of this as your "settings" file.

## Personal Information

### Basic Details
- **Name:**
- **Timezone:**
- **Location:**
- **Preferred Language:**

### Contact Information
- **Primary Email:**
- **Work Email:**
- **Phone:**
- **Slack Workspace:**

## Communication Preferences

### Response Style
- **Tone:** <!-- formal, casual, direct, friendly, etc. -->
- **Length:** <!-- concise, detailed, balanced -->
- **Format:** <!-- bullet points, paragraphs, mixed -->
- **Technical Level:** <!-- beginner, intermediate, expert -->

### Notification Preferences
- **Urgency Threshold:** <!-- When to send urgent notifications -->
- **Quiet Hours:** <!-- When NOT to send notifications -->
- **Preferred Channels:** <!-- Slack, email, etc. -->

### Meeting Preferences
- **Meeting Buffer:** <!-- minutes before/after meetings -->
- **Max Daily Meetings:**
- **Preferred Meeting Times:**
- **Meeting Prep Lead Time:** <!-- how far in advance you need prep -->

## Work Context

### Current Role
- **Title:**
- **Company:**
- **Team:**
- **Manager:**
- **Direct Reports:**

### Work Schedule
- **Working Hours:**
- **Days Off:**
- **Lunch Break:**
- **Focus Time Blocks:**

### Tools & Platforms
- **Primary Tools:**
  - Code Editor:
  - Terminal:
  - Browser:
  - Note-taking:
  - Task Management:
- **Integrations Enabled:**
  - [ ] Gmail
  - [ ] Google Calendar
  - [ ] Asana
  - [ ] Slack
  - [ ] GitHub

## Technical Preferences

### Development Environment
- **Languages:** <!-- primary programming languages -->
- **Frameworks:** <!-- preferred frameworks -->
- **Coding Style:** <!-- style guidelines, preferences -->
- **Testing Approach:** <!-- TDD, integration-first, etc. -->

### Project Management
- **Methodology:** <!-- Agile, Kanban, etc. -->
- **Sprint Length:**
- **Planning Cadence:**

## Personal Systems

### Task Management
- **System:** <!-- GTD, PARA, custom, etc. -->
- **Priority System:** <!-- how you prioritize tasks -->
- **Review Cadence:** <!-- daily, weekly, etc. -->

### Note-taking
- **System:** <!-- Obsidian, Notion, etc. -->
- **Organization:** <!-- tags, folders, links, etc. -->
- **Capture Method:** <!-- how you capture ideas -->

### Calendar Management
- **Scheduling Philosophy:**
- **Color Coding:**
- **Event Types:**

## Interests & Context

### Professional Interests
<!-- Topics and areas you're professionally interested in -->

-
-

### Personal Interests
<!-- Hobbies and personal interests that provide context -->

-
-

### Current Projects
<!-- Active projects to be aware of -->

1. **Project Name:**
   - Status:
   - Priority:
   - Next Action:

## Interaction Guidelines

### How to Help Me
<!-- Specific ways Sentinel can be most helpful -->

-
-

### What to Monitor
<!-- Specific things to watch for in heartbeat monitoring -->

- Gmail:
- Calendar:
- Asana:
- Slack:

### What to Flag
<!-- Conditions that should trigger immediate notification -->

-
-

## Access & Permissions

### API Keys & Credentials
<!-- Reference to where credentials are stored - NOT the actual credentials -->

- Anthropic API Key: `.env`
- Slack Tokens: `.env`
- Google OAuth: `config/google_credentials.json`
- Asana Token: `.env`

### Allowed Actions
<!-- What Sentinel is permitted to do autonomously -->

- [ ] Send Slack messages on my behalf
- [ ] Create calendar events
- [ ] Create tasks in Asana
- [ ] Draft emails (but not send)
- [ ] Update this memory system

---

*Last updated: {{ date }}*
*Update this file when your preferences, context, or circumstances change.*
