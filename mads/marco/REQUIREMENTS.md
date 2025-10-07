# Marco Requirements Specification

**Version:** 1.2
**Date:** 2025-10-04
**Status:** Final - Approved for Implementation
**Owner:** ICCM Architecture Team
**Reviewers:** Gemini 2.5 Pro, GPT-4o-mini, DeepSeek-R1

---

## 1. Overview

**Marco** is the Internet Gateway service for the ICCM (Integrated Cognitive Computing Model) system. Marco provides browser automation capabilities to all ICCM services via WebSocket MCP (Model Context Protocol), enabling web exploration, testing, and interaction.

### 1.1 Mission Statement

Marco serves as the system-wide gateway for web browser automation, allowing AI agents and services to:
- Navigate and interact with websites
- Test internal web applications
- Scrape and analyze web content
- Take screenshots and gather visual data
- Execute JavaScript in browser contexts

---

## 2. Role in ICCM Architecture

Marco is one of four core gateway services:

| Service | Role | Port | Protocol |
|---------|------|------|----------|
| **Fiedler** | LLM Orchestra Gateway | 9010 | WebSocket MCP |
| **Dewey** | Conversation Storage Gateway | 9020 | WebSocket MCP |
| **KGB** | Logging Proxy Gateway | 8089 | HTTP/SSE |
| **Marco** | Internet Gateway | 9030 | WebSocket MCP |

### 2.1 Integration Points

```
┌─────────────────────────────────────────────────────────┐
│  Clients (Bare Metal Claude, Claudette, Future Agents) │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │   MCP Relay      │ (stdio ↔ WebSocket bridge)
              └──────────────────┘
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
  ┌──────────┐   ┌──────────┐    ┌──────────┐
  │ Fiedler  │   │  Dewey   │    │  Marco   │
  │ (LLMs)   │   │  (DB)    │    │ (Browser)│
  └──────────┘   └──────────┘    └──────────┘
        │               │                │
        ▼               ▼                ▼
   Cloud LLMs     PostgreSQL        Playwright
                   (Winni)          (Chromium)
```

---

## 3. Functional Requirements

### 3.1 Core Capabilities

**REQ-1: Browser Automation**
- Must provide full Playwright MCP tool suite
- Support navigation, clicking, typing, form submission
- Handle dynamic content and JavaScript-heavy sites

**REQ-2: WebSocket MCP Server**
- Listen on port 9030 (container internal 8030)
- Accept multiple concurrent WebSocket connections
- Implement [MCP protocol specification](https://spec.modelcontextprotocol.io/specification/2025-03-26/) (2025-03-26)
- Serialize concurrent requests to single browser instance (Phase 1)
- Queue requests with FIFO ordering to prevent race conditions

**REQ-3: Playwright Process Management**
- Launch Playwright MCP as internal subprocess (stdio) with pinned version
- Start on container startup for low-latency readiness
- Restart automatically if subprocess crashes (max 3 attempts)
- Provide manual reset tool (`marco_reset_browser`) to restart browser without container restart
- Implement graceful shutdown handling (SIGTERM) to close browser cleanly

**REQ-4: Browser Context Management**
- Maintain single persistent browser instance (Phase 1)
- Create isolated browser contexts per client session (Playwright contexts)
- **Phase 1 Limitation:** All contexts share process resources; potential for cross-contamination
- Implement context cleanup on client disconnect to prevent memory leaks
- Future: Support multiple browser instances for true client isolation (Phase 2)

**REQ-5: Protocol Bridging**
- Bridge stdio (Playwright) ↔ WebSocket (clients)
- Use shared stdio-WebSocket library `@iccm/mcp-bridge` (to be developed from MCP Relay refactor)
- Preserve full MCP message semantics bidirectionally
- Map Playwright errors to MCP error codes with meaningful messages

### 3.2 Tool Exposure

Marco must expose all Playwright MCP tools, including:
- `playwright_navigate` - Navigate to URL
- `playwright_screenshot` - Capture page/element screenshots
- `playwright_click` - Click elements
- `playwright_fill` - Fill form inputs
- `playwright_evaluate` - Execute JavaScript
- `playwright_snapshot` - Get accessibility tree snapshot
- `marco_reset_browser` - Manual browser instance reset (Marco-specific tool)
- Additional tools as defined by Playwright MCP specification v1.43.0

### 3.3 Configuration

**REQ-6: Environment-Based Configuration**
- Browser type (chromium/firefox/webkit) - Default: chromium
- Headless mode (true/false) - Default: true
- Viewport size - Default: 1920x1080
- User agent string
- Proxy settings (if needed)
- Max concurrent clients (future use)

**REQ-7: Optional YAML Configuration**
- Support `marco/config/browser.yaml` for complex settings
- Playwright launch arguments
- Browser-specific configurations
- Timeout values
- **Configuration Precedence:** Environment Variables > YAML file > Defaults

---

## 4. Non-Functional Requirements

### 4.1 Performance

**REQ-8: Latency**
- Subprocess ready within 2 seconds of container start
- Tool invocation response time < 500ms (excluding actual browser action time)
- Screenshot generation < 3 seconds for full page

**REQ-9: Resource Management**
- Single browser instance memory footprint < 1GB idle (revised from 500MB)
- Docker memory limit set to 2GB to prevent host exhaustion
- Graceful handling of memory pressure
- Automatic cleanup of closed tabs/contexts
- Context recycling after 100 operations to prevent memory leaks

### 4.2 Reliability

**REQ-10: Fault Tolerance**
- Automatic subprocess restart on crash (max 3 attempts)
- Graceful degradation if browser fails to start
- Health check endpoint at `GET /health` returning:
  ```json
  {
    "status": "healthy",
    "browser": "alive",
    "uptime_seconds": 123.45,
    "playwright_subprocess": "responsive"
  }
  ```
- Health check validates: WebSocket server running + Playwright subprocess responsive
- Return HTTP 200 if healthy, 503 if degraded

**REQ-11: Error Handling**
- Map Playwright errors to standard MCP error codes:
  - Navigation timeout → `REQUEST_TIMEOUT`
  - Element not found → `INVALID_PARAMS`
  - Browser crash → `INTERNAL_ERROR`
- Return meaningful error messages via MCP with context
- Log all errors to stdout/stderr in structured JSON format
- Example error response:
  ```json
  {
    "jsonrpc": "2.0",
    "error": {
      "code": -32603,
      "message": "Navigation timeout after 30s",
      "data": {"url": "https://example.com", "timeout_ms": 30000}
    },
    "id": 1
  }
  ```
- Never crash the container on Playwright errors

### 4.3 Security

**REQ-12: Isolation**
- Run browser in sandboxed mode with `--no-sandbox` flag (required for containers)
- Run container process as non-root user (`pwuser` from Playwright image)
- No persistent cookies/storage between container restarts
- No access to host filesystem except mounted volumes
- Apply seccomp security profile for syscall filtering

**REQ-13: Network Security**
- Only accept WebSocket connections from `iccm_network`
- Bind WebSocket server to 0.0.0.0:8030 (internal)
- **No authentication in Phase 1** - relies on network isolation only
- **Security Warning:** Marco must NEVER be exposed to public internet
- Document security limitations prominently in README

### 4.4 Maintainability

**REQ-14: Logging**
- Structured JSON logs for tool invocations
- Example log entry:
  ```json
  {
    "timestamp": "2025-10-04T15:30:45.123Z",
    "level": "info",
    "event": "tool_invocation",
    "tool": "playwright_navigate",
    "params": {"url": "https://example.com"},
    "duration_ms": 1234,
    "client_id": "relay-connection-1"
  }
  ```
- Debug mode for verbose browser console output
- Performance metrics (tool execution times)

**REQ-15: Monitoring**
- Health check endpoint (`/health`)
- Metrics endpoint for process status
- Browser instance alive/dead status

---

## 5. Technical Architecture

### 5.1 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Base Image** | mcr.microsoft.com/playwright | v1.43.0-jammy |
| **Runtime** | Node.js | 22.x (included in image) |
| **Browser** | Chromium (default) | v123.x (in Playwright image) |
| **MCP Implementation** | @playwright/mcp | **0.0.41** (pinned stable, compatible with Playwright 1.43.0) |
| **WebSocket Server** | ws (Node.js library) | ^8.0.0 |
| **Bridge Library** | @iccm/mcp-bridge (custom) | 1.0.0 (to be developed) |

### 5.2 Container Specifications

**Image:**
```dockerfile
FROM mcr.microsoft.com/playwright:v1.43.0-jammy
```

**Ports:**
- Internal: 8030 (WebSocket MCP server + HTTP health check)
- External: 9030 (host mapping)
- **Note:** Same port (8030) handles both WebSocket upgrade requests and HTTP health checks

**Networks:**
- `iccm_network` (shared with Fiedler, Dewey, KGB)

**Environment Variables:**
- `MARCO_PORT` - WebSocket server port (default: 8030)
- `BROWSER_TYPE` - chromium/firefox/webkit (default: chromium)
- `HEADLESS` - true/false (default: true)
- `LOG_LEVEL` - debug/info/warn/error (default: info)

**Resource Limits:**
- Memory: 2GB (hard limit to prevent host exhaustion)
- CPU: No limit (burst allowed for page rendering)

### 5.3 Process Architecture

```
┌────────────────────────────────────────────────┐
│            Marco Container                     │
│  ┌──────────────────────────────────────────┐ │
│  │  WebSocket MCP Server (Node.js)          │ │
│  │  - Listens on :8030                      │ │
│  │  - Handles multiple client connections   │ │
│  └──────────────┬───────────────────────────┘ │
│                 │                              │
│  ┌──────────────▼───────────────────────────┐ │
│  │  stdio-WebSocket Bridge Library          │ │
│  │  - Bidirectional message forwarding      │ │
│  │  - JSON-RPC protocol handling            │ │
│  └──────────────┬───────────────────────────┘ │
│                 │ stdio (stdin/stdout)         │
│  ┌──────────────▼───────────────────────────┐ │
│  │  Playwright MCP Subprocess               │ │
│  │  - Command: npx @playwright/mcp@1.43.0   │ │
│  │  - Launched on container startup         │ │
│  │  - Auto-restart on crash                 │ │
│  └──────────────┬───────────────────────────┘ │
│                 │                              │
│  ┌──────────────▼───────────────────────────┐ │
│  │  Chromium Browser Instance               │ │
│  │  - Headless mode                         │ │
│  │  - Sandboxed                             │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

---

## 6. Development Phases

### Phase 1: MVP (Current)
- Single browser instance
- Basic stdio-WebSocket bridge
- Environment variable configuration
- Docker container deployment
- Integration with MCP Relay

**Success Criteria:**
- Marco container starts and connects to `iccm_network`
- Bare metal Claude can invoke Playwright tools via relay
- Can navigate to http://localhost:8080 and take screenshot

### Phase 2: Scaling (Future)
- Per-client browser instance isolation
- Connection pooling and queuing
- Advanced resource management
- Performance optimization

**Deferred to:** When Fiedler also needs multi-client support

### Phase 3: Production Hardening (Future)
- Authentication/authorization
- Rate limiting
- Advanced monitoring and telemetry
- Horizontal scaling support

---

## 7. Testing Requirements

### 7.1 Unit Tests
- stdio-WebSocket bridge library tests
- Message serialization/deserialization
- Error handling paths

### 7.2 Integration Tests
- Container startup and readiness
- WebSocket connection establishment
- Playwright subprocess lifecycle
- Tool invocation round-trip

### 7.3 End-to-End Tests
- Claude → Relay → Marco → Browser navigation
- Screenshot capture and retrieval
- JavaScript execution
- Multi-page workflows

### 7.4 Performance Tests
- Concurrent client handling
- Memory leak detection (24-hour soak test)
- Browser crash recovery

---

## 8. Dependencies

### 8.1 External Services
- **Docker Engine** - Container runtime
- **iccm_network** - Docker network (must exist)

### 8.2 Internal Services (Optional)
- **MCP Relay** - For bare metal Claude access
- **Dewey** - For logging Marco interactions (future)

### 8.3 Development Dependencies
- **Node.js 22+** - For local development
- **npm** - Package management
- **Docker Compose** - Container orchestration

---

## 9. Operational Considerations

### 9.1 Deployment
- Docker Compose service definition
- Port mapping: 9030:8030
- Network attachment to `iccm_network`
- Volume mounts for optional config file

### 9.2 Monitoring
- Docker logs for application logs
- Health check via Docker HEALTHCHECK directive
- Manual verification: `curl http://localhost:9030/health`

### 9.3 Maintenance
- Container restart: `docker compose restart marco-mcp`
- Log inspection: `docker logs marco-mcp -f`
- Config updates: Edit docker-compose.yml, recreate container

### 9.4 Troubleshooting
- Check network connectivity: `docker network inspect iccm_network`
- Verify Playwright installation: `docker exec marco-mcp npx playwright --version`
- Test stdio interface: `docker exec -i marco-mcp npx @playwright/mcp@latest`

---

## 10. Success Metrics

**Phase 1 Acceptance Criteria:**

1. ✅ Container builds successfully from official Playwright image
2. ✅ WebSocket MCP server starts on port 8030
3. ✅ Playwright subprocess launches and stays running
4. ✅ MCP Relay can connect via WebSocket
5. ✅ Bare metal Claude can list Marco's tools
6. ✅ Can navigate to localhost:8080 (Claude UI)
7. ✅ Can take screenshot and retrieve image data
8. ✅ Can extract page text via accessibility snapshot
9. ✅ Container auto-restarts if Playwright crashes
10. ✅ Documentation complete (README.md, architecture diagram)

**Performance Targets:**
- Container startup to ready: < 10 seconds
- Tool response latency: < 500ms (excluding browser action)
- Memory footprint: < 1GB at idle
- Uptime: 99.9% (auto-restart on crash)

---

## 11. Future Enhancements

### 11.1 Multi-Instance Support (Phase 2)
- Launch separate Playwright instance per WebSocket client
- Browser context pooling for resource efficiency
- Client session persistence and reconnection

### 11.2 Advanced Browser Features
- Multiple browser types simultaneously (Chromium + Firefox)
- Mobile device emulation
- Geolocation and timezone spoofing
- Network throttling and offline simulation

### 11.3 Content Intelligence
- Automatic page readability extraction
- Screenshot diff comparison
- Visual regression testing support
- Accessibility audit integration

### 11.4 Security Enhancements
- Authentication tokens for WebSocket connections
- Per-client resource quotas
- Audit logging of all browser actions
- Integration with KGB for request logging

---

## 12. Related Documentation

- **Architecture Diagram:** `/mnt/projects/ICCM/architecture/General Architecture.PNG`
- **MCP Specification:** https://spec.modelcontextprotocol.io/specification/2025-03-26/
- **Playwright MCP:** https://github.com/microsoft/playwright-mcp
- **Fiedler Requirements:** `/mnt/projects/ICCM/architecture/fiedler_requirements.md`
- **Triplet Consultations:**
  - Design Review: `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_153405_a5c755ba/`
  - Documentation Review: `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_155011_c0509ac2/`

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-04 | Claude Code | Initial requirements specification |
| 1.1 | 2025-10-04 | Claude Code | Triplet review revisions: Concurrency model, health checks, security hardening, resource limits, error handling, pinned dependencies |
| 1.2 | 2025-10-04 | Claude Code | Final review corrections: Fixed version pinning (§5.3), clarified health check port, standardized naming to "Internet Gateway" |

---

**Document Status:** APPROVED for Implementation
**Next Step:** Implementation of Phase 1 MVP
