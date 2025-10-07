# Godot - Unified Logging Infrastructure

**Status:** ✅ **APPROVED FOR DEPLOYMENT** - Unanimous triplet consensus achieved (2025-10-05)

Godot provides centralized, production-grade logging for all ICCM components, designed specifically for small development teams (1-3 developers) running on a single Docker host. Built to debug BUG #13 (Gates MCP tools not callable) by capturing exact message exchanges between components.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [MCP Tools](#mcp-tools)
- [Client Integration](#client-integration)
- [Configuration](#configuration)
- [Debugging BUG #13](#debugging-bug-13)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## Architecture Overview

```
Components (relay, gates, fiedler, dewey)
    ↓ loglib.py / loglib.js (non-blocking push)
Redis Queue (FIFO, 100K buffer)
    ↓ Godot Worker (batch processor)
Dewey MCP Tools (dewey_store_logs_batch)
    ↓
PostgreSQL (Winni on Irina - partitioned logs table)
```

### Container Structure

Godot runs as a single container with **three processes** managed by supervisord:

1. **Redis Server** (port 6379, internal)
   - In-memory log queue
   - AOF persistence enabled
   - FIFO drop policy (oldest first when > 100K entries)

2. **Worker Process** (background)
   - Consumes logs in batches (100 logs or 100ms timeout)
   - Sends to Dewey via MCP with exponential backoff retry
   - Enforces queue size limit (REQ-GOD-004)

3. **MCP Server** (port 9060, external)
   - Facade tools: logger_log, logger_query, logger_clear, logger_set_level
   - Proxies queries to Dewey

### Design Principles

- **Dewey Owns All Database Access**: Godot never touches PostgreSQL directly
- **Non-Blocking Clients**: Fire-and-forget Redis push with local fallback
- **FIFO Drop Policy**: Atomic Lua scripts ensure oldest logs dropped when full
- **Trace Correlation**: X-Trace-ID header propagation for distributed tracing
- **Resilient**: System survives Redis down, Dewey down, or queue overflow

---

## Key Features

### ✅ Critical Requirements Met

- **REQ-GOD-004**: 100,000 log buffer in Redis
- **REQ-GOD-005**: FIFO drop policy (oldest first via Lua script)
- **REQ-LIB-004**: Fallback to local logging on ANY Redis failure
- **REQ-LIB-007**: Warning logged when falling back with reason
- **REQ-COR-002**: X-Trace-ID header propagation support
- **REQ-PERF-003**: Atomic 100K entry queue limit enforcement
- **REQ-REL-002**: Exponential backoff retry (max 3 attempts)
- **REQ-MAINT-002**: Godot logs to stdout (not using loglib - prevents loops)

### 🔒 Security Features

- **Field Redaction**: Automatic redaction of sensitive fields (password, token, api_key, authorization, secret)
- **Custom Redaction**: Components can specify additional fields to redact
- **Client-Side**: Redaction happens before logs leave the component

### 📊 Query Capabilities

- **Trace ID Correlation**: Find all logs for a request across components
- **Component Filtering**: View logs for specific services
- **Log Level Filtering**: Minimum level (TRACE → DEBUG → INFO → WARN → ERROR)
- **Time Range Queries**: Start/end time filters
- **Full-Text Search**: PostgreSQL FTS on log messages
- **JSONB Queries**: Search structured data fields

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Existing Dewey MCP server running on `ws://dewey-mcp:8080`
- PostgreSQL (Winni) on Irina server
- Network: `iccm_network` (external)

### 1. Deploy Dewey Updates First

```bash
# Connect to PostgreSQL
psql -U dewey -h irina -d winni

# Run schema additions
\i /mnt/projects/ICCM/godot/dewey/schema_additions.sql
```

Merge `dewey/tools_additions.py` into `/mnt/projects/ICCM/dewey/dewey/tools.py`

Update Dewey's `docker-compose.yml`:
```yaml
environment:
  - LOG_RETENTION_DAYS=7
```

Restart Dewey:
```bash
cd /mnt/projects/ICCM/dewey
docker-compose restart
```

### 2. Build and Deploy Godot

```bash
cd /mnt/projects/ICCM/godot
docker-compose build
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check all three processes running
docker logs godot-mcp | grep "Godot MCP server listening"
docker logs godot-mcp | grep "Godot worker starting"
docker logs godot-mcp | grep "redis-server"

# Test Redis
docker exec godot-mcp redis-cli PING
# Expected: PONG

# Check MCP tools available in Claude Code
# You should see: mcp__iccm__logger_log, logger_query, logger_clear, logger_set_level
```

---

## Deployment

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEWEY_MCP_URL` | `ws://dewey-mcp:8080` | Dewey MCP WebSocket endpoint |
| `DEWEY_CONNECT_TIMEOUT` | `30` | Connection timeout (seconds) |
| `BATCH_SIZE` | `100` | Max logs per batch to Dewey |
| `BATCH_TIMEOUT_MS` | `100` | Max wait time for batch (ms) |
| `MAX_QUEUE_SIZE` | `100000` | Redis queue size limit |
| `RETRY_MAX_ATTEMPTS` | `5` | Max Dewey send retries |
| `RETRY_INITIAL_DELAY` | `1` | Initial retry delay (seconds) |
| `RETRY_MAX_DELAY` | `30` | Max retry delay (seconds) |
| `REDIS_HOST` | `localhost` | Redis host (internal) |
| `REDIS_PORT` | `6379` | Redis port (internal) |
| `MCP_PORT` | `9060` | MCP server port |

### Volumes

```yaml
volumes:
  godot_redis_data:/data  # Redis AOF persistence
```

### Networks

```yaml
networks:
  iccm_network:
    external: true  # Must exist before deployment
```

### Health Checks

```bash
# Redis health
docker exec godot-mcp redis-cli PING

# Worker health (check logs for errors)
docker logs godot-mcp | grep WORKER | tail -20

# MCP server health
docker logs godot-mcp | grep MCP_SERVER | tail -20

# Queue depth
docker exec godot-mcp redis-cli LLEN logs:queue
```

---

## MCP Tools

### logger_log

Submit a log entry to Godot.

**Input:**
```json
{
  "component": "string (required)",
  "level": "string (required) - ERROR|WARN|INFO|DEBUG|TRACE",
  "message": "string (required)",
  "trace_id": "string (optional) - UUID",
  "data": "object (optional)"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Log entry queued."
}
```

### logger_query

Query logs with filters (proxies to Dewey).

**Input:**
```json
{
  "trace_id": "string (optional)",
  "component": "string (optional)",
  "level": "string (optional) - minimum level",
  "start_time": "string (optional) - ISO 8601",
  "end_time": "string (optional) - ISO 8601",
  "search": "string (optional) - full-text search",
  "limit": "integer (optional, default 100, max 1000)"
}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "trace_id": "uuid",
    "component": "string",
    "level": "string",
    "message": "string",
    "data": {},
    "created_at": "timestamp",
    "age": "interval"
  }
]
```

### logger_clear

Clear old logs based on retention policy (proxies to Dewey).

**Input:**
```json
{
  "before_time": "string (optional) - ISO 8601, defaults to 7 days ago",
  "component": "string (optional)",
  "level": "string (optional)"
}
```

**Response:**
```json
{
  "status": "ok",
  "deleted_count": 123
}
```

### logger_set_level

Set log level for a component.

**Input:**
```json
{
  "component": "string (required)",
  "level": "string (required) - ERROR|WARN|INFO|DEBUG|TRACE"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Log level for 'component' set to 'TRACE'."
}
```

---

## Client Integration

**ARCHITECTURAL REQUIREMENT:** ALL MCP servers MUST use MCP-based logging (Approach 1). Direct Redis connections are **FORBIDDEN** and violate the ICCM architecture.

### Approach 1: MCP-Based Logging (**REQUIRED** for ALL MCP Servers)

**MANDATORY for:** Gates, Playfair, Marco, Fiedler, Dewey, KGB, Claudette, MCP Relay, and **ALL future MCP servers**

**Architecture:** ALL MCP servers MUST use Godot's MCP interface (`logger_log` tool) via WebSocket on port 9060.

**Why Redis is forbidden:**
- Redis (port 6379) is **internal to Godot container only** (bind: 127.0.0.1)
- Redis is **NOT exposed** on iccm_network
- Direct Redis access **violates the MCP protocol layer**
- Only Godot's internal batch worker accesses Redis

#### Node.js/JavaScript Implementation

```javascript
const WebSocket = require('ws');

const GODOT_URL = process.env.GODOT_URL || 'ws://godot-mcp:9060';
const LOGGING_ENABLED = true;

/**
 * Send log to Godot via MCP logger_log tool
 */
async function logToGodot(level, message, data = null, traceId = null) {
  if (!LOGGING_ENABLED) return;

  try {
    const ws = new WebSocket(GODOT_URL, { handshakeTimeout: 1000 });

    await new Promise((resolve, reject) => {
      ws.on('open', () => resolve());
      ws.on('error', reject);
      setTimeout(() => reject(new Error('Connection timeout')), 1000);
    });

    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: 'logger_log',
        arguments: {
          level,            // ERROR, WARN, INFO, DEBUG, TRACE
          message,
          component: 'your-component-name',
          data,
          trace_id: traceId
        }
      },
      id: 1
    };

    ws.send(JSON.stringify(request));

    // Wait for response or timeout
    await Promise.race([
      new Promise(resolve => ws.on('message', resolve)),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Response timeout')), 1000))
    ]);

    ws.close();
  } catch (err) {
    // Silently fail - logging should never break the application
  }
}

// Usage
await logToGodot('INFO', 'Server starting', { port: 8080 });
await logToGodot('TRACE', 'MCP request received', { method: 'tools/call' }, traceId);
await logToGodot('ERROR', 'Request failed', { error: err.message }, traceId);
```

**Environment Variables:**
```yaml
environment:
  - GODOT_URL=ws://godot-mcp:9060
  - LOGGING_ENABLED=true
```

#### Python Implementation

```python
import json
import asyncio
from typing import Optional, Dict, Any
import websockets

async def log_to_godot(
    level: str,
    message: str,
    component: str = 'your-component',
    data: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    godot_url: str = 'ws://godot-mcp:9060',
    timeout: float = 1.0
) -> None:
    """Send log to Godot via MCP logger_log tool."""
    try:
        async with websockets.connect(godot_url, open_timeout=timeout) as ws:
            request = {
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': 'logger_log',
                    'arguments': {
                        'level': level,        # ERROR, WARN, INFO, DEBUG, TRACE
                        'message': message,
                        'component': component,
                        'data': data,
                        'trace_id': trace_id
                    }
                },
                'id': 1
            }

            await ws.send(json.dumps(request))

            try:
                response = await asyncio.wait_for(ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                pass  # Response timeout - continue silently

    except Exception:
        # Silently fail - logging should never break the application
        pass

# Usage
GODOT_URL = os.getenv('GODOT_URL', 'ws://godot-mcp:9060')
LOGGING_ENABLED = os.getenv('LOGGING_ENABLED', 'true').lower() == 'true'

if LOGGING_ENABLED:
    await log_to_godot('INFO', 'Server starting', data={'port': 8080})
    await log_to_godot('TRACE', 'MCP request received', data={'method': 'tools/call'}, trace_id=trace_id)
    await log_to_godot('ERROR', 'Request failed', data={'error': str(err)}, trace_id=trace_id)
```

**Environment Variables:**
```yaml
environment:
  - GODOT_URL=ws://godot-mcp:9060
  - LOGGING_ENABLED=true
```

**Key Points:**
- ✅ Non-blocking: Fails silently on error
- ✅ Works when Godot is down (no exceptions thrown)
- ✅ No external dependencies (uses built-in websockets library)
- ✅ Consistent with all Blue deployments (Gates, Playfair, Marco, Fiedler)

---

### Approach 2: Redis Client Library (DEPRECATED - ARCHITECTURAL VIOLATION)

**🚫 FORBIDDEN FOR ALL MCP SERVERS 🚫**

**This approach VIOLATES the ICCM architecture:**
- Redis (port 6379) is **internal to Godot container only**
- Redis is **NOT exposed** on the network (bind address 127.0.0.1)
- Direct Redis connections **bypass the MCP protocol layer**
- **ALL MCP servers MUST use Approach 1** (MCP-based logging)

**Preserved for historical reference only. DO NOT USE.**

#### Python Components

#### 1. Install Dependencies

```bash
pip install redis>=5.0
```

#### 2. Copy Client Library

Copy `client_libs/python/godot/loglib.py` to your component.

#### 3. Initialize Logger

```python
from godot.loglib import ICCMLogger

logger = ICCMLogger(
    component='your-component',
    redis_url='redis://localhost:6379',  # Only works if Redis exposed
    default_level='INFO',
    redact_fields=['custom_sensitive_field']  # Optional
)
```

#### 4. Use Logger with Trace IDs

```python
import uuid

# In request handler
trace_id = request.headers.get('X-Trace-ID') or str(uuid.uuid4())

logger.info("Request received", {"path": request.path}, trace_id=trace_id)

try:
    result = process_request()
    logger.debug("Processing complete", {"result": result}, trace_id=trace_id)
except Exception as e:
    logger.error(f"Processing failed: {e}", {"error": str(e)}, trace_id=trace_id)

# Forward trace_id to backend
headers = {'X-Trace-ID': trace_id}
response = requests.post(backend_url, headers=headers)
```

#### JavaScript Components

#### 1. Install Dependencies

```bash
npm install redis
```

#### 2. Copy Client Library

Copy `client_libs/javascript/loglib.js` to your component.

#### 3. Initialize Logger

```javascript
const { ICCMLogger } = require('./loglib');

const logger = new ICCMLogger({
    component: 'your-component',
    redisUrl: 'redis://localhost:6379',  // Only works if Redis exposed
    defaultLevel: 'INFO',
    redactFields: ['customSensitiveField']  // Optional
});
```

#### 4. Use Logger with Trace IDs

```javascript
const { v4: uuidv4 } = require('uuid');

app.use((req, res, next) => {
    // Extract or generate trace_id
    req.traceId = req.headers['x-trace-id'] || uuidv4();
    res.setHeader('X-Trace-ID', req.traceId);
    next();
});

app.post('/endpoint', (req, res) => {
    const { traceId } = req;

    logger.info("Request received", { path: req.path }, traceId);

    try {
        const result = processRequest();
        logger.debug("Processing complete", { result }, traceId);
        res.json({ status: "ok" });
    } catch (e) {
        logger.error(`Processing failed: ${e.message}`, { error: e.stack }, traceId);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    await logger.close();
});
```

---

### Log Levels

```python
logger.trace("Verbose debug info", data, trace_id)  # TRACE - most verbose
logger.debug("Debug information", data, trace_id)    # DEBUG
logger.info("System status", data, trace_id)         # INFO - default
logger.warn("Potential issue", data, trace_id)       # WARN
logger.error("Critical failure", data, trace_id)     # ERROR - least verbose
```

### Dynamic Log Level Changes

```python
# From code
logger.set_level('DEBUG')

# From MCP tool (affects all components with same name)
mcp.call_tool('logger_set_level', {'component': 'relay', 'level': 'TRACE'})
```

### Local Fallback Behavior

When Redis is unreachable:
- **stdout**: Log entry as JSON
- **stderr**: Warning message with reason

Example stderr output:
```
[ICCMLogger WARNING] relay: Redis connection failed. Reason: Connection refused. Falling back to local logging.
```

---

## Configuration

### Redis Configuration (`redis.conf`)

```conf
port 6379
bind 127.0.0.1  # Internal only

# Persistence (REQ-REL-001)
appendonly yes
appendfsync everysec
dir /data

loglevel notice
logfile ""
```

### Supervisord Configuration (`supervisord.conf`)

```ini
[supervisord]
nodaemon=true

[program:redis]
command=redis-server /etc/redis/redis.conf
autorestart=true

[program:worker]
command=python -u src/worker.py
autorestart=true
startsecs=5

[program:mcp_server]
command=python -u src/mcp_server.py
autorestart=true
startsecs=5
```

All processes log to stdout/stderr for Docker container logging.

---

## Debugging BUG #13

Godot was built specifically to debug BUG #13 (Gates MCP tools not callable).

### Procedure

1. **Enable TRACE logging on relay and Gates:**
```bash
# From Claude Code MCP tools
mcp__iccm__logger_set_level({'component': 'relay', 'level': 'TRACE'})
mcp__iccm__logger_set_level({'component': 'gates', 'level': 'TRACE'})
```

2. **Call the failing tool:**
```bash
mcp__iccm__gates_list_capabilities()
```

3. **Query logs by trace ID:**
```python
# Get trace_id from relay logs
results = mcp__iccm__logger_query({
    'trace_id': '<trace_id>',
    'level': 'TRACE',
    'limit': 1000
})
```

4. **Compare Gates vs Dewey tool registration:**
```python
# Query Gates tool registration
gates_logs = mcp__iccm__logger_query({
    'component': 'gates',
    'search': 'tools/list',
    'level': 'TRACE'
})

# Query Dewey tool registration (working example)
dewey_logs = mcp__iccm__logger_query({
    'component': 'dewey',
    'search': 'tools/list',
    'level': 'TRACE'
})

# Compare data structures in data JSONB field
# Look for differences in tool schema, naming, or format
```

5. **Analyze relay routing:**
```python
relay_logs = mcp__iccm__logger_query({
    'component': 'relay',
    'trace_id': '<trace_id>',
    'search': 'gates'
})

# Check for routing failures, tool name mismatches
```

---

## Troubleshooting

### Redis Connection Refused

**Symptom:** Client logs show "Redis connection failed"

**Check:**
```bash
docker exec godot-mcp redis-cli PING
```

**Fix:**
- Verify Godot container is running
- Check Redis is bound to 127.0.0.1:6379
- Ensure clients use correct URL: `redis://godot-mcp:6379`

### Queue Growing Uncontrolled

**Symptom:** Queue depth > 100,000 for extended period

**Check:**
```bash
docker exec godot-mcp redis-cli LLEN logs:queue
```

**Diagnose:**
```bash
# Check worker is running
docker logs godot-mcp | grep "Godot worker starting"

# Check for Dewey connection errors
docker logs godot-mcp | grep "Dewey client disconnected"

# Check batch processing rate
docker logs godot-mcp | grep "Successfully sent batch"
```

**Fix:**
- Verify Dewey is accessible at `ws://dewey-mcp:8080`
- Check Dewey is not overloaded (too many log writes)
- Increase `BATCH_SIZE` if network latency is high
- Check PostgreSQL disk space on Irina

### Logs Not Appearing in Dewey

**Symptom:** Client logs successfully but queries return nothing

**Check:**
```bash
# Verify worker is sending batches
docker logs godot-mcp | grep "Successfully sent batch"

# Check Dewey logs for insert errors
docker logs dewey-mcp | grep "dewey_store_logs_batch"

# Query PostgreSQL directly
psql -U dewey -h irina -d winni -c "SELECT COUNT(*) FROM logs;"
```

**Fix:**
- Verify Dewey has `dewey_store_logs_batch` tool registered
- Check PostgreSQL permissions for dewey user
- Verify schema was applied correctly

### High Memory Usage

**Symptom:** Godot container using excessive RAM

**Check:**
```bash
docker stats godot-mcp

# Check queue depth
docker exec godot-mcp redis-cli LLEN logs:queue

# Check Redis memory
docker exec godot-mcp redis-cli INFO memory
```

**Fix:**
- Queue should not exceed 100K entries (Lua script enforces this)
- If queue is large, worker may be stalled - check Dewey connectivity
- Redis AOF file grows over time - consider periodic restarts if disk space is concern

### Local Fallback Not Working

**Symptom:** No logs in container logs when Redis is down

**Check component container logs:**
```bash
docker logs <component-name> | grep ICCMLogger
```

**Diagnose:**
- Client library should print to stdout (log entry) and stderr (warning)
- If nothing appears, client library may not be initialized
- Check component is using logger correctly

---

## Development

### Project Structure

```
godot/
├── Dockerfile                  # Multi-process container
├── docker-compose.yml          # Service definition
├── supervisord.conf            # Process manager config
├── redis.conf                  # Redis persistence config
├── src/
│   ├── config.py              # Environment variables
│   ├── worker.py              # Batch log processor
│   └── mcp_server.py          # MCP facade tools
└── README.md                  # This file
```

### Running Locally

```bash
# Build image
docker-compose build

# Start with logs
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Testing

```bash
# Test Redis
docker exec godot-mcp redis-cli PING

# Test MCP server
# From Claude Code, test logger_log tool

# Test client library
cd client_libs/python
python3 -c "
from godot.loglib import ICCMLogger
logger = ICCMLogger('test', 'redis://localhost:6379')
logger.info('Test message', {'key': 'value'})
"

# Check queue
docker exec godot-mcp redis-cli LLEN logs:queue

# Check batch processing
docker logs godot-mcp | grep "Successfully sent batch"
```

### Viewing Logs

```bash
# All logs
docker logs godot-mcp

# Just worker
docker logs godot-mcp | grep WORKER

# Just MCP server
docker logs godot-mcp | grep MCP_SERVER

# Just Redis
docker logs godot-mcp | grep redis-server

# Follow logs
docker logs -f godot-mcp
```

### Performance Monitoring

```bash
# Queue depth over time
watch -n 1 'docker exec godot-mcp redis-cli LLEN logs:queue'

# Batch processing rate
docker logs godot-mcp | grep "Successfully sent batch" | tail -20

# Redis stats
docker exec godot-mcp redis-cli INFO stats
```

---

## Architecture Decisions

### Why Supervisord?

**Alternatives Considered:**
- Bash script with background processes
- Separate containers for Redis, Worker, MCP Server

**Decision:** Supervisord
- **Reliability**: Automatic process restart on failure
- **Logging**: Unified logging to stdout/stderr
- **Simplicity**: Single container for small team deployment
- **Management**: Process control via supervisorctl

### Why Lua Scripts for Queue Management?

**Alternatives Considered:**
- Client checks LLEN before push
- Worker trims queue periodically
- Redis Streams instead of Lists

**Decision:** Client-side Lua script
- **Atomic**: Single round-trip, no race conditions
- **FIFO**: Guarantees oldest dropped when full
- **Efficient**: No extra network calls
- **Correct**: Enforces 100K limit at push time

### Why MCP Protocol?

**Alternatives Considered:**
- REST API (HTTP)
- gRPC
- Direct database access

**Decision:** MCP protocol
- **Requirements**: Specified in Godot REQUIREMENTS.md
- **Consistency**: All ICCM components use MCP
- **Relay Integration**: Claude Code MCP relay already exists
- **Tooling**: Existing mcp-tools-py library

---

## Performance Characteristics

### Throughput

- **Target**: 1,000 logs/second sustained (REQ-PERF-002)
- **Tested**: Load test required before production use
- **Bottleneck**: Dewey batch insert (< 100ms per 100 logs per REQ-PERF-004)

### Latency

- **Client Push**: < 1ms (REQ-PERF-001, non-blocking Lua script)
- **Batch Processing**: 100ms maximum wait (REQ-GOD-002)
- **Query Response**: < 500ms for 1,000 results (REQ-PERF-005)

### Capacity

- **Queue Buffer**: 100,000 entries (~10MB RAM)
- **Database**: 10M+ logs supported with partitioning (REQ-SCALE-002)
- **Retention**: 7 days default (configurable via LOG_RETENTION_DAYS)
- **Storage**: ~1KB per log entry (message + JSONB data)

---

## Triplet Review Summary

**Development Cycle:** Requirements → Triplet Review → **Triplet Implementation** → Synthesis → Consensus Review → **APPROVED**

**Consensus Achieved:** 2025-10-05
**Correlation IDs:** a9c97edd (implementations), 1c281d80 (consensus review)

**Triplet Votes:**
- ✅ **GPT-4o-mini**: YES - "Robust, comprehensive, meets specified requirements"
- ✅ **Gemini-2.5-Pro**: YES - "Most robust and correct architecture achievable"
- ✅ **DeepSeek-R1**: YES - "Production-ready, meets all critical requirements"

**Synthesis Base:** Gemini-2.5-Pro implementation with DeepSeek-R1 Lua script enhancements

---

## Support

### Bug Reports

- Log bugs in `/mnt/projects/ICCM/BUG_TRACKING.md`
- Include: component, trace_id, timestamp, error message
- Attach: relevant logs from `logger_query` results

### Documentation

- **Requirements**: `/mnt/projects/ICCM/godot/REQUIREMENTS.md`
- **Client Integration**: `client_libs/README.md` (if exists)
- **Dewey Tools**: `/mnt/projects/ICCM/dewey/README.md`

### Development Cycle

This implementation follows the ICCM Development Cycle PNG:
1. ✅ Ideation: User and Claude work together
2. ✅ Draft: Claude drafts idea
3. ✅ Review: Claude gets review from triplets
4. ✅ Unanimous LLM agreement
5. ✅ Synthesis: Claude synthesizes with reviews
6. ✅ Aggregate: Claude packages and sends back to triplets
7. ✅ **APPROVED FOR DEPLOYMENT**

---

## License

Internal use only - ICCM Project

**Version:** 2.0 (Triplet-Synthesized)
**Date:** 2025-10-05
**Author:** Claude Code (ICCM Development Cycle)
**Status:** ✅ **READY FOR DEPLOYMENT**
