#!/bin/bash
# Claudette Test Suite
# Tests all documented functionality of Claudette container
# MUST pass ALL tests before claiming "operational"

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0
CONTAINER_NAME="claude-code-container"

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Test 1: Container is running
test_container_running() {
    log_test "Checking if Claudette container is running..."
    if docker ps --filter "name=${CONTAINER_NAME}" --format '{{.Status}}' | grep -q "Up"; then
        log_pass "Container is running"
        return 0
    else
        log_fail "Container is not running"
        return 1
    fi
}

# Test 2: Claude CLI is installed
test_claude_installed() {
    log_test "Checking if Claude CLI is installed..."
    if docker exec ${CONTAINER_NAME} which claude > /dev/null 2>&1; then
        log_pass "Claude CLI is installed"
        return 0
    else
        log_fail "Claude CLI not found"
        return 1
    fi
}

# Test 3: Claude version check
test_claude_version() {
    log_test "Checking Claude CLI version..."
    VERSION=$(echo "1" | timeout 5 docker exec -i ${CONTAINER_NAME} claude --version 2>&1 || echo "TIMEOUT")
    if [[ "$VERSION" == *"2.0.5"* ]]; then
        log_pass "Claude version: $VERSION"
        return 0
    else
        log_fail "Claude version check failed: $VERSION"
        return 1
    fi
}

# Test 4: Environment variables set
test_env_vars() {
    log_test "Checking environment variables..."

    API_KEY=$(docker exec ${CONTAINER_NAME} env | grep ANTHROPIC_API_KEY | cut -d'=' -f2)
    BASE_URL=$(docker exec ${CONTAINER_NAME} env | grep ANTHROPIC_BASE_URL | cut -d'=' -f2)

    if [[ -n "$API_KEY" ]] && [[ -n "$BASE_URL" ]]; then
        log_pass "Environment variables set (API_KEY, BASE_URL)"
        log_info "BASE_URL: $BASE_URL"
        return 0
    else
        log_fail "Missing environment variables"
        return 1
    fi
}

# Test 5: KGB gateway reachable from container
test_kgb_reachable() {
    log_test "Checking if KGB gateway is reachable..."
    if docker exec ${CONTAINER_NAME} sh -c 'command -v curl > /dev/null && curl -s http://kgb-proxy:8089/health > /dev/null' 2>&1; then
        log_pass "KGB gateway is reachable"
        return 0
    else
        log_fail "KGB gateway not reachable"
        return 1
    fi
}

# Test 6: MCP config exists
test_mcp_config() {
    log_test "Checking MCP configuration..."
    if docker exec ${CONTAINER_NAME} test -f /root/.config/claude-code/claude.json; then
        log_pass "MCP config file exists"

        # Check for sequential-thinking
        if docker exec ${CONTAINER_NAME} grep -q "sequential-thinking" /root/.config/claude-code/claude.json; then
            log_pass "sequential-thinking MCP server configured"
        else
            log_fail "sequential-thinking NOT configured in claude.json"
            return 1
        fi

        # Check for CLAUDE.md
        if docker exec ${CONTAINER_NAME} test -f /root/.config/claude-code/CLAUDE.md; then
            log_pass "CLAUDE.md exists"
        else
            log_fail "CLAUDE.md missing"
            return 1
        fi

        return 0
    else
        log_fail "MCP config file missing"
        return 1
    fi
}

# Test 7: Non-interactive simple prompt (THE CRITICAL TEST)
test_simple_prompt() {
    log_test "Testing non-interactive prompt execution..."
    log_info "This is the critical test - Claude must respond within 30s"

    RESPONSE=$(echo "What is 2+2? Reply with ONLY the number, nothing else." | timeout 30 docker exec -i ${CONTAINER_NAME} claude --print 2>&1 || echo "TIMEOUT")

    if [[ "$RESPONSE" == *"TIMEOUT"* ]]; then
        log_fail "Command timed out after 30s"
        log_info "Response: $RESPONSE"
        return 1
    elif [[ "$RESPONSE" == *"4"* ]]; then
        log_pass "Claude responded correctly: $RESPONSE"
        return 0
    else
        log_fail "Unexpected response: $RESPONSE"
        return 1
    fi
}

# Test 8: Stream JSON output format
test_stream_json() {
    log_test "Testing stream-json output format..."

    RESPONSE=$(echo "test" | timeout 30 docker exec -i ${CONTAINER_NAME} claude --output-format stream-json --verbose --print 2>&1 || echo "TIMEOUT")

    if [[ "$RESPONSE" == *"TIMEOUT"* ]]; then
        log_fail "Stream JSON command timed out"
        return 1
    elif [[ "$RESPONSE" == *'"type"'* ]]; then
        log_pass "Stream JSON format working"
        return 0
    else
        log_fail "Stream JSON not working: $RESPONSE"
        return 1
    fi
}

# Test 9: KGB logging verification
test_kgb_logging() {
    log_test "Testing KGB logging pipeline..."

    # Send a unique test message
    UNIQUE_MSG="CLAUDETTE_TEST_$(date +%s)"
    echo "$UNIQUE_MSG" | timeout 30 docker exec -i ${CONTAINER_NAME} claude --print > /dev/null 2>&1 || true

    sleep 2

    # Check KGB logs for the request
    if docker logs kgb-proxy --since 10s 2>&1 | grep -q "POST /v1/messages"; then
        log_pass "KGB received API request"
        return 0
    else
        log_fail "No requests in KGB logs"
        return 1
    fi
}

# Test 10: Workspace mount
test_workspace_mount() {
    log_test "Testing workspace mount..."

    if docker exec ${CONTAINER_NAME} test -d /mnt/projects; then
        log_pass "Workspace /mnt/projects mounted"
        return 0
    else
        log_fail "Workspace not mounted"
        return 1
    fi
}

# Run all tests
echo "================================"
echo "  CLAUDETTE TEST SUITE"
echo "================================"
echo ""

test_container_running || true
test_claude_installed || true
test_claude_version || true
test_env_vars || true
test_kgb_reachable || true
test_mcp_config || true
test_workspace_mount || true

echo ""
echo "================================"
echo "  CRITICAL TESTS"
echo "================================"
echo ""

test_simple_prompt || true
test_stream_json || true
test_kgb_logging || true

echo ""
echo "================================"
echo "  TEST RESULTS"
echo "================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - Claudette is OPERATIONAL${NC}"
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED - Claudette is NOT operational${NC}"
    echo "Do NOT claim Claudette is working until all tests pass."
    exit 1
fi
