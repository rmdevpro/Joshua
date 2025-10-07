#!/bin/bash
# Run Docker integration tests from host

set -e

echo "Running Docker Integration Tests..."
echo "===================================="

# Test 1: Container running
if docker ps --filter "name=fiedler-mcp" --format "{{.Status}}" | grep -q "Up"; then
    echo "✓ Container is running"
else
    echo "✗ Container is NOT running"
    exit 1
fi

# Test 2: Container healthy
sleep 5  # Wait for health check
if docker inspect --format='{{.State.Health.Status}}' fiedler-mcp | grep -q "healthy"; then
    echo "✓ Container is healthy"
else
    echo "✗ Container is NOT healthy"
    docker inspect --format='{{.State.Health.Status}}' fiedler-mcp
    exit 1
fi

# Test 3: Environment variables
echo "Checking environment variables..."
docker exec fiedler-mcp env | grep -q "FIEDLER_GEMINI_CLIENT=/app/clients/gemini_client.py" && echo "✓ FIEDLER_GEMINI_CLIENT set"
docker exec fiedler-mcp env | grep -q "FIEDLER_ALLOWED_FILE_ROOTS=/app/allowed_files,/app/fiedler_output" && echo "✓ FIEDLER_ALLOWED_FILE_ROOTS set"
docker exec fiedler-mcp env | grep -q "FIEDLER_SAVE_PROMPT=0" && echo "✓ FIEDLER_SAVE_PROMPT set"

# Test 4: Volumes mounted
docker exec fiedler-mcp ls -d /app/fiedler_output >/dev/null 2>&1 && echo "✓ fiedler_output volume mounted"
docker exec fiedler-mcp ls -d /app/allowed_files >/dev/null 2>&1 && echo "✓ allowed_files volume mounted"
docker exec fiedler-mcp ls /app/clients/gemini_client.py >/dev/null 2>&1 && echo "✓ gemini_client.py mounted"
docker exec fiedler-mcp ls /app/clients/grok_client.py >/dev/null 2>&1 && echo "✓ grok_client.py mounted"

# Test 5: Port exposed
docker port fiedler-mcp | grep -q "9010" && echo "✓ Port 9010 exposed"

# Test 6: Python dependencies
docker exec fiedler-mcp pip list | grep -q "tiktoken" && echo "✓ tiktoken installed"
docker exec fiedler-mcp pip list | grep -q "pydantic" && echo "✓ pydantic installed"

# Test 7: Fiedler module importable
docker exec fiedler-mcp python -c "import fiedler" 2>/dev/null && echo "✓ fiedler module importable"

# Test 8: Restart policy
if docker inspect --format='{{.HostConfig.RestartPolicy.Name}}' fiedler-mcp | grep -q "unless-stopped"; then
    echo "✓ Restart policy: unless-stopped"
else
    echo "✗ Restart policy incorrect"
    exit 1
fi

# Test 9: stdin_open
if docker inspect --format='{{.Config.OpenStdin}}' fiedler-mcp | grep -q "true"; then
    echo "✓ stdin_open: true"
else
    echo "✗ stdin_open not set"
    exit 1
fi

# Test 10: tty
if docker inspect --format='{{.Config.Tty}}' fiedler-mcp | grep -q "true"; then
    echo "✓ tty: true"
else
    echo "✗ tty not set"
    exit 1
fi

echo ""
echo "===================================="
echo "✅ All Docker tests passed!"
echo "===================================="
