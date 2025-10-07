# Godot: Unified Logging Infrastructure - Requirements Document

## 1. Project Overview

**Project Name:** Godot (Unified Logging Infrastructure)
**Purpose:** Provide centralized, production-grade logging for all ICCM components to enable debugging of distributed system communication issues
**Primary Use Case:** Debug BUG #13 (Gates MCP tools not callable) by capturing exact message exchanges between components
**Architecture Principle:** Dewey owns all Winni (PostgreSQL) access - Godot acts as collection/buffering layer only

**Environment Context:**
- **Scale:** Small development group (1-3 developers)
- **Deployment:** Single Docker host (not enterprise/distributed)
- **Usage:** Development and debugging tool, not mission-critical production infrastructure
- **Constraints:** All containers run on one machine, no Kubernetes/orchestration
- **Priorities:** Debuggability over high availability, simplicity over enterprise resilience

## 2. Problem Statement

### Current State
- No visibility into message exchanges between MCP relay and backend servers
- Cannot see exact data structures being sent/received during tool registration
- Unable to correlate logs across components (relay, Gates, Dewey, Fiedler)
- Insufficient logging to debug why Gates tools register but aren't callable

### Desired State
- Capture EVERY message exchanged between components at TRACE level
- Store logs centrally with full-text search and structured querying
- Correlate logs across components using request/trace IDs
- Compare message structures between working servers (Dewey, Fiedler) and broken (Gates)

## 3. System Architecture

### Components

#### 3.1 Godot Container (New)
**Responsibilities:**
- Receive logs from all components via Redis queue
- Buffer logs during high load or Dewey downtime
- Batch logs and send to Dewey for storage
- Provide MCP tools for log management (facade to Dewey)

**Services:**
- Redis Server (internal, not exposed)
- Log Worker Process (background, consumes queue)
- MCP Server (port 9060, external)

#### 3.2 Dewey Container (Updated)
**Responsibilities:**
- Own all access to Winni (PostgreSQL) database
- Validate and store log entries
- Provide log query/management tools

**New Tools:**
- `dewey_store_logs_batch(logs)` - Batch insert log entries
- `dewey_query_logs(filters)` - Query logs with full-text search
- `dewey_clear_logs(criteria)` - Clear old logs (with retention policy)

#### 3.3 Logging Integration (MCP-Based)
**ARCHITECTURAL REQUIREMENT:** ALL MCP servers MUST use MCP-based logging via WebSocket to Godot's `logger_log` tool. Direct Redis connections are FORBIDDEN.

**Integration Methods:**
1. **MCP Servers (REQUIRED):** Call `logger_log` MCP tool via WebSocket (ws://godot-mcp:9060)
   - Gates, Playfair, Marco, Fiedler, Dewey, KGB, Claudette, MCP Relay
   - Uses WebSocket client library (built-in to most platforms)
   - Redis (port 6379) is internal to Godot only - NOT accessible on network

2. **Legacy Redis Client (DEPRECATED - Architectural Violation):**
   - Direct Redis connections (loglib.py/loglib.js) - FORBIDDEN for MCP servers
   - Only preserved for historical reference
   - Violates MCP protocol layer architecture

### Data Flow

```
MCP Components (gates, fiedler, dewey, relay, etc.)
    ↓ (WebSocket MCP: logger_log tool call to ws://godot-mcp:9060)
Godot MCP Server receives log
    ↓ (pushes to internal Redis queue - port 6379 NOT exposed)
Godot Redis Queue (internal only)
    ↓ (worker pulls and batches)
Godot Worker → dewey_store_logs_batch()
    ↓ (MCP call)
Dewey validates & stores
    ↓
PostgreSQL (Winni on Irina)
```

**CRITICAL:** Redis (port 6379) is internal to Godot container (bind: 127.0.0.1). Components MUST NOT attempt direct Redis connections.

## 4. Functional Requirements

### 4.1 Log Collection (Godot)

**REQ-GOD-001:** Godot MUST accept log entries via Redis LPUSH to `logs:queue`
**REQ-GOD-002:** Godot worker MUST consume logs in batches (100 logs or 100ms window, whichever first)
**REQ-GOD-003:** Godot worker MUST call `dewey_store_logs_batch()` with batched entries
**REQ-GOD-004:** Godot MUST handle Dewey downtime by buffering up to 100,000 logs in Redis
**REQ-GOD-005:** Godot MUST drop oldest logs (FIFO) when buffer exceeds 100,000 entries

### 4.2 Log Storage (Dewey)

**REQ-DEW-001:** Dewey MUST provide `dewey_store_logs_batch(logs)` tool accepting up to 1,000 log entries
**REQ-DEW-002:** Each log entry MUST contain: `id`, `trace_id`, `component`, `level`, `message`, `data`, `created_at`
**REQ-DEW-003:** Dewey MUST validate log level is one of: ERROR, WARN, INFO, DEBUG, TRACE
**REQ-DEW-004:** Dewey MUST use single transaction for batch insert (atomicity)
**REQ-DEW-005:** Dewey MUST create partitions by day for `logs` table (automated via cron or pg_partman)

### 4.3 Log Querying (Dewey)

**REQ-DEW-006:** Dewey MUST provide `dewey_query_logs()` tool with filters:
- `trace_id` (UUID) - Find all logs for a request
- `component` (string) - Filter by component name
- `level` (string) - Minimum log level
- `start_time`, `end_time` (ISO 8601) - Time range
- `search` (string) - Full-text search on message
- `limit` (int) - Max results (default 100, max 1000)

**REQ-DEW-007:** Dewey MUST support searching structured data in `data` JSONB field
**REQ-DEW-008:** Query results MUST include all fields plus computed `age` (time since log)

### 4.4 Log Management (Dewey)

**REQ-DEW-009:** Dewey MUST provide `dewey_clear_logs()` with retention policy:
- Default: Delete logs older than 7 days
- Support: `before_time`, `component`, `level` filters

**REQ-DEW-010:** Dewey MUST provide `dewey_get_log_stats()` returning:
- Total log count by component
- Log count by level
- Oldest/newest log timestamps
- Database size estimate

### 4.5 MCP-Based Logging Integration (REQUIRED for ALL MCP Servers)

**REQ-MCP-001:** ALL MCP servers MUST use WebSocket MCP to call `logger_log` tool on Godot (ws://godot-mcp:9060)
**REQ-MCP-002:** Log calls MUST be non-blocking and fail silently (never break application)
**REQ-MCP-003:** Log levels MUST be one of: ERROR, WARN, INFO, DEBUG, TRACE
**REQ-MCP-004:** Components MUST propagate `trace_id` when available for request correlation
**REQ-MCP-005:** Components MUST include structured `data` (JSONB) for context
**REQ-MCP-006:** Logging MUST be controlled via environment variable `LOGGING_ENABLED` (default: true)
**REQ-MCP-007:** Components MUST use connection timeout ≤1 second for Godot WebSocket calls

### 4.6 Legacy Redis Client (DEPRECATED - DO NOT USE)

**DEPRECATED:** Direct Redis client libraries (loglib.py/loglib.js) violate ICCM architecture. Preserved for historical reference only. See Godot README for correct MCP-based implementation.

### 4.7 Request Correlation

**REQ-COR-001:** Relay MUST generate `trace_id` (UUID v4) for each incoming request from Claude Code
**REQ-COR-002:** Relay MUST include `trace_id` in all forwarded messages to backends via `X-Trace-ID` header (or MCP metadata field if supported)
**REQ-COR-003:** All components MUST extract `trace_id` from incoming messages and include in logs
**REQ-COR-004:** MCP logging calls MUST include optional `trace_id` parameter when available
**REQ-COR-005:** If no `trace_id` provided, components MUST use `null` (not generate new ID)

### 4.8 Security & Privacy

**REQ-SEC-001:** Components SHOULD redact sensitive fields before logging (client-side responsibility)
**REQ-SEC-002:** Recommended redacted fields: `password`, `token`, `api_key`, `authorization`, `secret`
**REQ-SEC-003:** Redaction SHOULD replace sensitive values with `"[REDACTED]"`
**REQ-SEC-004:** Components SHOULD support configurable redaction patterns
**REQ-SEC-005:** Godot Redis MUST bind to 127.0.0.1 only (not exposed on network)
**REQ-SEC-006:** Godot and Dewey internal communication MUST use MCP over localhost/docker network only

## 5. Non-Functional Requirements

### 5.1 Performance

**REQ-PERF-001:** MCP logging call (logger_log) MUST be non-blocking and fail silently on timeout
**REQ-PERF-002:** Godot worker MUST process 1,000 logs/second sustained
**REQ-PERF-003:** Redis queue depth MUST NOT exceed 100,000 entries (drop oldest if full)
**REQ-PERF-004:** Dewey batch insert MUST complete in <100ms for 100 log entries
**REQ-PERF-005:** Log query with filters MUST return in <500ms for result sets up to 1,000 entries
**REQ-PERF-006:** MCP logging calls MUST use timeout ≤1 second to prevent blocking

### 5.2 Reliability

**REQ-REL-001:** Godot Redis MUST persist queue to disk (AOF enabled)
**REQ-REL-002:** Godot worker MUST retry Dewey calls with exponential backoff (max 3 retries)
**REQ-REL-003:** MCP logging MUST fail silently - never break application on Godot unavailability
**REQ-REL-004:** System MUST survive simultaneous failure of Godot and Dewey (components continue operating)

### 5.3 Scalability

**REQ-SCALE-001:** System MUST handle 100 requests/second from relay with 10 logs per request (1,000 logs/sec)
**REQ-SCALE-002:** PostgreSQL `logs` table MUST support 10M+ entries without degradation
**REQ-SCALE-003:** Full-text search MUST remain performant up to 10M log entries
**REQ-SCALE-004:** Time-based partitioning MUST prevent table bloat beyond 30 days retention

### 5.4 Maintainability

**REQ-MAINT-001:** All components MUST log to `stdout/stderr` for Docker container logging
**REQ-MAINT-002:** Godot MUST NOT call its own logger_log tool (prevent infinite loops)
**REQ-MAINT-003:** Each component MUST expose health check endpoint
**REQ-MAINT-004:** Configuration MUST be via environment variables (12-factor app)
**REQ-MAINT-005:** Components MUST document MCP-based logging integration in README

## 6. Database Schema

### 6.1 Logs Table (Dewey/Winni)

```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trace_id UUID,                    -- Request correlation ID
    component TEXT NOT NULL,           -- Component name (relay, gates, etc.)
    level TEXT NOT NULL CHECK (level IN ('ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')),
    message TEXT NOT NULL,             -- Log message
    data JSONB,                        -- Structured data (full request/response objects)
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Indexes
CREATE INDEX idx_logs_trace_id ON logs(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_logs_component_time ON logs(component, created_at DESC);
CREATE INDEX idx_logs_level ON logs(level) WHERE level IN ('ERROR', 'WARN');
CREATE INDEX idx_logs_message_fts ON logs USING gin(to_tsvector('english', message));
CREATE INDEX idx_logs_data ON logs USING gin(data jsonb_path_ops);

-- Auto-partitioning (daily)
-- Managed via pg_partman or cron job
```

### 6.2 Logger Config Table (Optional)

```sql
CREATE TABLE logger_config (
    component TEXT PRIMARY KEY,
    level TEXT NOT NULL DEFAULT 'INFO',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 7. API Specifications

### 7.1 Godot MCP Tools (Facades)

**Tool: `logger_log`** (Facade - pushes to Redis)
```json
{
  "name": "logger_log",
  "inputSchema": {
    "component": "string (required)",
    "level": "string (required) - ERROR|WARN|INFO|DEBUG|TRACE",
    "message": "string (required)",
    "trace_id": "string (optional) - UUID",
    "data": "object (optional)"
  }
}
```

**Tool: `logger_query`** (Facade - calls dewey_query_logs)
```json
{
  "name": "logger_query",
  "inputSchema": {
    "trace_id": "string (optional)",
    "component": "string (optional)",
    "level": "string (optional)",
    "start_time": "string (optional) - ISO 8601",
    "end_time": "string (optional) - ISO 8601",
    "search": "string (optional)",
    "limit": "integer (optional, default 100, max 1000)"
  }
}
```

**Tool: `logger_clear`** (Facade - calls dewey_clear_logs)
```json
{
  "name": "logger_clear",
  "inputSchema": {
    "before_time": "string (optional) - ISO 8601",
    "component": "string (optional)"
  }
}
```

**Tool: `logger_set_level`** (Updates logger_config)
```json
{
  "name": "logger_set_level",
  "inputSchema": {
    "component": "string (required)",
    "level": "string (required) - ERROR|WARN|INFO|DEBUG|TRACE"
  }
}
```

### 7.2 Dewey New Tools

**Tool: `dewey_store_logs_batch`**
```json
{
  "name": "dewey_store_logs_batch",
  "inputSchema": {
    "logs": "array (required, max 1000 items)",
    "logs[].trace_id": "string (optional) - UUID",
    "logs[].component": "string (required)",
    "logs[].level": "string (required)",
    "logs[].message": "string (required)",
    "logs[].data": "object (optional)",
    "logs[].created_at": "string (optional) - ISO 8601, defaults to NOW()"
  }
}
```

**Tool: `dewey_query_logs`**
(Same schema as `logger_query`)

**Tool: `dewey_clear_logs`**
(Same schema as `logger_clear`)

**Tool: `dewey_get_log_stats`**
```json
{
  "name": "dewey_get_log_stats",
  "inputSchema": {}
}
```

### 7.3 MCP-Based Logging Integration (REQUIRED)

**ARCHITECTURAL REQUIREMENT:** ALL MCP servers MUST use MCP-based logging. See Godot README for complete implementation examples.

**Python Implementation:**
```python
from .godot import log_to_godot

# Non-blocking async logging
await log_to_godot(
    level='INFO',
    message='Server starting',
    component='your-component',
    data={'port': 8080},
    trace_id=trace_id,  # Optional
    godot_url='ws://godot-mcp:9060'
)
```

**Node.js Implementation:**
```javascript
const WebSocket = require('ws');

async function logToGodot(level, message, data = null, traceId = null) {
    // See Godot README for complete implementation
    // Calls logger_log tool via WebSocket MCP
}
```

**Environment Variables:**
```yaml
environment:
  - GODOT_URL=ws://godot-mcp:9060
  - LOGGING_ENABLED=true
```

**DEPRECATED:** Legacy Redis client libraries (loglib.py/loglib.js) are FORBIDDEN. They violate the ICCM architecture by bypassing the MCP protocol layer.

## 8. Deployment Architecture

### 8.1 Container Configuration

**Godot Container:**
```yaml
services:
  godot:
    image: godot-logger:latest
    container_name: godot-mcp
    ports:
      - "9060:9060"  # MCP server
    environment:
      - REDIS_PERSISTENCE=1
      - REDIS_AOF_ENABLED=1
      - DEWEY_MCP_URL=ws://dewey-mcp:8080
      - BATCH_SIZE=100
      - BATCH_TIMEOUT_MS=100
      - MAX_QUEUE_SIZE=100000
    volumes:
      - godot_data:/data
    networks:
      - iccm_network
```

**Dewey Container (Updated):**
```yaml
services:
  dewey:
    # ... existing config ...
    environment:
      # ... existing vars ...
      - LOG_RETENTION_DAYS=7
      - LOG_PARTITION_ENABLED=1
```

### 8.2 Network Configuration

- All containers on `iccm_network` bridge network
- Godot exposes port 9060 for MCP tools (WebSocket)
- Godot connects to Dewey via `ws://dewey-mcp:9020` (internal)
- **Godot Redis port 6379 is INTERNAL ONLY** - bound to 127.0.0.1, NOT exposed on network
- **Components MUST connect via WebSocket MCP** (ws://godot-mcp:9060), NOT Redis directly

## 9. Testing Requirements

### 9.1 Unit Tests

**REQ-TEST-001:** Client library MUST have unit tests for all log methods
**REQ-TEST-002:** Client library MUST test redaction logic with sample sensitive data
**REQ-TEST-003:** Godot worker MUST test batch processing logic
**REQ-TEST-004:** Dewey tools MUST test batch insert with 1,000 entries

### 9.2 Integration Tests

**REQ-TEST-005:** End-to-end test: Component → Godot → Dewey → PostgreSQL
**REQ-TEST-006:** Test trace_id propagation: Relay → Gates → Godot → Dewey
**REQ-TEST-007:** Test Redis queue overflow: Send 150,000 logs, verify 100,000 stored
**REQ-TEST-008:** Test Dewey downtime: Verify Godot buffers and retries

### 9.3 Performance Tests

**REQ-TEST-009:** Load test: 1,000 logs/sec for 60 seconds, verify no data loss
**REQ-TEST-010:** Query performance: 10M logs in DB, query by trace_id in <500ms

### 9.4 BUG #13 Validation

**REQ-TEST-011:** Enable TRACE on relay and Gates
**REQ-TEST-012:** Call `mcp__iccm__gates_list_capabilities`
**REQ-TEST-013:** Query logs by trace_id, compare Gates vs Dewey tool registration messages
**REQ-TEST-014:** Identify structural difference in tool objects

## 10. Success Criteria

### 10.1 Functional Success

- ✅ All components successfully log to Godot
- ✅ Logs appear in Dewey PostgreSQL `logs` table
- ✅ Query logs by trace_id returns correlated entries across components
- ✅ Field redaction works (no sensitive data in logs)
- ✅ Log levels dynamically adjustable via `logger_set_level`

### 10.2 BUG #13 Resolution

- ✅ Capture exact JSON sent from Gates during `tools/list`
- ✅ Capture exact JSON sent from Dewey during `tools/list`
- ✅ Compare and identify difference causing relay lookup failure
- ✅ Root cause identified and documented

### 10.3 Performance Success

- ✅ Client log calls <1ms (non-blocking)
- ✅ System handles 1,000 logs/sec sustained
- ✅ Query by trace_id returns in <500ms with 10M logs
- ✅ No memory leaks after 24hr operation

### 10.4 Operational Success

- ✅ System survives Godot restart (logs resume)
- ✅ System survives Dewey restart (Godot buffers and retries)
- ✅ Retention policy auto-deletes logs >7 days old
- ✅ No infinite logging loops

## 11. Constraints & Assumptions

### 11.1 Constraints

- **CONST-001 (Refined for Option 4):** Dewey is the authoritative **READ gatekeeper** for Winni. **WRITE operations** may be delegated to specialized ingestion services (e.g., Godot for logs) with appropriate access controls and clear architectural boundaries. Godot has INSERT-only access to the `logs` table via dedicated `godot_log_writer` database user.
- **CONST-002:** All containers must run on single Docker host (no Kubernetes/orchestration)
- **CONST-003:** Claude Code cannot be restarted - MCP relay handles backend connections dynamically
- **CONST-004:** Log retention policy determined by operational needs, not disk space (44TB RAID 5 available on Irina)
- **CONST-005:** Development/staging use only initially - production requires security hardening

### 11.2 Assumptions

- **ASSUM-001:** PostgreSQL (Winni) on Irina server has 44TB RAID 5 storage - sufficient for years of log retention
- **ASSUM-002:** Network latency between containers <10ms (same host)
- **ASSUM-003:** Redis can buffer 100,000 logs in memory (~10MB)
- **ASSUM-004:** BUG #13 will be resolved within 7 days (log retention window)
- **ASSUM-005:** TRACE level will only be enabled temporarily for debugging

## 12. Future Enhancements (Out of Scope)

- Distributed tracing (OpenTelemetry integration)
- Log aggregation across multiple ICCM deployments
- Real-time log streaming to web UI
- Machine learning anomaly detection on logs
- Metrics/alerting based on log patterns
- Elasticsearch integration for advanced querying
- Multi-tenancy support

## 13. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Redis memory exhaustion | High | Medium | Bounded queue (100K), drop oldest logs |
| PostgreSQL disk full | High | Low | Auto-retention (7 days), partition cleanup |
| Dewey overload from log volume | Medium | Medium | Batching (100 logs), rate limiting |
| Sensitive data exposure | High | Low | Client-side redaction, security review |
| Infinite logging loops | Medium | Low | Godot uses local logging only |
| Performance degradation at TRACE | Medium | High | Dynamic level control, disable after debug |

## 14. Acceptance Criteria

**This project is accepted when:**

1. ✅ All functional requirements (REQ-GOD-*, REQ-DEW-*, REQ-LIB-*) are implemented
2. ✅ All unit and integration tests pass
3. ✅ BUG #13 root cause identified using Godot logs
4. ✅ Performance benchmarks meet requirements (1,000 logs/sec)
5. ✅ Security review confirms no sensitive data leakage
6. ✅ Documentation complete (README, API docs, architecture diagram)
7. ✅ Triplet review approves final implementation
8. ✅ User acceptance test passes

---

**Document Version:** 2.0 (Triplet-Approved with Environment Context)
**Author:** Claude (ICCM Development Cycle)
**Date:** 2025-10-04
**Status:** Approved - Ready for Implementation
**Triplet Review:** Unanimous approval with minor enhancements applied (100K buffer, FIFO drop, enhanced fallback, X-Trace-ID header)
