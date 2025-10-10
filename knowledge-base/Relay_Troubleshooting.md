# MCP Relay Troubleshooting Guide

## Overview
The MCP Relay is a battle-tested system that dynamically connects to backend MCP servers. This guide covers troubleshooting when tools aren't available or connections fail.

---

## Critical Rule: Don't Modify Relay

**The relay works perfectly - if tools aren't available, the problem is elsewhere.**

- ✅ Diagnose relay status
- ✅ Check backend health
- ✅ Restart backend containers
- ✅ Use relay tools
- ❌ Edit relay configuration
- ❌ Modify relay code
- ❌ "Fix" the relay itself

---

## Relay Architecture

**Location:** `/home/aristotle9/mcp-relay/`

**Key files (DO NOT EDIT):**
- `backends.yaml` - Backend configuration
- `mcp_relay.py` - Relay server code
- `.venv/` - Python virtual environment

**All MCP containers are LOCAL:**
- dewey-mcp, fiedler-mcp, horace-mcp, etc. run on `localhost`
- Backends.yaml points to `ws://localhost:PORT`
- Use `docker restart <container-name>` locally (NO SSH)

---

## Common Issues

### Issue 1: "No such tool available" Error

**Symptoms:**
- Tool call returns "no such tool" error
- Expected tools not showing up

**Diagnosis:**
```
mcp__iccm__relay_get_status
```

**Common causes:**
1. Tool name has relay namespace prefix
   - ❌ `fiedler_send`
   - ✅ `mcp__iccm__fiedler_send`
2. Backend not connected
3. Backend hasn't registered the tool

**Solution:**
- Check exact tool names in relay status
- See `/mnt/projects/Joshua/knowledge-base/MCP_TOOL_NAMING.md`

---

### Issue 2: Backend Not Connecting

**Symptoms:**
- Relay status shows backend disconnected
- Tools from specific backend unavailable

**Diagnosis:**
```bash
# Check if backend container is running
docker ps | grep <backend-name>-mcp

# Check backend logs
docker logs <backend-name>-mcp --tail 50
```

**Solution:**
```bash
# Restart the BACKEND container
docker restart <backend-name>-mcp

# Reconnect via relay
mcp__iccm__relay_reconnect_server
  name: "<backend-name>"
```

**DO NOT restart Claude Code or edit relay config.**

---

### Issue 3: Relay Tools Not Working

**Symptoms:**
- `relay_get_status` fails
- `relay_reconnect_server` not available

**95% likely causes:**
1. You're looking in wrong place
2. You broke something (check what you changed)
3. Relay itself is down (very rare)

**Diagnosis:**
```bash
# Check relay process
ps aux | grep relay

# Check relay is accessible
nc -zv localhost 9999  # (or relay port)
```

**Solution:**
1. Check what you last changed
2. Revert recent changes
3. Check backend container health
4. **Only if all else fails:** Ask user for permission to investigate relay

---

## Troubleshooting Workflow

**When tools aren't available:**

1. **Check relay status**
   ```
   mcp__iccm__relay_get_status
   ```

2. **Identify which backend**
   - Which tool is missing?
   - Which backend provides it?

3. **Check backend container**
   ```bash
   docker ps | grep <backend>-mcp
   docker logs <backend>-mcp --tail 20
   ```

4. **Restart backend (not relay)**
   ```bash
   docker restart <backend>-mcp
   ```

5. **Reconnect via relay**
   ```
   mcp__iccm__relay_reconnect_server
     name: "<backend>"
   ```

6. **Verify tools available**
   ```
   mcp__iccm__relay_get_status
   ```

---

## What NOT to Do

**Never do these without user approval:**
- ❌ Edit `backends.yaml`
- ❌ Modify `mcp_relay.py`
- ❌ Touch relay `.venv`
- ❌ Restart Claude Code
- ❌ "Fix" relay configuration
- ❌ Assume relay is the problem

**The relay has worked perfectly for dozens of tool discoveries. If it's not working, you're probably looking in the wrong place.**

---

## Emergency Escalation

**If genuinely stuck after trying above:**
1. Document what you tried
2. Show relay status output
3. Show backend logs
4. Ask user for guidance
5. **Do NOT modify relay**

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/MCP_TOOL_NAMING.md` - Tool naming conventions
- `/mnt/projects/Joshua/knowledge-base/File_System_Architecture.md` - Container paths

---

*Last Updated: 2025-10-10*
