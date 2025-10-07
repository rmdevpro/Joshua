# Marco Documentation Review Package

## Context
Marco is a new containerized service being added to the ICCM system. It will serve as the Internet Gateway, providing browser automation capabilities via WebSocket MCP. This review is to validate the requirements and README documentation before implementation.

## Review Instructions
Please review both documents for:
1. **Completeness** - Are any critical requirements or details missing?
2. **Clarity** - Is the documentation clear and understandable?
3. **Consistency** - Do the documents align with each other and with ICCM architecture?
4. **Feasibility** - Are the technical approaches sound and implementable?
5. **Best Practices** - Any recommendations for improvement?

---

# Marco Requirements Specification

**Version:** 1.0
**Date:** 2025-10-04
**Status:** Design Phase
**Owner:** ICCM Architecture Team

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
| **Marco** | Internet/Browser Gateway | 9030 | WebSocket MCP |

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
- Implement MCP protocol specification (2025-03-26)

**REQ-3: Playwright Process Management**
- Launch Playwright MCP as internal subprocess (stdio)
- Start on container startup for low-latency readiness
- Restart automatically if subprocess crashes
- Provide manual reset capability via MCP tool

**REQ-4: Browser Context Management**
- Maintain single persistent browser instance (Phase 1)
- Support browser context isolation within instance
- Future: Support multiple instances for true client isolation (Phase 2)

**REQ-5: Protocol Bridging**
- Bridge stdio (Playwright) ↔ WebSocket (clients)
- Use shared stdio-WebSocket library (from MCP Relay refactor)
- Preserve full MCP message semantics bidirectionally

### 3.2 Tool Exposure

Marco must expose all Playwright MCP tools, including:
- `playwright_navigate` - Navigate to URL
- `playwright_screenshot` - Capture page/element screenshots
- `playwright_click` - Click elements
- `playwright_fill` - Fill form inputs
- `playwright_evaluate` - Execute JavaScript
- `playwright_snapshot` - Get accessibility tree snapshot
- Additional tools as defined by Playwright MCP specification

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

---

## 4. Non-Functional Requirements

### 4.1 Performance

**REQ-8: Latency**
- Subprocess ready within 2 seconds of container start
- Tool invocation response time < 500ms (excluding actual browser action time)
- Screenshot generation < 3 seconds for full page

**REQ-9: Resource Management**
- Single browser instance memory footprint < 500MB idle
- Graceful handling of memory pressure
- Automatic cleanup of closed tabs/contexts

### 4.2 Reliability

**REQ-10: Fault Tolerance**
- Automatic subprocess restart on crash (max 3 attempts)
- Graceful degradation if browser fails to start
- Health check endpoint for container orchestration

**REQ-11: Error Handling**
- Return meaningful error messages via MCP
- Log all errors to stdout/stderr for Docker logs
- Never crash the container on Playwright errors

### 4.3 Security

**REQ-12: Isolation**
- Run browser in sandboxed mode
- No persistent cookies/storage between container restarts
- No access to host filesystem except mounted volumes

**REQ-13: Network Security**
- Only accept WebSocket connections from `iccm_network`
- Bind WebSocket server to 0.0.0.0:8030 (internal)
- No authentication required (network isolation sufficient)

### 4.4 Maintainability

**REQ-14: Logging**
- Structured JSON logs for tool invocations
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
| **Browser** | Chromium (default) | Latest in Playwright image |
| **MCP Implementation** | @playwright/mcp | Latest |
| **WebSocket Server** | ws (Node.js library) | ^8.0.0 |
| **Bridge Library** | @iccm/mcp-bridge (custom) | 1.0.0 |

### 5.2 Container Specifications

**Image:**
```dockerfile
FROM mcr.microsoft.com/playwright:v1.43.0-jammy
```

**Ports:**
- Internal: 8030 (WebSocket MCP server)
- External: 9030 (host mapping)

**Networks:**
- `iccm_network` (shared with Fiedler, Dewey, KGB)

**Environment Variables:**
- `MARCO_PORT` - WebSocket server port (default: 8030)
- `BROWSER_TYPE` - chromium/firefox/webkit (default: chromium)
- `HEADLESS` - true/false (default: true)
- `LOG_LEVEL` - debug/info/warn/error (default: info)

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
│  │  - Command: npx @playwright/mcp@latest   │ │
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
- **Triplet Consultation:** `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_153405_a5c755ba/`

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-04 | Claude Code | Initial requirements specification |

---

**Document Status:** APPROVED for Implementation
**Next Step:** Implementation of Phase 1 MVP


---


# Marco - ICCM Internet Gateway

**Version:** 1.0.0
**Status:** Development
**Port:** 9030 (WebSocket MCP)

---

## Overview

Marco is the Internet Gateway service for the ICCM system, providing browser automation capabilities to all services via WebSocket MCP (Model Context Protocol). Marco enables AI agents to navigate websites, test web applications, and interact with web content through Playwright.

### Quick Stats

- **Container:** `marco-mcp`
- **Port:** 9030 (external) → 8030 (internal)
- **Network:** `iccm_network`
- **Protocol:** WebSocket MCP
- **Technology:** Playwright + Node.js

---

## Architecture

Marco serves as one of four core ICCM gateway services:

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Fiedler    │   │    Dewey     │   │     KGB      │   │    Marco     │
│ (LLM Orch.)  │   │  (Conv. DB)  │   │  (Logging)   │   │  (Browser)   │
│   Port 9010  │   │   Port 9020  │   │   Port 8089  │   │  Port 9030   │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

### Internal Architecture

```
┌─────────────────────────────────────────┐
│         Marco Container                 │
│                                         │
│  ┌────────────────────────────────┐    │
│  │  WebSocket MCP Server (Node)   │    │
│  │  Listens on :8030              │    │
│  └──────────────┬─────────────────┘    │
│                 │                       │
│  ┌──────────────▼─────────────────┐    │
│  │  stdio-WebSocket Bridge        │    │
│  │  (Shared with MCP Relay)       │    │
│  └──────────────┬─────────────────┘    │
│                 │ stdio                 │
│  ┌──────────────▼─────────────────┐    │
│  │  Playwright MCP Subprocess     │    │
│  │  npx @playwright/mcp@latest    │    │
│  └──────────────┬─────────────────┘    │
│                 │                       │
│  ┌──────────────▼─────────────────┐    │
│  │  Chromium Browser (Headless)   │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Features

### Current (Phase 1 - MVP)

✅ **Browser Automation**
- Navigate to URLs
- Click elements
- Fill forms
- Execute JavaScript
- Take screenshots
- Extract page content via accessibility tree

✅ **WebSocket MCP Server**
- Multiple concurrent client connections
- Full MCP protocol compliance
- Automatic reconnection handling

✅ **Subprocess Management**
- Auto-launch Playwright on startup
- Crash detection and restart
- Manual reset capability

✅ **Configuration**
- Environment variable-based
- Optional YAML for advanced settings
- Docker Compose integration

### Future (Phase 2+)

🔄 **Multi-Instance Support**
- Per-client browser isolation
- Connection pooling
- Advanced resource management

🔄 **Advanced Features**
- Multiple browser types (Firefox, WebKit)
- Mobile device emulation
- Network throttling
- Visual regression testing

---

## Installation

### Prerequisites

- Docker Engine 24+
- Docker Compose
- `iccm_network` Docker network (created during ICCM setup)

### Build and Deploy

```bash
cd /mnt/projects/ICCM/marco

# Build the container
docker compose build

# Start Marco
docker compose up -d

# Verify it's running
docker ps | grep marco-mcp
docker logs marco-mcp
```

### Verify Connectivity

```bash
# Check health endpoint (once implemented)
curl http://localhost:9030/health

# Test WebSocket connection (requires wscat or similar)
wscat -c ws://localhost:9030
```

---

## Configuration

### Environment Variables

Configure via `docker-compose.yml`:

```yaml
environment:
  - MARCO_PORT=8030          # Internal WebSocket port
  - BROWSER_TYPE=chromium    # chromium | firefox | webkit
  - HEADLESS=true            # Run browser headless
  - LOG_LEVEL=info           # debug | info | warn | error
  - VIEWPORT_WIDTH=1920      # Browser viewport width
  - VIEWPORT_HEIGHT=1080     # Browser viewport height
```

### Advanced Configuration (Optional)

Create `marco/config/browser.yaml`:

```yaml
launchOptions:
  headless: true
  args:
    - "--disable-gpu"
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
defaultViewport:
  width: 1920
  height: 1080
userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
```

Mount in docker-compose.yml:

```yaml
volumes:
  - ./config/browser.yaml:/app/config/browser.yaml:ro
```

---

## Usage

### Via MCP Relay (Bare Metal Claude)

Add to `~/.iccm-mcp/backends.yaml`:

```yaml
backends:
  - name: marco
    url: ws://localhost:9030
    enabled: true
```

Restart MCP Relay, then use from Claude:

```
Can you navigate to http://localhost:8080 and take a screenshot?
```

### Via Direct WebSocket Connection

```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:9030');

ws.on('open', () => {
  ws.send(JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/list',
    id: 1
  }));
});
```

---

## Available Tools

Marco exposes all Playwright MCP tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `playwright_navigate` | Navigate to URL | url, waitUntil |
| `playwright_screenshot` | Capture screenshot | fullPage, selector |
| `playwright_click` | Click element | selector |
| `playwright_fill` | Fill input field | selector, value |
| `playwright_evaluate` | Execute JavaScript | script |
| `playwright_snapshot` | Get accessibility tree | selector (optional) |
| `playwright_pdf` | Generate PDF | path, options |

See [Playwright MCP documentation](https://github.com/microsoft/playwright-mcp) for complete tool reference.

---

## Testing

### Manual Testing

```bash
# 1. Verify container is running
docker ps | grep marco-mcp

# 2. Check logs for startup messages
docker logs marco-mcp

# Expected output:
# ✅ Playwright subprocess started (PID: 123)
# ✅ WebSocket server listening on :8030
# ✅ Marco ready to accept connections

# 3. Test Playwright directly (inside container)
docker exec -i marco-mcp npx @playwright/mcp@latest
# Type: {"jsonrpc":"2.0","method":"tools/list","id":1}
# Expect: List of available tools
```

### Integration Testing

```bash
# Run test suite (once implemented)
cd /mnt/projects/ICCM/marco
npm test

# Test with Claude
claude --print -- "Navigate to http://localhost:8080 using Marco"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check Docker logs
docker logs marco-mcp

# Common issues:
# - Port 9030 already in use: Change MARCO_PORT
# - iccm_network doesn't exist: Create network first
# - Playwright installation failed: Rebuild image
```

### Playwright Subprocess Crashes

```bash
# Marco should auto-restart, but if persistent:

# 1. Check browser requirements
docker exec marco-mcp npx playwright install --dry-run

# 2. Increase container memory
docker compose down
# Edit docker-compose.yml: Add mem_limit: 2g
docker compose up -d

# 3. Check browser flags
docker exec marco-mcp ps aux | grep chromium
```

### WebSocket Connection Refused

```bash
# 1. Verify Marco is listening
docker exec marco-mcp netstat -tlnp | grep 8030

# 2. Check network connectivity
docker network inspect iccm_network | grep marco-mcp

# 3. Test from another container
docker run --network iccm_network --rm curlimages/curl curl http://marco-mcp:8030/health
```

### Tools Not Available in Claude

```bash
# 1. Verify MCP Relay sees Marco
cat ~/.iccm-mcp/backends.yaml | grep marco

# 2. Check MCP Relay logs
# Bare metal: Check Claude session logs
# Claudette: docker logs claude-code-container

# 3. Test direct connection
wscat -c ws://localhost:9030
# Send: {"jsonrpc":"2.0","method":"tools/list","id":1}
```

---

## Performance

### Expected Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| **Container startup** | < 10s | Includes Playwright launch |
| **Tool response latency** | < 500ms | Excluding browser action time |
| **Screenshot generation** | < 3s | Full page, 1920x1080 |
| **Memory (idle)** | < 500MB | Single browser instance |
| **Memory (active)** | < 1GB | With multiple tabs/contexts |

### Optimization Tips

1. **Use headless mode** - Saves ~100MB memory
2. **Limit viewport size** - Reduces screenshot time
3. **Close unused contexts** - Prevents memory leaks
4. **Use page snapshots** - Faster than screenshots for text

---

## Maintenance

### Updating Playwright

```bash
# Rebuild container with latest Playwright
cd /mnt/projects/ICCM/marco
docker compose build --no-cache
docker compose up -d
```

### Viewing Logs

```bash
# Follow logs
docker logs marco-mcp -f

# Last 100 lines
docker logs marco-mcp --tail 100

# Since specific time
docker logs marco-mcp --since 30m
```

### Restarting Service

```bash
# Graceful restart
docker compose restart marco-mcp

# Force recreate
docker compose down
docker compose up -d
```

---

## Security Considerations

### Current (Phase 1)

- ✅ Browser runs in sandboxed mode
- ✅ No persistent cookies/storage
- ✅ Network isolated to `iccm_network`
- ✅ No host filesystem access
- ⚠️ No authentication (relies on network isolation)

### Future Enhancements

- 🔄 WebSocket authentication tokens
- 🔄 Per-client resource quotas
- 🔄 Audit logging via KGB integration
- 🔄 Content Security Policy enforcement

---

## Development

### Project Structure

```
marco/
├── README.md              # This file
├── REQUIREMENTS.md        # Detailed requirements
├── Dockerfile            # Container definition
├── docker-compose.yml    # Service orchestration
├── package.json          # Node.js dependencies
├── src/
│   ├── server.js         # WebSocket MCP server
│   ├── bridge.js         # stdio-WebSocket bridge
│   ├── playwright.js     # Subprocess management
│   └── utils/            # Utilities
├── config/
│   └── browser.yaml      # Optional browser config
└── tests/
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

### Building from Source

```bash
cd /mnt/projects/ICCM/marco

# Install dependencies
npm install

# Run locally (requires Playwright installed)
npm start

# Run tests
npm test

# Build Docker image
docker build -t marco-mcp:latest .
```

---

## Related Documentation

- **Requirements:** [REQUIREMENTS.md](./REQUIREMENTS.md)
- **Architecture:** `/mnt/projects/ICCM/architecture/General Architecture.PNG`
- **Triplet Consultation:** `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_153405_a5c755ba/`
- **Playwright MCP:** https://github.com/microsoft/playwright-mcp
- **MCP Specification:** https://spec.modelcontextprotocol.io/

---

## Support

### Getting Help

1. Check logs: `docker logs marco-mcp`
2. Review troubleshooting section above
3. Consult requirements document: [REQUIREMENTS.md](./REQUIREMENTS.md)
4. Check architecture documentation

### Known Issues

- **Issue #1:** None reported yet (development phase)

### Reporting Bugs

Include:
- Docker logs (`docker logs marco-mcp`)
- Configuration (`docker-compose.yml` environment)
- Steps to reproduce
- Expected vs actual behavior

---

## License

Part of the ICCM (Integrated Cognitive Computing Model) project.

---

## Changelog

### Version 1.0.0 (2025-10-04)
- Initial requirements and design
- Documentation created
- Implementation pending

---

**Status:** Documentation complete, ready for implementation
**Next Steps:**
1. Create directory structure
2. Implement stdio-WebSocket bridge library
3. Build Marco WebSocket server
4. Create Dockerfile and docker-compose.yml
5. Test end-to-end integration
