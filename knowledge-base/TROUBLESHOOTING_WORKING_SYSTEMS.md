# Troubleshooting Working Systems Without Breaking Them

**Created:** 2025-10-09
**Purpose:** How to diagnose problems in systems that were working WITHOUT making them worse
**Philosophy:** Ready-Aim-Fire, not Fire-Ready-Aim

---

## 🔴 FIRST RULE: ASSUME IT'S NOT BROKEN WHERE YOU THINK IT IS

When a production system appears broken, the problem is rarely in the obvious place. Before modifying ANYTHING:
1. Prove the component is actually broken (not just appearing broken)
2. Understand the full data flow
3. Test each layer in isolation
4. Only then consider modifications

**Key Insight:** Most "broken" components are actually working fine - the problem is in the integration layer, configuration, or somewhere unexpected.

---

## The Ready-Aim-Fire Methodology

### READY: Gather Evidence Without Touching
- Observe current state
- Check logs
- Monitor network connections
- Read configuration files
- Document what you find

### AIM: Analyze and Isolate
- Test components in isolation
- Trace the data path
- Identify the exact failure point
- Form a hypothesis

### FIRE: Only Modify After Full Understanding
- Make minimal changes
- Have a rollback plan
- Test the specific fix
- Document what you did

---

## Case Study: MCP Relay Diagnosis

*Using the relay as an example of how to diagnose without destroying*

### The Symptom
"No tools available in Claude Code" - immediate assumption might be "relay is broken"

### The Diagnosis Process (Read-Only)

### Step 1: Verify Relay Process is Running

```bash
# Check if relay process exists
ps aux | grep mcp_relay | grep -v grep

# Expected output:
# aristotle9  890049  0.0  0.0 559204 30504 pts/3    Sl+  11:42   0:00 /home/aristotle9/mcp-relay/.venv/bin/python /home/aristotle9/mcp-relay/mcp_relay.py
```

**If not running:** Claude Code failed to start it (not a relay problem)
**If running:** Continue to Step 2

### Step 2: Check Backend Connections

```bash
# Get relay process PID
RELAY_PID=$(ps aux | grep mcp_relay.py | grep -v grep | awk '{print $2}')

# Check network connections
lsof -p $RELAY_PID 2>/dev/null | grep -E "(TCP|ESTABLISHED)"

# Or use ss
ss -antp | grep $RELAY_PID
```

**Expected:** Established connections to backend ports (9012, 9022, 9050, etc.)
**If connected:** Relay is working, continue to Step 3
**If not connected:** Check if backend containers are running

### Step 3: Test Relay Directly (Standalone)

```bash
# Test MCP protocol directly
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}' | \
  /home/aristotle9/mcp-relay/.venv/bin/python /home/aristotle9/mcp-relay/mcp_relay.py 2>&1 | head -20
```

**Expected output:**
```
2025-10-09 12:02:03,694 - INFO - Loaded 8 backends: ['dewey', 'godot', 'horace', ...]
2025-10-09 12:02:03,696 - INFO - MCP Relay ready
2025-10-09 12:02:03,718 - INFO - Connected to [backend]: ws://...
2025-10-09 12:02:03,722 - INFO - [backend] initialized successfully
```

### Step 4: Count Available Tools

```bash
# List all tools from relay
echo -e '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}\n{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}' | \
  /home/aristotle9/mcp-relay/.venv/bin/python /home/aristotle9/mcp-relay/mcp_relay.py 2>&1 | grep -c "tool"
```

**Expected:** 100+ tools (depends on connected backends)
**If tools present:** Relay is 100% functional, problem is Claude Code
**If no tools:** Check backend containers

### Step 5: Check Claude Code Integration

```bash
# Check if relay is child of Claude process
ps -f -p $RELAY_PID

# Check parent process
ps -f -p $(ps -o ppid= -p $RELAY_PID)
```

**Expected:** Parent process should be "claude"
**If true:** Claude started relay but isn't communicating with it
**If false:** Relay was started manually or by something else

### Step 6: Verify stdio Communication

```bash
# Check file descriptors (stdin/stdout/stderr)
ls -l /proc/$RELAY_PID/fd/ | head -5
```

**Expected:**
```
lrwx------ 1 aristotle9 aristotle9 64 Oct  9 12:01 0 -> socket:[21157992]  # stdin
lrwx------ 1 aristotle9 aristotle9 64 Oct  9 12:01 1 -> socket:[21157994]  # stdout
lrwx------ 1 aristotle9 aristotle9 64 Oct  9 12:01 2 -> socket:[21157996]  # stderr
```

Sockets indicate connection to parent process (Claude Code).

---

## Common Scenarios and Solutions

### Scenario 1: "No relay tools available in Claude Code"

**Diagnosis:**
1. Relay running? ✅
2. Backends connected? ✅
3. Tools available directly? ✅ (116 tools)
4. Claude Code communicating? ❌

**Conclusion:** Claude Code initialization issue, NOT a relay problem

**Fix:** Kill relay process to force Claude Code to restart it:
```bash
kill $RELAY_PID
# Claude Code should auto-restart it
```

### Scenario 2: "Some backend tools missing"

**Diagnosis:**
1. Check specific backend connection:
```bash
lsof -p $RELAY_PID | grep 9012  # Fiedler port
```

2. Check if backend container is running:
```bash
docker ps | grep fiedler-mcp
```

**Conclusion:** Backend container issue, NOT a relay problem

**Fix:** Restart the specific backend container:
```bash
docker restart fiedler-mcp
```

### Scenario 3: "Relay tools have wrong prefix"

**Remember:** Tools are prefixed with relay namespace from `.claude.json`:
- If relay registered as "iccm": tools are `mcp__iccm__*`
- If relay registered as "relay": tools are `mcp__relay__*`
- NOT prefixed with backend name

**Check configuration:**
```bash
grep -A 5 'mcpServers' ~/.config/claude-code/mcp.json
```

---

## What NOT to Do

### ❌ DON'T modify relay files
- Don't edit `/home/aristotle9/mcp-relay/mcp_relay.py`
- Don't edit `/home/aristotle9/mcp-relay/backends.yaml`
- Don't change relay virtual environment

### ❌ DON'T restart Claude Code
The relay supports dynamic reconnection. Restarting Claude Code is rarely the solution.

### ❌ DON'T assume relay is broken
In dozens of deployments, the relay has NEVER been the root cause. The problem is always:
- Claude Code MCP client issues
- Backend container problems
- Docker networking issues

### ❌ DON'T bypass the relay
Connecting directly to backends breaks the entire architecture.

---

## Quick Diagnostic Command

Run this one-liner to get relay health summary:

```bash
RELAY_PID=$(ps aux | grep mcp_relay.py | grep -v grep | awk '{print $2}'); \
echo "=== RELAY DIAGNOSIS ==="; \
echo "Process running: $([ -n "$RELAY_PID" ] && echo "✅ PID $RELAY_PID" || echo "❌")"; \
echo "Backend connections: $(lsof -p $RELAY_PID 2>/dev/null | grep -c ESTABLISHED) active"; \
echo "Tool count: $(echo -e '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}\n{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}' | /home/aristotle9/mcp-relay/.venv/bin/python /home/aristotle9/mcp-relay/mcp_relay.py 2>/dev/null | grep -o '"name"' | wc -l) tools available"
```

---

## Universal Principles for Production Diagnosis

### 1. Battle-Tested Components Are Rarely the Problem
If a component has been working in production for weeks/months, it's probably still working. The problem is likely:
- In the integration between components
- A configuration change
- An environmental change (network, permissions, resources)
- A dependent service failure

### 2. Follow the Data Path
Trace data flow systematically:
```
Input → Component A → Component B → Component C → Output
         ✅            ✅            ❌
```
Test each hop independently to find the exact failure point.

### 3. Test in Isolation Before Blaming
Can you make the "broken" component work in a standalone test?
- If YES: Component works, integration is broken
- If NO: Component is actually broken (rare)

### 4. Network Diagnostics Don't Lie
Tools like `lsof`, `ss`, `netstat` show objective truth:
- Connections established? Process is communicating
- Listening on port? Service is up
- No connections? Service or network issue

### 5. Read-Only First, Always
Diagnosis should be:
1. 90% reading/observing
2. 9% isolated testing
3. 1% actual modifications

---

## The Cost of "Fixing" Without Understanding

### What Happens When You Skip Diagnosis:

**Scenario:** System appears broken
**Impulsive Action:** Modify configuration/code
**Result:**
- Original problem remains (was elsewhere)
- New problem created by modifications
- Now you have TWO problems
- Can't roll back because you don't know what you changed
- System is worse than when you started

### Real Example from Today:

**Symptom:** No MCP tools available
**Assumption:** Relay must be broken
**Reality:** Relay had 116 tools working perfectly
**Actual Problem:** Claude Code initialization issue
**If we had modified relay:** Would have broken a working system

---

## Diagnostic Commands Toolbox

### For Any Process
```bash
# Is it running?
ps aux | grep [process_name]

# What's it connected to?
lsof -p [PID] | grep ESTABLISHED

# What's it listening on?
lsof -p [PID] | grep LISTEN

# What files does it have open?
lsof -p [PID]

# System call activity
strace -p [PID] -c
```

### For Docker Containers
```bash
# Container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Container logs
docker logs [container] --tail 100

# Container network
docker inspect [container] | grep -A 10 NetworkMode
```

### For Network Services
```bash
# Test connectivity
nc -zv hostname port

# Test service response
curl -v http://service/health

# Check routing
traceroute hostname
```

---

## When to Actually Modify

Only modify after you can answer:
1. ✅ What exactly is broken?
2. ✅ Why is it broken?
3. ✅ What will this change fix?
4. ✅ What could this change break?
5. ✅ How will I roll back if needed?

If you can't answer ALL five, keep diagnosing.

---

## The Diagnosis Mindset

**Wrong:** "It's not working, let me fix it"
**Right:** "It appears to not be working, let me understand why"

**Wrong:** "This component is broken"
**Right:** "This component appears broken, let me prove it"

**Wrong:** "I'll just try changing this"
**Right:** "I'll test this hypothesis with a read-only check first"

---

**Remember:** In production systems, the most dangerous person is the one who "fixes" things without understanding them. Deep diagnosis prevents shallow fixes that make things worse.

**Mantra:** Ready-Aim-Fire. Never Fire-Ready-Aim.