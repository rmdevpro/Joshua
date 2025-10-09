# Relay V3.6 Deployment Plan & Testing Suite - REVISED
## Addressing All Critical Issues from Junior Review

---

## IMPORTANT NOTES

### Code Reference Policy
The relay code (`relay_v3.6_updated.py`) in this document is the REFERENCE VERSION from Gemini's original deployment plan. Known issues (logger initialization, file locking) will be fixed DURING IMPLEMENTATION, not in this reference document.

### Issues Addressed in This Revision
1. ✅ **Logger Initialization** - Deployment scripts now set JOSHUA_LOGGER_URL environment variable
2. ✅ **Bare Metal Deployment** - Complete guide with systemd services added
3. ✅ **Health Check Enhancement** - Parameterized health_check.py for testing inactive instances
4. ✅ **File Locking** - Implementation guide included (to be applied during deployment)
5. ✅ **Stress Testing** - Locust-based stress tests added
6. ✅ **Security Documentation** - TLS configuration and security guidelines added

---

## 1. DEPLOYMENT STRATEGY

### Blue/Green Deployment Architecture

#### Phase 1: Container Testing
Test the updated relay in Docker containers before bare metal deployment.

#### Phase 2: Bare Metal Deployment
Deploy to production servers using Blue/Green strategy with zero downtime.

### Container Testing Configuration

**docker-compose.yml**
```yaml
version: '3.8'

services:
  # Blue and Green relay instances
  relay-blue:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: relay-blue
    environment:
      - JOSHUA_LOGGER_URL=ws://godot-mcp:9060  # Fixes logger initialization
      - RELAY_INSTANCE=blue
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config:ro
    networks:
      - relay-net

  relay-green:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: relay-green
    environment:
      - JOSHUA_LOGGER_URL=ws://godot-mcp:9060  # Fixes logger initialization
      - RELAY_INSTANCE=green
    ports:
      - "8001:8000"
    volumes:
      - ./config:/app/config:ro
    networks:
      - relay-net

  # HAProxy for Blue/Green switching
  haproxy:
    image: haproxy:2.8
    container_name: relay-haproxy
    ports:
      - "80:80"
      - "8404:8404"  # Stats page
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    networks:
      - relay-net

  # Mock Godot logger for testing
  godot-mcp:
    image: python:3.10-slim
    container_name: godot-mcp
    command: python /app/mock_godot.py
    volumes:
      - ./tests/fixtures:/app
    ports:
      - "9060:9060"
    networks:
      - relay-net

  # Fiedler backend for LLM integration testing
  fiedler-mcp:
    image: fiedler:latest
    container_name: fiedler-mcp
    ports:
      - "9012:9012"
    volumes:
      - /mnt/irina_storage:/mnt/irina_storage:ro
    networks:
      - relay-net

networks:
  relay-net:
    driver: bridge
```

### Bare Metal Deployment

#### Directory Structure
```
/opt/relay-blue/
  ├── relay_v3.6_updated.py
  ├── requirements.txt
  ├── config/
  │   └── backends.yaml
  └── venv/

/opt/relay-green/
  ├── relay_v3.6_updated.py
  ├── requirements.txt
  ├── config/
  │   └── backends.yaml
  └── venv/

/opt/relay-active -> /opt/relay-blue  (symlink to active version)
```

#### Systemd Service Files

**/etc/systemd/system/relay-blue.service**
```ini
[Unit]
Description=MCP Relay (Blue Instance)
After=network.target

[Service]
Type=simple
User=relay
Group=relay
WorkingDirectory=/opt/relay-blue
Environment="JOSHUA_LOGGER_URL=ws://godot-mcp:9060"
Environment="RELAY_PORT=8000"
ExecStartPre=/opt/relay-blue/venv/bin/python -c "from joshua_logger import Logger; Logger()"
ExecStart=/opt/relay-blue/venv/bin/python relay_v3.6_updated.py --config config/backends.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/relay-green.service**
```ini
[Unit]
Description=MCP Relay (Green Instance)
After=network.target

[Service]
Type=simple
User=relay
Group=relay
WorkingDirectory=/opt/relay-green
Environment="JOSHUA_LOGGER_URL=ws://godot-mcp:9060"
Environment="RELAY_PORT=8001"
ExecStartPre=/opt/relay-green/venv/bin/python -c "from joshua_logger import Logger; Logger()"
ExecStart=/opt/relay-green/venv/bin/python relay_v3.6_updated.py --config config/backends.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Deployment Scripts

**deploy.sh** (Enhanced with proper health checking)
```bash
#!/bin/bash
set -e

# Configuration
BLUE_DIR="/opt/relay-blue"
GREEN_DIR="/opt/relay-green"
BLUE_PORT=8000
GREEN_PORT=8001
HEALTH_CHECK_SCRIPT="/opt/relay-tools/health_check.py"

# Determine active/inactive
CURRENT_ACTIVE=$(readlink /opt/relay-active)
if [ "$CURRENT_ACTIVE" = "$BLUE_DIR" ]; then
    INACTIVE_DIR=$GREEN_DIR
    INACTIVE_SERVICE="relay-green"
    INACTIVE_PORT=$GREEN_PORT
    ACTIVE_SERVICE="relay-blue"
else
    INACTIVE_DIR=$BLUE_DIR
    INACTIVE_SERVICE="relay-blue"
    INACTIVE_PORT=$BLUE_PORT
    ACTIVE_SERVICE="relay-green"
fi

echo "Deploying to inactive instance: $INACTIVE_DIR"

# Deploy new code
cd $INACTIVE_DIR
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Start inactive instance
sudo systemctl start $INACTIVE_SERVICE

# Health check against INACTIVE instance (critical fix)
echo "Running health check on port $INACTIVE_PORT..."
python3 $HEALTH_CHECK_SCRIPT --host localhost --port $INACTIVE_PORT
if [ $? -ne 0 ]; then
    echo "Health check failed! Rolling back..."
    sudo systemctl stop $INACTIVE_SERVICE
    exit 1
fi

# Switch HAProxy backend
echo "Switching traffic to new instance..."
# Update HAProxy config or use runtime API
echo "enable server backend/$INACTIVE_SERVICE" | sudo socat stdio /var/run/haproxy/admin.sock
echo "disable server backend/$ACTIVE_SERVICE" | sudo socat stdio /var/run/haproxy/admin.sock

# Update symlink
sudo ln -sfn $INACTIVE_DIR /opt/relay-active

# Stop old instance
sudo systemctl stop $ACTIVE_SERVICE

echo "Deployment complete!"
```

---

## 2. TESTING SUITE

### Test Categories

#### A. Library Integration Tests
**test_libraries_integration.py**
```python
import pytest
from fixtures.mock_claude import MockClaude

@pytest.mark.asyncio
async def test_relay_uses_joshua_logger():
    """Verify logs are sent through joshua_logger."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    # Trigger a tool call that generates logs
    response = await claude.call_tool("relay_get_status", {})

    # Check Godot received the logs
    godot_logs = get_godot_logs()
    assert "mcp-relay" in godot_logs
    assert "Tool call received" in godot_logs

@pytest.mark.asyncio
async def test_relay_uses_joshua_network():
    """Verify relay uses joshua_network.Client for backends."""
    # Test connection handling, reconnection, etc.
    pass
```

#### B. Fiedler LLM Integration Tests (CRITICAL)
**test_fiedler_integration.py**
```python
@pytest.mark.asyncio
async def test_fiedler_simple_query():
    """Test simple LLM query through relay."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    response = await claude.call_tool("fiedler_send", {
        "models": ["gpt-4o"],
        "prompt": "What is 2+2?"
    })

    assert "result" in response
    assert response["result"]["status"] == "success"

@pytest.mark.asyncio
async def test_fiedler_large_document():
    """Test large document processing."""
    test_file = "/mnt/irina_storage/test_large.md"
    Path(test_file).write_text("Large content " * 10000)

    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    response = await claude.call_tool("fiedler_send", {
        "models": ["gemini-2.5-pro"],
        "prompt": "Summarize this document",
        "files": [test_file]
    })

    assert "result" in response
    assert len(response["result"]["output_file"]) > 0

@pytest.mark.asyncio
async def test_fiedler_parallel_models():
    """Test multiple models in parallel."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    response = await claude.call_tool("fiedler_send", {
        "models": ["gpt-4o", "gemini-2.5-pro", "deepseek"],
        "prompt": "Explain quantum computing in one sentence"
    })

    assert response["result"]["results"]
    assert len(response["result"]["results"]) == 3

@pytest.mark.asyncio
async def test_fiedler_error_handling():
    """Test error handling for invalid models."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    response = await claude.call_tool("fiedler_send", {
        "models": ["invalid-model"],
        "prompt": "This should fail"
    })

    assert "error" in response

@pytest.mark.asyncio
async def test_connection_recovery_during_llm_call():
    """Test relay recovers if backend disconnects during LLM call."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    # Start LLM call
    task = asyncio.create_task(claude.call_tool("fiedler_send", {
        "models": ["gpt-4o"],
        "prompt": "Long running task"
    }))

    # Kill and restart backend
    await asyncio.sleep(1)
    docker_compose.restart("fiedler-mcp")

    # Should still complete
    response = await task
    assert "result" in response
```

#### C. Stress Testing (NEW)
**test_stress.py**
```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def stress_test_concurrent_requests():
    """Test 1000+ concurrent requests as required."""
    NUM_CLIENTS = 1000

    async def make_request(client_id):
        claude = MockClaude()
        await claude.connect()
        await claude.initialize()

        start = time.time()
        response = await claude.call_tool("relay_get_status", {})
        duration = time.time() - start

        await claude.disconnect()
        return {"client_id": client_id, "duration": duration, "success": "result" in response}

    # Create all tasks
    tasks = [make_request(i) for i in range(NUM_CLIENTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analyze results
    successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    avg_duration = sum(r["duration"] for r in results if isinstance(r, dict)) / successes

    assert successes >= NUM_CLIENTS * 0.99  # 99% success rate
    assert avg_duration < 2.0  # Average response under 2 seconds
    print(f"Stress test: {successes}/{NUM_CLIENTS} succeeded, avg {avg_duration:.2f}s")

def test_memory_under_load():
    """Monitor memory usage during sustained load."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Run stress test
    asyncio.run(stress_test_concurrent_requests())

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    assert memory_increase < 500  # Less than 500MB increase
    print(f"Memory: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
```

#### D. Security Tests (NEW)
**test_security.py**
```python
@pytest.mark.asyncio
async def test_tls_connection():
    """Verify TLS is properly configured."""
    claude = MockClaude(url="wss://localhost:443")  # WSS for TLS
    await claude.connect()

    # Verify certificate
    assert claude.websocket.ssl_context is not None

@pytest.mark.asyncio
async def test_authentication_required():
    """Verify authentication is enforced."""
    claude = MockClaude()
    claude.set_auth_token("")  # No token

    with pytest.raises(ConnectionRefusedError):
        await claude.connect()

@pytest.mark.asyncio
async def test_rate_limiting():
    """Verify rate limiting is enforced."""
    claude = MockClaude()
    await claude.connect()
    await claude.initialize()

    # Spam requests
    for i in range(100):
        response = await claude.call_tool("relay_get_status", {})
        if "error" in response and "rate limit" in response["error"]:
            break
    else:
        pytest.fail("Rate limiting not enforced")
```

---

## 3. HEALTH CHECK (Enhanced)

**health_check.py**
```python
#!/usr/bin/env python3
import asyncio
import json
import sys
import argparse

async def check_health(host, port, timeout=5):
    """Check relay health on specified host:port."""
    try:
        reader, writer = await asyncio.open_connection(host, port)

        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"clientInfo": {"name": "health-check"}},
            "id": 1
        }
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        # Read response with timeout
        data = await asyncio.wait_for(reader.readline(), timeout=timeout)
        response = json.loads(data.decode())

        if response.get("result", {}).get("serverInfo"):
            print(f"✅ Health check PASSED for {host}:{port}")
            print(f"   Server: {response['result']['serverInfo']}")

            # Test tool listing
            list_req = {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
            writer.write((json.dumps(list_req) + '\n').encode())
            await writer.drain()

            data = await asyncio.wait_for(reader.readline(), timeout=timeout)
            tools_response = json.loads(data.decode())

            tool_count = len(tools_response.get("result", {}).get("tools", []))
            print(f"   Tools: {tool_count} available")

            writer.close()
            await writer.wait_closed()
            return True
        else:
            print(f"❌ Health check FAILED for {host}:{port}")
            print(f"   Invalid response: {response}")
            return False

    except asyncio.TimeoutError:
        print(f"❌ Health check TIMEOUT for {host}:{port}")
        return False
    except Exception as e:
        print(f"❌ Health check ERROR for {host}:{port}: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    result = asyncio.run(check_health(args.host, args.port, args.timeout))
    sys.exit(0 if result else 1)
```

---

## 4. SECURITY CONFIGURATION (NEW)

### TLS Configuration

**haproxy.cfg** (with TLS termination)
```
global
    ssl-default-bind-ciphers ECDHE+AESGCM:ECDHE+AES256:!aNULL:!MD5:!DSS
    ssl-default-bind-options ssl-min-ver TLSv1.2

frontend relay_frontend
    bind *:443 ssl crt /etc/ssl/certs/relay.pem
    mode tcp
    default_backend relay_backend

backend relay_backend
    mode tcp
    balance roundrobin
    server blue localhost:8000 check
    server green localhost:8001 check backup
```

### Authentication & Authorization

**Environment Variables**
```bash
# In systemd service files
Environment="RELAY_AUTH_TOKEN=<secure-token>"
Environment="RELAY_AUTH_ENABLED=true"
Environment="RELAY_RATE_LIMIT=100"  # Requests per minute
```

### Security Checklist
- ✅ TLS 1.2+ only
- ✅ Strong cipher suites
- ✅ Authentication tokens required
- ✅ Rate limiting enabled
- ✅ Separate user for relay service
- ✅ Read-only config mounts in containers
- ✅ Network segmentation (relay-net)
- ✅ Logging all authentication attempts

---

## 5. MONITORING & ALERTING

### Metrics to Monitor
- Connection count
- Request latency (p50, p95, p99)
- Error rate
- Memory usage
- CPU usage
- Backend health status

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'relay'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### Alert Rules
```yaml
groups:
  - name: relay_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(relay_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: BackendDown
        expr: relay_backend_health == 0
        for: 2m
        annotations:
          summary: "Backend {{ $labels.backend }} is down"
```

---

## 6. IMPLEMENTATION NOTES

### Known Issues to Fix During Implementation

1. **Logger Initialization in Relay Code**
   ```python
   # Add to MCPRelay.__init__():
   from joshua_logger import Logger
   self.joshua_logger = Logger(url=os.getenv("JOSHUA_LOGGER_URL"))
   # Replace all 'joshua_logger' with 'self.joshua_logger'
   ```

2. **File Locking for backends.yaml**
   ```python
   import fcntl
   # In save_backends_to_yaml():
   with open(temp_file, 'w') as f:
       fcntl.flock(f.fileno(), fcntl.LOCK_EX)
       yaml.dump(config, f)
       fcntl.flock(f.fileno(), fcntl.LOCK_UN)
   ```

### Pre-Deployment Checklist
- [ ] Logger initialization code added
- [ ] File locking implemented
- [ ] Environment variables configured
- [ ] TLS certificates installed
- [ ] Authentication tokens generated
- [ ] Monitoring configured
- [ ] All tests passing
- [ ] Stress test completed
- [ ] Security scan completed

---

## 7. ROLLBACK PROCEDURE

**rollback.sh**
```bash
#!/bin/bash
set -e

CURRENT_ACTIVE=$(readlink /opt/relay-active)

if [ "$CURRENT_ACTIVE" = "/opt/relay-blue" ]; then
    ROLLBACK_TO="/opt/relay-green"
    ROLLBACK_SERVICE="relay-green"
    CURRENT_SERVICE="relay-blue"
else
    ROLLBACK_TO="/opt/relay-blue"
    ROLLBACK_SERVICE="relay-blue"
    CURRENT_SERVICE="relay-green"
fi

echo "Rolling back to: $ROLLBACK_TO"

# Health check old version first
python3 /opt/relay-tools/health_check.py --host localhost --port $([ "$ROLLBACK_SERVICE" = "relay-blue" ] && echo "8000" || echo "8001")
if [ $? -ne 0 ]; then
    echo "ERROR: Rollback target is not healthy!"
    exit 1
fi

# Switch traffic
echo "enable server backend/$ROLLBACK_SERVICE" | sudo socat stdio /var/run/haproxy/admin.sock
echo "disable server backend/$CURRENT_SERVICE" | sudo socat stdio /var/run/haproxy/admin.sock

# Update symlink
sudo ln -sfn $ROLLBACK_TO /opt/relay-active

# Stop current
sudo systemctl stop $CURRENT_SERVICE

echo "Rollback complete!"
```

---

## END OF DEPLOYMENT PLAN & TESTING SUITE

This revised plan addresses all critical issues identified by the juniors while maintaining the original relay code as reference only.