##Slack Setup Guide

Complete guide to setting up the Sentinel Slack bot.

## Prerequisites

- Slack workspace with admin access
- Sentinel installed and configured (Phase 1 complete)
- API keys configured in `.env` file

## Step 1: Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app name: `Sentinel` (or your preferred name)
5. Select your workspace
6. Click **"Create App"**

## Step 2: Configure OAuth & Permissions

1. In the sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** section
3. Add the following **Bot Token Scopes**:

   **Required scopes:**
   - `app_mentions:read` - View messages that directly mention @Sentinel
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic channel information
   - `chat:write` - Send messages as @Sentinel
   - `groups:history` - View messages in private channels
   - `groups:read` - View basic information about private channels
   - `im:history` - View messages in direct messages
   - `im:read` - View basic information about direct messages
   - `im:write` - Start direct messages with people
   - `mpim:history` - View messages in group DMs
   - `mpim:read` - View basic information about group DMs
   - `users:read` - View people in the workspace

4. Click **"Install to Workspace"**
5. Review permissions and click **"Allow"**
6. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   - Save this as `SLACK_BOT_TOKEN` in your `.env` file

## Step 3: Enable Socket Mode

1. In the sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to ON
3. Enter a token name (e.g., "Sentinel App Token")
4. Click **"Generate"**
5. Copy the **App-Level Token** (starts with `xapp-`)
   - Save this as `SLACK_APP_TOKEN` in your `.env` file
6. Click **"Done"**

## Step 4: Subscribe to Events

1. In the sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON
3. Expand **"Subscribe to bot events"**
4. Add the following bot events:
   - `app_mention` - Bot is mentioned in a channel
   - `message.channels` - Message posted in public channel
   - `message.groups` - Message posted in private channel
   - `message.im` - Message posted in DM
   - `message.mpim` - Message posted in group DM
5. Click **"Save Changes"**

## Step 5: Configure App Home

1. In the sidebar, click **"App Home"**
2. Under **"Show Tabs"**, ensure **"Messages Tab"** is enabled
3. Check **"Allow users to send Slash commands and messages from the messages tab"**
4. Optionally customize your bot's display name and icon

## Step 6: Get Signing Secret

1. In the sidebar, click **"Basic Information"**
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**
   - Save this as `SLACK_SIGNING_SECRET` in your `.env` file

## Step 7: Update .env File

Your `.env` file should now have:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_BOT_NAME=Sentinel
SLACK_BOT_EMOJI=:robot_face:
```

## Step 8: Test the Bot

### Start the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Slack bot
python -m src.adapters.slack_bot
```

You should see:
```
============================================================
SENTINEL SLACK BOT
============================================================
Configuration valid - starting bot...
Slack Socket Mode connection established
```

### Test in Slack

1. **In a DM:**
   - Open a DM with @Sentinel
   - Send a message: "Hello!"
   - The bot should respond

2. **In a channel:**
   - Invite @Sentinel to a channel: `/invite @Sentinel`
   - Mention the bot: "@Sentinel what can you do?"
   - The bot should respond

3. **In a thread:**
   - Reply to a message in a thread
   - Mention @Sentinel in the thread
   - The bot maintains context within threads

## Troubleshooting

### Bot doesn't respond

**Check connection:**
```bash
# Look for this in logs
Slack Socket Mode connection established
```

**If not connected:**
- Verify tokens in `.env` are correct
- Check you have Socket Mode enabled
- Ensure all scopes are added

### "Token invalid" error

- Double-check `SLACK_BOT_TOKEN` starts with `xoxb-`
- Double-check `SLACK_APP_TOKEN` starts with `xapp-`
- Reinstall the app to workspace if tokens were regenerated

### Bot invited but can't read messages

- Check bot has `channels:history` scope
- Re-add scopes and reinstall app if needed

### "Missing configuration" errors

```bash
# Validate configuration
python -c "from src.utils.config import config; errors = config.validate(); print(errors if errors else 'Valid')"
```

## Advanced Configuration

### Custom Bot Name

Change in `.env`:
```bash
SLACK_BOT_NAME=YourBotName
SLACK_BOT_EMOJI=:your_emoji:
```

### Claude Model Settings

Adjust in `.env`:
```bash
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
```

### Memory Settings

Configure session limits:
```bash
MEMORY_MAX_SESSION_LENGTH=1000  # Messages before new session
```

## Running in Production

### Using systemd (Linux)

Create `/etc/systemd/system/sentinel.service`:

```ini
[Unit]
Description=Sentinel Slack Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/sentinel
Environment="PATH=/path/to/sentinel/venv/bin"
ExecStart=/path/to/sentinel/venv/bin/python -m src.adapters.slack_bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sentinel
sudo systemctl start sentinel
sudo systemctl status sentinel
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.adapters.slack_bot"]
```

Build and run:
```bash
docker build -t sentinel .
docker run --env-file .env sentinel
```

### Using Screen (Quick Solution)

```bash
# Start in background
screen -S sentinel
source venv/bin/activate
python -m src.adapters.slack_bot

# Detach: Ctrl+A, then D

# Reattach later
screen -r sentinel
```

## Monitoring

### Check Logs

```bash
# Real-time logs
tail -f logs/sentinel.log

# Search for errors
grep ERROR logs/sentinel.log

# Session activity
grep "Session started" logs/sentinel.log
```

### Database Queries

```bash
# Active sessions
sqlite3 memory/sentinel.db "SELECT * FROM sessions WHERE status='active'"

# Recent messages
sqlite3 memory/sentinel.db "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10"

# Conversation stats
sqlite3 memory/sentinel.db "SELECT COUNT(*) as total_messages FROM messages"
```

## Security Best Practices

1. **Never commit tokens to git**
   - `.env` is in `.gitignore`
   - Rotate tokens if exposed

2. **Limit bot permissions**
   - Only add required scopes
   - Review permissions regularly

3. **Monitor usage**
   - Check logs for unusual activity
   - Set up alerts for errors

4. **Secure server**
   - Run bot as non-root user
   - Keep dependencies updated
   - Use firewall rules

## Next Steps

Once your bot is running:

1. **Test conversation memory**
   - Have multi-turn conversations
   - Check `memory/daily/` for logs
   - Verify database has sessions

2. **Customize behavior**
   - Edit system prompt in `slack_bot.py`
   - Adjust response formatting
   - Add custom commands

3. **Proceed to Phase 3**
   - Implement heartbeat monitoring
   - Add proactive notifications
   - Integrate with Gmail, Calendar, Asana

---

**Questions?** Check the logs first: `tail -f logs/sentinel.log`
