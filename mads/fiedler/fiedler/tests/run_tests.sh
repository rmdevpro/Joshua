#!/bin/bash
# Fiedler MCP Server - Test Suite Runner

set -e

echo "================================"
echo "Fiedler MCP Server Test Suite"
echo "================================"
echo ""

# Check if container is running
if ! docker ps | grep -q fiedler-mcp; then
    echo "❌ ERROR: fiedler-mcp container is not running"
    echo "Start it with: docker compose up -d"
    exit 1
fi

echo "✓ Container is running"
echo ""

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing pytest..."
    pip install pytest
fi

# Change to project root
cd "$(dirname "$0")/.."

echo "Running test suite..."
echo ""

# Run tests with verbose output
pytest tests/ -v --tb=short \
    --color=yes \
    -k "not test_fiedler_send" \
    2>&1 | tee test_results.log

# Check exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "================================"
    echo "✅ All tests passed!"
    echo "================================"
    exit 0
else
    echo ""
    echo "================================"
    echo "❌ Some tests failed"
    echo "================================"
    exit 1
fi
