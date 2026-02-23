# Heartbeat System Setup Guide

Complete guide to setting up Sentinel's proactive monitoring system.

## Overview

The Heartbeat system is Sentinel's autonomous monitoring engine that runs every 30 minutes (configurable) to check:

- **Gmail**: Unread emails and priority messages
- **Google Calendar**: Upcoming meetings and schedule conflicts
- **Asana**: Overdue tasks and deadlines
- **Slack**: Unread messages and mentions

It then uses Claude AI to analyze findings and send intelligent notifications through Slack.

## Prerequisites

1. **Phase 1 & 2 Complete**: Memory system and Slack integration must be working
2. **Google Cloud Project**: For Gmail and Calendar APIs
3. **Asana Account**: With Personal Access Token
4. **Slack Channel**: For receiving heartbeat notifications

## Google Workspace Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Note your project ID

### Step 2: Enable APIs

1. In the sidebar, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Gmail API**
   - **Google Calendar API**

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Choose application type: **Desktop app**
4. Name it "Sentinel Heartbeat"
5. Click **Create**
6. Download the JSON file
7. Save it to `config/google_credentials.json` in your Sentinel directory

### Step 4: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Fill in app details:
   - App name: "Sentinel"
   - User support email: Your email
   - Developer contact: Your email
4. Click **Save and Continue**
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`
6. Add your email as a test user
7. Click **Save and Continue**

### Step 5: First-Time Authorization

The first time you run the heartbeat system, it will:

1. Open a browser window
2. Ask you to sign in with Google
3. Request permission to access Gmail and Calendar
4. Save a token to `config/google_token.json`

**Note**: The token is saved locally and refreshes automatically.

## Asana Setup

### Step 1: Get Personal Access Token

1. Go to [Asana Developer Console](https://app.asana.com/0/my-apps)
2. Click **Create New Token**
3. Name it "Sentinel Heartbeat"
4. Copy the token (you won't see it again!)
5. Save it to your `.env` file

### Step 2: Get Workspace GID

1. In Asana, go to your workspace
2. Check the URL: `https://app.asana.com/0/1234567890/...`
3. The number after `/0/` is your workspace GID
4. Save it to your `.env` file

## Slack Notification Channel Setup

### Option 1: Use Existing Channel

1. Create a channel for heartbeat alerts (e.g., `#sentinel-alerts`)
2. Invite @Sentinel bot to the channel: `/invite @Sentinel`
3. Copy the channel name to `.env`

### Option 2: Direct Messages

You can also send notifications to a specific user:
- Use their Slack user ID (e.g., `@U01234ABCD`)
- Or use `@username`

## Environment Configuration

Update your `.env` file with these settings:

```bash
# Google Workspace
GOOGLE_CREDENTIALS_PATH=./config/google_credentials.json
GOOGLE_TOKEN_PATH=./config/google_token.json
GMAIL_IMPORTANT_SENDERS=boss@company.com,client@important.com

# Calendar
CALENDAR_PREP_WARNING_MINUTES=60

# Asana
ASANA_ACCESS_TOKEN=your-personal-access-token-here
ASANA_WORKSPACE_GID=1234567890

# Heartbeat Settings
HEARTBEAT_INTERVAL_MINUTES=30

# Notifications
SLACK_NOTIFICATION_CHANNEL=#sentinel-alerts
NOTIFICATION_DND_START=22:00
NOTIFICATION_DND_END=08:00
```

## Configuration Options

### Heartbeat Interval

```bash
HEARTBEAT_INTERVAL_MINUTES=30  # Run every 30 minutes
```

Recommended intervals:
- **15 minutes**: Very active monitoring (high API usage)
- **30 minutes**: Balanced (default)
- **60 minutes**: Light monitoring

### Important Senders

```bash
GMAIL_IMPORTANT_SENDERS=ceo@company.com,client@vip.com,manager@work.com
```

Emails from these senders will trigger alerts even if not marked urgent.

### Meeting Prep Warning

```bash
CALENDAR_PREP_WARNING_MINUTES=60
```

Alert this many minutes before meetings (default: 60).

### Do Not Disturb Hours

```bash
NOTIFICATION_DND_START=22:00  # 10 PM
NOTIFICATION_DND_END=08:00    # 8 AM
```

During these hours:
- Only **urgent** alerts are sent
- Normal/low priority alerts are suppressed

## Running the Heartbeat System

### Quick Start

```bash
./scripts/run_heartbeat.sh
```

### Manual Start

```bash
source venv/bin/activate
python -m src.heartbeat.heartbeat_app
```

### First Run

On first run, you'll see:

```
============================================================
SENTINEL HEARTBEAT SYSTEM
============================================================
Active monitors: ['gmail', 'calendar', 'asana']
Heartbeat interval: 30 minutes
Notifications enabled: #sentinel-alerts

[Browser opens for Google OAuth...]
```

1. Sign in to Google
2. Grant permissions
3. Close the browser
4. Heartbeat will start running

## What Happens During a Heartbeat

Every 30 minutes (or your configured interval):

1. **Monitor Execution**:
   - Gmail: Check unread emails, detect priority
   - Calendar: Check upcoming events, detect conflicts
   - Asana: Check tasks due today/soon, find overdue

2. **Intelligent Analysis**:
   - Claude AI analyzes all findings
   - Identifies patterns and connections
   - Prioritizes based on context

3. **Notification Delivery**:
   - Formats alerts for Slack
   - Groups by priority (urgent, normal, low)
   - Sends summary to notification channel

4. **Memory Logging**:
   - Stores results in SQLite database
   - Logs to daily markdown files
   - Tracks notification history

## Alert Examples

### Gmail Alert

```
🚨 Urgent Email: Q4 Budget Review - Action Required

Gmail

From: ceo@company.com
Subject: Q4 Budget Review - Action Required

Need your input on the Q4 budget by EOD today.
Please review the attached spreadsheet...
```

### Calendar Alert

```
🔔 Meeting Soon: Client Kickoff Call

Calendar

Starting in 45 minutes
Time: 02:00 PM (60 min)
Attendees: 8
Location: Zoom (link in description)
```

### Asana Alert

```
🚨 Overdue Task: Complete Project Proposal

Asana

Overdue by 2 days
Date: Monday, December 18
Project: Client Onboarding
Tags: high-priority, deliverable
```

## Troubleshooting

### "Failed to initialize Gmail monitor"

**Problem**: Google credentials not found or invalid.

**Solution**:
1. Check `config/google_credentials.json` exists
2. Verify it's a valid OAuth client JSON file
3. Delete `config/google_token.json` and re-authorize

### "No alerts to send"

**Problem**: No actionable items found.

**This is normal!** If you have:
- No unread emails
- No upcoming meetings
- No tasks due soon

...the heartbeat will run silently.

### "Monitor disabled, skipping check"

**Problem**: Monitor is explicitly disabled.

**Solution**: Check your `.env` file - monitors are enabled by default. If you disabled one intentionally, this is expected.

### Browser doesn't open for OAuth

**Problem**: Running headless or SSH session.

**Solution**:
1. Run on a machine with a browser
2. Or use `gcloud auth application-default login` to authenticate manually

### Notifications not received

**Check**:
1. `SLACK_NOTIFICATION_CHANNEL` is set correctly
2. Bot is invited to that channel
3. Channel name starts with `#`
4. Not in DND hours (check `NOTIFICATION_DND_START/END`)

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/sentinel-heartbeat.service`:

```ini
[Unit]
Description=Sentinel Heartbeat System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/sentinel
Environment="PATH=/path/to/sentinel/venv/bin"
ExecStart=/path/to/sentinel/venv/bin/python -m src.heartbeat.heartbeat_app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable sentinel-heartbeat
sudo systemctl start sentinel-heartbeat
sudo systemctl status sentinel-heartbeat
```

### Using Docker

Add to `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.heartbeat.heartbeat_app"]
```

Run:

```bash
docker build -t sentinel-heartbeat .
docker run --env-file .env sentinel-heartbeat
```

### Using Screen (Quick)

```bash
screen -S sentinel-heartbeat
source venv/bin/activate
python -m src.heartbeat.heartbeat_app

# Detach: Ctrl+A, then D

# Reattach later
screen -r sentinel-heartbeat
```

## Monitoring the Heartbeat

### Check Logs

```bash
# Real-time logs
tail -f logs/sentinel.log

# Heartbeat cycles only
grep "HEARTBEAT CYCLE" logs/sentinel.log

# Find errors
grep ERROR logs/sentinel.log
```

### Database Queries

```bash
# Check heartbeat history
sqlite3 memory/sentinel.db "SELECT * FROM messages WHERE session_id LIKE 'heartbeat%' ORDER BY timestamp DESC LIMIT 10"

# Count alerts sent today
sqlite3 memory/sentinel.db "SELECT COUNT(*) FROM messages WHERE session_id LIKE 'heartbeat%' AND timestamp >= date('now')"
```

### Slack History

Review the notification channel in Slack to see all past alerts.

## Advanced Configuration

### Custom Monitor Schedule

Want different intervals for different monitors? Modify `heartbeat_app.py`:

```python
# Add custom schedules
self.scheduler.add_job(
    self._check_gmail_only,
    trigger=IntervalTrigger(minutes=15),  # Gmail every 15 min
    id="gmail-only"
)
```

### Custom Alert Priority Logic

Edit `gmail_monitor.py`, `calendar_monitor.py`, or `asana_monitor.py`:

```python
def _check_priority(self, email: Dict[str, Any]) -> Optional[Alert]:
    # Add custom logic here
    if "URGENT" in email['subject'].upper():
        return self.create_alert(
            title=f"Custom: {email['subject']}",
            priority="urgent"
        )
```

### Disable Specific Monitors

In your `.env`:

```bash
# Gmail only
GOOGLE_CREDENTIALS_PATH=./config/google_credentials.json
ASANA_ACCESS_TOKEN=   # Leave empty to disable
```

The heartbeat system automatically disables monitors with missing credentials.

## API Usage & Costs

### Google APIs

- **Free Tier**: 1 billion API calls/day (you'll never hit this)
- **Gmail quota**: 250 quota units/user/second
- **Calendar quota**: 500,000 requests/day

At 30-minute intervals (48 runs/day):
- ~200 API calls/day (well within free tier)

### Anthropic Claude API

Each heartbeat cycle uses Claude for analysis:
- ~500-1000 tokens per analysis
- At $3/million input tokens (Sonnet):
  - $0.0015 - $0.003 per cycle
  - $0.072 - $0.144 per day (48 cycles)
  - ~$2-4 per month

### Asana API

- **Rate Limit**: 1500 requests/minute
- **Free tier**: Unlimited API calls

At 30-minute intervals:
- ~50-100 API calls/day (well within limits)

## Security Best Practices

1. **Protect credentials**:
   ```bash
   chmod 600 config/google_credentials.json
   chmod 600 config/google_token.json
   ```

2. **Rotate tokens** if exposed:
   - Delete `google_token.json`
   - Revoke access in [Google Account Settings](https://myaccount.google.com/permissions)
   - Re-authorize

3. **Review permissions**:
   - Heartbeat only needs read access
   - Never grant write/delete permissions

4. **Monitor logs** for unusual activity:
   ```bash
   grep "Failed\|Error" logs/sentinel.log
   ```

## Next Steps

Once your heartbeat is running:

1. **Monitor for a day** - Check if alerts are useful
2. **Adjust intervals** - Fine-tune based on your needs
3. **Customize priority logic** - Tweak what triggers alerts
4. **Proceed to Phase 4** - Add MCP skills for even more capabilities

---

**Questions?** Check the logs first: `tail -f logs/sentinel.log`
