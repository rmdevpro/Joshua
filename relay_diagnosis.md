# MCP Relay Tool Discovery Failure - Diagnosis Request

## Problem
MCP Relay V3.8 connects to backends but fails to discover tools from 3 out of 8 backends on initial connection.

## Current Status
- **Working**: Godot (7 tools), Horace (7 tools), Sergey (40 tools), Fiedler (8 tools)
- **Degraded**: Dewey (0 tools), Marco (0 tools), Playfair (0 tools)
- **Failed**: Gates (not running)

## Error Messages from relay_get_status
1. **Dewey**: "Tool discovery failed: Method not found: notifications/initialized"
2. **Marco**: "Tool discovery failed: Invalid response structure"
3. **Playfair**: "Tool discovery failed: Method 'notifications/initialized' is not supported"

## Key Observations
1. **Fiedler had the same problem initially** (0 tools at 18:40), but after reconnecting at 18:57, it discovered 8 tools and became healthy
2. This suggests a **timing or race condition** rather than a fundamental backend problem
3. The error messages mention `notifications/initialized` but this is sent AFTER handshake, not during tool discovery

## Relevant Code Flow (mcp_relay.py)
```
connect_backend() [line 313]
  → _perform_handshake() [line 255]
    → sends "initialize" request
    → receives response
    → sends "notifications/initialized" [line 275]
  → _fetch_and_validate_tools() [line 286]
    → discover_tools() [line 350]
      → sends "tools/list" request [line 357]
      → expects response with tools [line 364]
```

## Questions
1. Why would `tools/list` request fail with errors about `notifications/initialized`?
2. Is there a timing issue where relay sends `tools/list` before backend is ready?
3. Should relay wait/retry after sending `notifications/initialized` before calling `tools/list`?
4. Why does reconnecting fix the issue (as seen with Fiedler)?

## V3.8 Change (Wrong Fix?)
V3.8 modified tool change notification logic (lines 369-422) to track when NEW tools are added to routing table, but this doesn't address the initial discovery failure.

## Request
Please analyze this and suggest:
1. Root cause of tool discovery failures
2. Why reconnecting fixes it
3. Proper fix location and approach
