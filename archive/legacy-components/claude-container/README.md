# Claudette - Containerized Claude Code with Full Logging

**Status:** ⚠️ **DEPRECATED - ARCHITECTURE OUTDATED**
**Last Updated:** 2025-10-06
**Deprecation Reason:** KGB HTTP Gateway eliminated (2025-10-06). Claudette needs rearchitecture to connect directly to MCP Relay.

**⚠️ WARNING:** This entire README describes an outdated architecture using KGB. Do not deploy until rearchitected to use direct MCP Relay connections like bare metal Claude Code.

---

## Overview

Claudette is a containerized deployment of Claude Code that routes all Anthropic API traffic through the KGB HTTP Gateway, enabling complete conversation logging to Dewey/Winni.

### Architecture

```
Claudette (Docker container)
    ↓ ANTHROPIC_BASE_URL=http://kgb-proxy:8089
KGB HTTP Gateway (reverse proxy)
    ↓ Forward to https://api.anthropic.com
    ↓ Log to Dewey
Dewey MCP Server
    ↓ Store in PostgreSQL
Winni Database (Irina 192.168.1.210)
```

### Key Features

1. **Complete Logging:** All Anthropic API conversations captured automatically
2. **Isolated Environment:** Runs in Docker container on iccm_network
3. **MCP Integration:** Connects to ICCM MCP servers via relay
4. **Pre-configured:** Theme and onboarding settings applied
5. **Persistent Storage:** Workspace and configs mounted from host

---

## Configuration

### Docker Compose (`docker-compose.yml`)

```yaml
services:
  claude-code:
    build: .
    image: iccm/claude-code:latest
    container_name: claude-code-container
    command: sleep infinity  # Keep container alive
    networks:
      - iccm-network
    volumes:
      - /mnt/projects:/mnt/projects
      - ./config:/root/.config/claude-code
    environment:
      - ANTHROPIC_BASE_URL=http://kgb-proxy:8089
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Claude Config (`config/claude.json`)

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sequential-thinking"]
    },
    "iccm": {
      "type": "stdio",
      "command": "/mnt/projects/ICCM/mcp-relay/mcp_relay.py",
      "args": []
    }
  },
  "hasTrustDialogAccepted": true,
  "theme": "dark",
  "hasCompletedOnboarding": true
}
```

### MCP Relay Backends (`config/backends.yaml`)

```yaml
backends:
  - name: fiedler
    url: ws://kgb-proxy:9000?upstream=fiedler
    # Routes through KGB for logging

  - name: dewey
    url: ws://kgb-proxy:9000?upstream=dewey
    # Routes through KGB for logging
```

---

## Usage

### Start Claudette

```bash
cd /mnt/projects/ICCM/claude-container
docker compose up -d
```

### Execute Claude Commands

```bash
# Run Claude in container
docker exec claude-code-container claude "Your prompt here"

# Interactive session
docker exec -it claude-code-container claude

# Check status
docker ps --filter "name=claude-code"
```

### Stop Claudette

```bash
cd /mnt/projects/ICCM/claude-container
docker compose down
```

---

## Verification

### 1. Check Container Status

```bash
docker ps --filter "name=claude-code-container"
```

Should show: `Up X minutes`

### 2. Verify Gateway Connection

```bash
# Check KGB gateway health
curl http://localhost:8089/health

# View gateway logs
docker logs kgb-proxy --tail 20
```

Should show: `"status": "healthy"`

### 3. Verify Conversation Logging

```bash
# Check Dewey logs for stored conversations
docker logs dewey-mcp --tail 20 | grep "Stored message"
```

Should show: `Stored message <id> in conversation <conv_id>`

### 4. Test End-to-End

```bash
# Send test query
docker exec claude-code-container claude "What is 2+2?"

# Check KGB logs for 200 response
docker logs kgb-proxy | grep "200"

# Check Dewey for conversation
docker logs dewey-mcp | grep "Began new conversation"
```

---

## Troubleshooting

### Container Exits Immediately

**Problem:** Container stops after starting
**Cause:** Command fails (e.g., `tail -f` syntax error)
**Solution:** Use `command: sleep infinity` in docker-compose.yml

### Gateway Returns 403 Forbidden

**Problem:** Cloudflare blocks proxied requests
**Cause:** Missing SSL/TLS connector in aiohttp
**Solution:** Already fixed in KGB HTTP Gateway (SSL context added)

### MCP Tools Not Available

**Problem:** `mcp__iccm__*` tools missing
**Cause:** MCP relay not connected or config missing
**Solution:**
1. Check `config/claude.json` has "iccm" mcpServer
2. Verify `backends.yaml` is mounted correctly
3. Check MCP relay is executable: `chmod +x /mnt/projects/ICCM/mcp-relay/mcp_relay.py`

### No Logging to Dewey

**Problem:** Conversations not appearing in Dewey
**Cause:** KGB not forwarding logs or Dewey connection issue
**Solution:**
1. Check KGB logs: `docker logs kgb-proxy | grep -i error`
2. Verify Dewey is running: `docker ps | grep dewey`
3. Test Dewey connection: `docker exec kgb-proxy ping dewey-mcp`

---

## Key Differences from Bare Metal Claude

| Feature | Bare Metal Claude | Claudette (Containerized) |
|---------|------------------|---------------------------|
| **Anthropic API** | Direct to api.anthropic.com | Through KGB Gateway |
| **Logging** | None | All conversations logged |
| **MCP Connections** | Direct WebSocket | Through KGB Proxy |
| **Environment** | Host system | Isolated container |
| **Use Case** | Development, emergency fallback | Production with audit trail |

---

## Files and Directories

```
claude-container/
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Container orchestration
├── README.md              # This file
└── config/                # Mounted configuration
    ├── claude.json        # Claude Code settings
    └── backends.yaml      # MCP relay backends
```

---

## Network Architecture

Claudette participates in the `iccm_network` Docker bridge:

```
Docker Network: iccm_network
├── claude-code-container (Claudette)
├── kgb-proxy (Gateway + Spy)
├── fiedler-mcp (LLM Orchestra)
└── dewey-mcp (Conversation Storage)
```

**Container Communication:**
- Claudette → KGB: HTTP/WebSocket (internal Docker network)
- KGB → Anthropic: HTTPS (external internet)
- KGB → Dewey: WebSocket (internal Docker network)
- Dewey → Winni: PostgreSQL (192.168.1.210:5432)

---

## Security Considerations

1. **API Key Protection:**
   - API key passed via environment variable
   - Redacted before logging (KGB sanitizes headers)
   - Never persisted to disk in logs

2. **Network Isolation:**
   - Container runs on isolated bridge network
   - Only KGB gateway exposed on host (ports 8089, 9000)
   - Winni database on private network (Irina)

3. **Audit Trail:**
   - Complete conversation history in Dewey/Winni
   - Request/response pairs with timestamps
   - Metadata includes source, client info

---

## Performance Notes

- **Latency:** Minimal overhead (<50ms) from proxy
- **Logging:** Asynchronous (doesn't block API responses)
- **Storage:** Conversations truncated to 10KB per message
- **Resources:** Container uses ~200MB RAM idle

---

## Future Enhancements

1. **Default Mode:** Consider making Claudette the primary Claude instance
2. **MCP Tool Routing:** Add intelligent routing between direct/logged modes
3. **Conversation Export:** Bulk export tools for Dewey conversations
4. **Multi-Instance:** Run multiple Claudette containers for different projects

---

## Related Documentation

- **KGB HTTP Gateway:** `/mnt/projects/ICCM/kgb/README.md`
- **Anthropic Gateway Implementation:** `/mnt/projects/ICCM/ANTHROPIC_GATEWAY_IMPLEMENTATION.md`
- **MCP Relay:** `/mnt/projects/ICCM/mcp-relay/README.md`
- **Dewey MCP Server:** `/mnt/projects/ICCM/dewey/README.md`
- **Current Status:** `/mnt/projects/ICCM/CURRENT_STATUS.md`

---

## Quick Reference

**Start Claudette:**
```bash
cd /mnt/projects/ICCM/claude-container && docker compose up -d
```

**Run Command:**
```bash
docker exec claude-code-container claude "Your prompt"
```

**View Logs:**
```bash
docker logs kgb-proxy --tail 20        # Gateway logs
docker logs dewey-mcp --tail 20        # Storage logs
docker logs claude-code-container      # Claudette logs
```

**Stop Claudette:**
```bash
cd /mnt/projects/ICCM/claude-container && docker compose down
```

---

**Status:** ✅ Operational and verified (2025-10-04)
**Verified Conversations:** Multiple logged successfully (e.g., `b02ea596-74fe-4919-b2a5-d8630751fd6d`)
