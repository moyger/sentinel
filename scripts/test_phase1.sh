#!/bin/bash
# Test Phase 1: Core Memory System

echo "=================================="
echo "Testing Phase 1: Core Memory System"
echo "=================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    echo ""
fi

# Run the test script
python tests/test_memory_system.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ Phase 1 tests PASSED!"
    echo "=================================="
else
    echo ""
    echo "=================================="
    echo "❌ Phase 1 tests FAILED"
    echo "=================================="
fi

exit $exit_code
