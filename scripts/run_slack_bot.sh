#!/bin/bash
# Run the Sentinel Slack Bot

echo "=================================="
echo "Starting Sentinel Slack Bot"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run ./scripts/setup.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Copy .env.template to .env and configure your API keys"
    exit 1
fi

# Activate virtual environment and run bot
source venv/bin/activate
python -m src.adapters.slack_bot

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ Slack bot stopped gracefully"
    echo "=================================="
else
    echo ""
    echo "=================================="
    echo "❌ Slack bot exited with error code $exit_code"
    echo "=================================="
fi

exit $exit_code
