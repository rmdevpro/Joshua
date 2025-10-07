# Claude Code UI - Web Interface for Claudette

**Status:** ✅ Operational
**Last Updated:** 2025-10-04
**Purpose:** Browser-based interface for containerized Claude Code (Claudette) with full conversation logging

---

## Overview

Claude Code UI (by siteboon) provides a responsive web interface that wraps Claudette, giving you browser-based access to your logged Claude Code sessions. All conversations still flow through KGB → Dewey → Winni for complete audit trail.

### Architecture

```
User's Browser (http://localhost:8080)
    ↓
Claude UI Container (port 3001)
    ↓ docker exec -i
Claudette Container (claude-code-container)
    ↓ ANTHROPIC_BASE_URL=http://kgb-proxy:8089
KGB HTTP Gateway
    ↓ Log to Dewey
    ↓ Forward to api.anthropic.com
Anthropic API
```

**Key Point:** The UI container only triggers commands via `docker exec`. The actual Claude process runs inside `claude-code-container`, so all logging remains intact.

---

## Features

- **Responsive Design** - Works on desktop, tablet, and mobile
- **Interactive Chat Interface** - Full conversation UI
- **File Explorer** - Browse and edit files with syntax highlighting
- **Git Integration** - View changes, stage, commit, switch branches
- **Session Management** - Resume conversations, manage multiple sessions
- **Complete Logging** - All conversations logged to Dewey/Winni (no bypass)

---

## Access

### Web Interface

**URL:** http://localhost:8080
**Alternative:** http://<your-server-ip>:8080 (for remote access)

### Mobile Access

The UI is fully responsive and works on mobile browsers when connected to your local network.

---

## Configuration

### Docker Compose

Location: `/mnt/projects/ICCM/claude-container/docker-compose.yml`

```yaml
claude-ui:
  build:
    context: ../claudecodeui
  image: iccm/claude-code-ui:latest
  container_name: claude-ui
  ports:
    - "8080:3001"
  networks:
    - iccm-network
  environment:
    - PORT=3001
    - CLAUDE_CLI_PATH=docker exec -i claude-code-container claude
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  depends_on:
    - claude-code
```

### Environment Variables

- `PORT=3001` - Backend API server port
- `CLAUDE_CLI_PATH=docker exec -i claude-code-container claude` - Command to execute Claude in container
- Docker socket mount enables `docker exec` commands

---

## Usage

### Start the UI

```bash
cd /mnt/projects/ICCM/claude-container
docker compose up -d claude-ui
```

### Stop the UI

```bash
cd /mnt/projects/ICCM/claude-container
docker compose stop claude-ui
```

### Restart the UI

```bash
cd /mnt/projects/ICCM/claude-container
docker compose restart claude-ui
```

### View Logs

```bash
docker logs claude-ui --tail 50 -f
```

---

## Verification

### Check Container Status

```bash
docker ps --filter "name=claude-ui"
```

Should show: `Up X minutes` with ports `0.0.0.0:8080->3001/tcp`

### Test Web Access

```bash
curl http://localhost:8080
```

Should return HTML (the UI frontend).

### Verify Conversation Logging

1. Use the web UI to have a conversation
2. Check Dewey logs for stored messages:
   ```bash
   docker logs dewey-mcp | grep "Stored message"
   ```
3. Verify conversations in Winni database

---

## Troubleshooting

### UI Not Loading

**Problem:** Can't access http://localhost:8080
**Solution:**
1. Check container is running: `docker ps | grep claude-ui`
2. Check logs: `docker logs claude-ui`
3. Rebuild if needed: `docker compose build --no-cache claude-ui && docker compose up -d claude-ui`

### Can't Execute Commands

**Problem:** UI shows "Command failed" or timeout errors
**Solution:**
1. Verify Claudette is running: `docker ps | grep claude-code-container`
2. Test docker exec manually: `docker exec -i claude-code-container claude --version`
3. Check Docker socket permissions

### No Conversation Logging

**Problem:** Conversations not appearing in Dewey
**Solution:**
1. The logging happens in Claudette, not the UI container
2. Verify Claudette → KGB → Dewey path is working
3. Check KGB logs: `docker logs kgb-proxy | grep -i error`
4. Check Dewey logs: `docker logs dewey-mcp --tail 50`

---

## Technical Details

### Source Repository

**Project:** claudecodeui by siteboon
**GitHub:** https://github.com/siteboon/claudecodeui
**Location:** `/mnt/projects/ICCM/claudecodeui/`

### Container Specs

- **Base Image:** `node:20-alpine`
- **Additional Tools:** Docker CLI, Python3, make, g++ (for native modules)
- **Frontend:** Vite + React
- **Backend:** Express + WebSocket server
- **Build Size:** ~300MB (with build dependencies)

### Ports

- **3001** - Backend API server (mapped to host 8080)
- **5173** - Frontend Vite dev server (not exposed in production)

---

## Comparison with Bare Metal Claude

| Feature | Bare Metal Claude | Claude UI (Claudette) |
|---------|------------------|----------------------|
| **Interface** | Terminal only | Browser + Mobile |
| **Logging** | None (emergency fallback) | Complete (KGB → Dewey) |
| **Access** | Local shell only | Any browser on network |
| **Session Persistence** | Terminal session only | Resume from any device |
| **File Explorer** | Command-line only | Visual tree with syntax highlighting |
| **Git Integration** | CLI commands | Visual diff, staging, commits |

---

## Security Considerations

1. **Docker Socket Access:**
   - UI container has access to Docker socket
   - Can execute `docker exec` commands
   - Only exposes Claudette, not host system

2. **Network Exposure:**
   - Port 8080 exposed on all interfaces (0.0.0.0)
   - For production: Use reverse proxy with authentication
   - For development: Firewall restricts to local network

3. **Conversation Privacy:**
   - All conversations logged to Winni database
   - Same audit trail as Claudette
   - No additional egress paths created

---

## Future Enhancements

- [ ] Add authentication/authorization layer
- [ ] HTTPS support with reverse proxy
- [ ] Multi-user session isolation
- [ ] Custom themes and UI customization
- [ ] Integration with other ICCM tools (Fiedler, Dewey UIs)

---

## Related Documentation

- **Claudette:** `/mnt/projects/ICCM/claude-container/README.md`
- **KGB Gateway:** `/mnt/projects/ICCM/kgb/README.md`
- **Architecture:** `/mnt/projects/ICCM/architecture/CURRENT_ARCHITECTURE_OVERVIEW.md`
- **Current Status:** `/mnt/projects/ICCM/CURRENT_STATUS.md`

---

## Quick Reference

**Start UI:**
```bash
cd /mnt/projects/ICCM/claude-container && docker compose up -d claude-ui
```

**Access UI:**
```
http://localhost:8080
```

**View Logs:**
```bash
docker logs claude-ui --tail 50 -f
```

**Stop UI:**
```bash
docker compose stop claude-ui
```

---

**Status:** ✅ Operational (2025-10-04)
**Access URL:** http://localhost:8080
