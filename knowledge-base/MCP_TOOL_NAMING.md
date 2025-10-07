# MCP Tool Naming Convention and Troubleshooting

**Date:** 2025-10-07
**Status:** Active Reference
**Category:** Troubleshooting / MCP Infrastructure

---

## Problem Statement

**Symptom:** When attempting to call MCP tools provided by backend servers through the relay, tools appear to be unavailable even though:
- The relay shows the backend is connected and healthy
- The relay reports tools discovered (e.g., 8 tools for Fiedler)
- `relay_get_status` shows all servers healthy with tool names listed

**Common Error:**
```
Error: No such tool available: mcp__fiedler__fiedler_get_config
```

---

## Root Cause

The relay MCP server is registered in `.claude.json` with a **namespace**, and all tools from backends are prefixed with that namespace, not the backend name.

**Example from `.claude.json`:**
```json
"mcpServers": {
  "iccm": {
    "type": "stdio",
    "command": "/home/aristotle9/mcp-relay/.venv/bin/python",
    "args": ["/home/aristotle9/mcp-relay/mcp_relay.py"]
  }
}
```

In this configuration, the relay is named **"iccm"**, so ALL tools from ALL backend servers are prefixed with `mcp__iccm__`, not `mcp__<backend-name>__`.

---

## Solution

**Incorrect tool call:**
```
mcp__fiedler__fiedler_get_config  ❌
```

**Correct tool call:**
```
mcp__iccm__fiedler_get_config  ✅
```

**Pattern:**
- Tool prefix = `mcp__<relay-namespace>__<backend-tool-name>`
- NOT `mcp__<backend-name>__<tool-name>`

---

## How to Diagnose

### Step 1: Check Relay Status
```
Use tool: mcp__iccm__relay_get_status
```

This will show:
- All connected backends
- Tool count per backend
- **Tool names** as they're actually available

### Step 2: Identify the Relay Namespace

Check `.claude.json` on the local machine:
```bash
grep -A 5 'mcpServers' ~/.claude.json
```

Look for the key name (e.g., "iccm", "relay", etc.) - this is your namespace.

### Step 3: Use Correct Prefix

All tools are available as:
```
mcp__<namespace>__<tool-name>
```

---

## Common Tool Patterns

If relay namespace is **"iccm"**:

| Backend | Tool Name | Correct Call |
|---------|-----------|--------------|
| Fiedler | fiedler_send | `mcp__iccm__fiedler_send` |
| Dewey | dewey_get_conversation | `mcp__iccm__dewey_get_conversation` |
| Godot | godot_logger_log | `mcp__iccm__godot_logger_log` |
| Horace | horace_register_file | `mcp__iccm__horace_register_file` |
| Marco | browser_navigate | `mcp__iccm__browser_navigate` |
| Playfair | playfair_create_diagram | `mcp__iccm__playfair_create_diagram` |
| Gates | gates_create_document | `mcp__iccm__gates_create_document` |

---

## What NOT to Do

### ❌ Don't Blame the Relay

The relay is working correctly:
- It's discovering tools
- It's connecting to backends
- It's reporting status accurately

The issue is always **incorrect tool name prefix**.

### ❌ Don't Restart Claude Code

Restarting Claude Code won't fix a naming issue. The tools are already available, just with a different prefix than expected.

### ❌ Don't Modify Relay Files

Per CLAUDE.md:
> **🔴🔴🔴 RULE #1: DO NOT FUCK WITH RELAY 🔴🔴🔴**

The relay configuration is correct. This is a naming convention issue, not a relay bug.

---

## Testing Tool Availability

**Quick test to verify a backend is working:**

```python
# Test Fiedler (replace 'iccm' with your relay namespace)
mcp__iccm__fiedler_get_config

# Expected response:
{
  "models": [...],
  "output_dir": "...",
  "total_available_models": N
}
```

If this works, all Fiedler tools are available with the `mcp__iccm__` prefix.

---

## Resolution Checklist

When you encounter "No such tool available" errors:

- [ ] Check relay status with `mcp__iccm__relay_get_status`
- [ ] Verify relay shows backend connected and healthy
- [ ] Verify relay shows tools discovered
- [ ] Check `.claude.json` for relay namespace
- [ ] Update tool calls to use correct prefix: `mcp__<namespace>__<tool-name>`
- [ ] Test one tool to confirm pattern
- [ ] Update all tool calls in code/documentation

**Do NOT:**
- [ ] ~~Restart Claude Code~~
- [ ] ~~Modify relay files~~
- [ ] ~~Remove and re-add backends~~
- [ ] ~~Blame the relay~~

---

## Historical Context

This issue has occurred multiple times during development, typically when:
1. New backend servers are added
2. Backend tools are renamed
3. Sessions span multiple days (forget the pattern)

The pattern is always the same: relay works correctly, tools are available, just with the wrong prefix assumed.

---

## Related Documentation

- CLAUDE.md - Section: "🔴🔴🔴 RULE #1: DO NOT FUCK WITH RELAY"
- `/home/aristotle9/mcp-relay/backends.yaml` - Backend configuration
- `.claude.json` - MCP server namespace configuration

---

**Key Takeaway:** The relay namespace ("iccm") prefixes ALL tools from ALL backends. Use `relay_get_status` to see exact tool names.
