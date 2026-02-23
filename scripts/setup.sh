#!/bin/bash
# Sentinel Setup Script
# Initializes the development environment

set -e  # Exit on error

echo "=================================="
echo "Sentinel - Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✓ Python $python_version detected"
else
    echo "✗ Python $required_version or higher required"
    echo "  Current version: $python_version"
    exit 1
fi

echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"

echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - SLACK_APP_TOKEN"
    echo "   - And other required credentials"
else
    echo "✓ .env file already exists"
fi

echo ""

# Create necessary directories
echo "Creating directory structure..."
mkdir -p memory/daily
mkdir -p memory/topics
mkdir -p config
mkdir -p logs
mkdir -p .claude/skills
mkdir -p .claude/commands
mkdir -p .claude/rules
echo "✓ Directory structure created"

echo ""

# Validate configuration
echo "Validating configuration..."
python -c "from src.utils.config import config; errors = config.validate(); print('✓ Configuration valid' if not errors else f'⚠️  Config warnings: {errors}')"

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Customize memory files:"
echo "   - memory/soul.md"
echo "   - memory/user.md"
echo "   - memory/agents.md"
echo "3. Run tests: ./scripts/test_phase1.sh"
echo "4. Start building Phase 2!"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
echo ""
