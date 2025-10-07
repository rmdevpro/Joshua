# Marco - ICCM Internet Gateway

**Version:** 1.1.0
**Status:** Documentation Complete - Ready for Implementation
**Port:** 9030 (WebSocket MCP)
**Security:** ⚠️ **Internal Use Only - Not for Public Internet**

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
- Request serialization (FIFO queue) to single browser instance
- Full MCP protocol compliance
- Automatic reconnection handling

✅ **Subprocess Management**
- Auto-launch Playwright on startup (pinned version 1.43.0)
- Crash detection and restart (max 3 attempts)
- Manual reset tool (`marco_reset_browser`)
- Graceful shutdown handling

✅ **Configuration**
- Environment variable-based (highest precedence)
- Optional YAML for advanced settings
- Docker Compose integration

### Phase 1 Limitations

⚠️ **Single Browser Instance**
- All clients share one browser process with separate contexts
- Potential for resource contention under high load
- Cross-context contamination possible (shared process)
- Requests are serialized to prevent race conditions

⚠️ **No Authentication**
- Relies entirely on Docker network isolation
- **Must NOT be exposed to public internet**
- Suitable only for trusted internal network (`iccm_network`)

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
# Check health endpoint
curl http://localhost:9030/health

# Expected response (HTTP 200):
{
  "status": "healthy",
  "browser": "alive",
  "uptime_seconds": 123.45,
  "playwright_subprocess": "responsive"
}

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
mem_limit: 2g                # Hard memory limit (prevents host exhaustion)
```

**Note:** Environment variables take precedence over YAML configuration.

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
| `marco_reset_browser` | Reset browser instance | none |

**Note:** `playwright_pdf` tool was incorrectly listed in initial draft. Verify actual tool list against Playwright MCP v1.43.0 specification.

See [Playwright MCP documentation](https://github.com/microsoft/playwright-mcp) for complete tool reference.

---

## Testing

### Manual Testing

```bash
# 1. Verify container is running
docker ps | grep marco-mcp

# 2. Check logs for startup messages
docker logs marco-mcp

# Expected output (structured JSON logs):
{"timestamp":"2025-10-04T15:30:45.123Z","level":"info","event":"playwright_started","pid":123}
{"timestamp":"2025-10-04T15:30:45.234Z","level":"info","event":"websocket_listening","port":8030}
{"timestamp":"2025-10-04T15:30:45.345Z","level":"info","event":"marco_ready"}

# 3. Test Playwright directly (inside container)
docker exec -i marco-mcp npx @playwright/mcp@1.43.0
# Type: {"jsonrpc":"2.0","method":"tools/list","id":1}
# Expect: List of available tools
```

**Example Tool Invocation Log:**
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
| **Memory (idle)** | < 1GB | Single browser instance (revised) |
| **Memory (active)** | < 1.5GB | With multiple tabs/contexts |
| **Memory limit** | 2GB | Hard Docker limit |

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

- ✅ Browser runs in sandboxed mode (`--no-sandbox` flag for containers)
- ✅ Container process runs as non-root user (`pwuser`)
- ✅ No persistent cookies/storage between container restarts
- ✅ Network isolated to `iccm_network`
- ✅ No host filesystem access (except mounted volumes)
- ✅ Seccomp security profile applied
- ⚠️ **No authentication** (relies on network isolation only)

### ⚠️ CRITICAL SECURITY WARNING

**Marco MUST NEVER be exposed to the public internet.**

- No built-in authentication in Phase 1
- Suitable ONLY for trusted internal network (`iccm_network`)
- Exposing Marco publicly creates severe security risk
- All security relies on Docker network isolation

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
- **Triplet Consultations:**
  - Design Review: `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_153405_a5c755ba/`
  - Documentation Review: `/mnt/projects/ICCM/fiedler/fiedler_output/20251004_155011_c0509ac2/`
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

### Version 1.1.0 (2025-10-04) - Triplet Review Revisions
- Added Phase 1 limitations section (single browser instance, no auth)
- Updated memory targets (500MB → 1GB idle, added 2GB Docker limit)
- Added structured JSON log examples
- Clarified request serialization for concurrent clients
- Added security warning (internal use only)
- Pinned Playwright MCP version (1.43.0)
- Added `marco_reset_browser` tool
- Documented health check response format
- Added configuration precedence note (ENV > YAML > defaults)
- Corrected tool list (removed `playwright_pdf`, pending verification)

### Version 1.0.0 (2025-10-04)
- Initial requirements and design
- Documentation created
- Implementation pending

---

**Status:** Documentation revised and approved - Ready for implementation
**Next Steps:**
1. Create stdio-WebSocket bridge library
2. Implement Marco WebSocket server
3. Create Dockerfile and docker-compose.yml
4. Test end-to-end integration
