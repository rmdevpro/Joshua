# Bug Fix: Fiedler MCP Server Not Working

**Date:** 2025-10-02
**Status:** ✅ FIXED - Verified working after Claude Code restart

## Problem

User reported: "fielder is not working as an MCP server"

## Investigation

1. **Container Status:** Container running healthy
   ```
   fiedler-mcp   Up About an hour (healthy)   0.0.0.0:9010->8080/tcp
   ```

2. **Initial Hypothesis:** Wrong file path (mcp_server.py vs server.py)
   - Found `mcp_server.py` exists but is 0 bytes (empty file)
   - Actual server code is in `server.py`

3. **Root Cause Discovery:**
   - `server.py` uses relative imports: `from .tools import ...`
   - Cannot be run directly as `python /app/fiedler/server.py`
   - Results in error: `ImportError: attempted relative import with no known parent package`

4. **Correct Method Found:**
   - Package installed via `pyproject.toml` with entry point: `fiedler = "fiedler.server:main"`
   - Should be invoked as `fiedler` command, not direct Python script
   - Test confirmed: `echo '{"jsonrpc": "2.0", "method": "initialize", ...}' | docker exec -i fiedler-mcp fiedler` works

## Change Made

**File:** `/home/aristotle9/.claude.json`

**Before:**
```json
"fiedler": {
  "command": "docker",
  "args": [
    "exec",
    "-i",
    "fiedler-mcp",
    "python",
    "/app/fiedler/mcp_server.py"
  ]
}
```

**After:**
```json
"fiedler": {
  "command": "docker",
  "args": [
    "exec",
    "-i",
    "fiedler-mcp",
    "fiedler"
  ]
}
```

## Verification Completed ✅

- [x] Restarted Claude Code
- [x] Confirmed Fiedler tools appear (8 tools: fiedler_list_models, fiedler_set_models, fiedler_set_output, fiedler_get_config, fiedler_send, fiedler_set_key, fiedler_delete_key, fiedler_list_keys)
- [x] Tested tool invocation: `fiedler_list_models` returned all 7 models successfully
  - gemini-2.5-pro, gpt-5, llama-3.1-70b, llama-3.3-70b, deepseek-r1, qwen-2.5-72b, grok-4
- [x] No errors - MCP integration fully functional

## Questions/Concerns

1. Why does `mcp_server.py` exist as an empty file?
2. Was the original documentation incorrect, or was something changed during deployment?
3. Need to understand if this is the right fix or if something else is wrong

## Rollback Instructions

If this doesn't work, revert `.claude.json` to:
```json
"fiedler": {
  "command": "docker",
  "args": ["exec", "-i", "fiedler-mcp", "python", "/app/fiedler/mcp_server.py"]
}
```
