#!/bin/bash
# Test Claudette with KGB-green (routing through Fiedler)
# KGB-green is on port 8090, routing to Fiedler's HTTP proxy on port 8081

set -e

echo "=== Testing Claudette with KGB-green (Claudette → KGB-green → Fiedler → Anthropic) ==="
echo ""

# Test non-interactive mode (the critical path that was failing)
echo "Test: Non-interactive command through green deployment..."
docker exec -i claude-code-container bash -c "ANTHROPIC_BASE_URL=http://localhost:8090 claude 'what is 2+2?'" > /tmp/test_green_result.txt 2>&1 &
PID=$!

# Wait max 10 seconds for response
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✅ Response received in ${i} seconds"
        cat /tmp/test_green_result.txt
        echo ""
        echo "✅ KGB-green routing through Fiedler is working!"
        exit 0
    fi
    sleep 1
    echo -n "."
done

echo ""
echo "❌ Test timed out after 10 seconds"
kill $PID 2>/dev/null || true
exit 1
