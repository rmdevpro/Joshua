Short answer: this isn’t a network or config-syntax problem; the MCP loader inside Claude Code is not executing at all. The two most common, evidence-consistent causes are:
- MCP feature got globally disabled or stuck behind a trust/permission gate, so the loader never runs.
- One stdio MCP entry (e.g., using npx) fails to resolve/spawn in the current process environment (missing PATH/NVM), and the loader aborts before attempting any other servers (including WebSocket). This perfectly matches “no child processes” and “no connection attempts.”

Below is a focused plan to identify which of these is true and then fix it.

1) Root-cause analysis (ranked by likelihood)
- Global MCP disabled or blocked by a persisted “deny”/untrusted state
  - Symptom match: zero spawn attempts, zero logs, same configs, worked earlier.
  - Trigger: app update, settings toggle, or a denied trust prompt cached.
- PATH / npx resolution failure causing MCP bootstrap to abort
  - Your stdio servers depend on npx/python/venv. If Claude Code was launched from an environment where nvm PATH isn’t present, the first spawn attempt can throw and stop the whole MCP init, so even WebSocket servers won’t be attempted. The previous (working) session could have been launched from an interactive shell with nvm initialized, the current one not.
- Config discovery/state corruption
  - XDG paths changed or stale lock/permission-state is preventing initialization. If Claude Code isn’t even reading your config or thinks MCP is “off” via a persisted flag/lock, you’ll see exactly this behavior.

2) Diagnostics (run in order; stop when you find the smoking gun)
A. Confirm the Claude Code process environment
- Print the current process environment:
  - tr '\0' '\n' < /proc/2396980/environ | egrep '(^PATH=|^NVM|^NODE|XDG_CONFIG_HOME|^HOME=|MCP|CLAUDE|ANTHROPIC)'
  - Check that PATH includes your nvm bin, e.g. /home/aristotle9/.nvm/versions/node/v22.19.0/bin. If not present, it’s a prime suspect.
- Compare to your normal login shell:
  - echo "$PATH"
  - which npx; npx -v
  - If the app was launched from a GUI or different shell profile, it often lacks NVM environment.

B. Verify Claude Code is actually reading your MCP configs
- Validate JSON (ensures no silent parse abort):
  - jq . ~/.config/claude-code/mcp.json
  - jq . ~/.claude.json
- strace a fresh launch to confirm which files it reads:
  - pkill -f 'claude-code'  # stop all instances
  - env ANTHROPIC_LOG_LEVEL=debug CLAUDE_CODE_LOG_LEVEL=debug strace -f -o /tmp/cc.trace -s 200 -e openat,stat,read claude-code
  - grep -E 'claude-code/mcp.json|\.claude\.json' /tmp/cc.trace
  - If neither path appears, check XDG_CONFIG_HOME in the process env and look there; otherwise it isn’t reading your config.

C. Check for feature-gate/permissions disabling MCP
- Search for MCP-related toggles in Claude Code’s config/state:
  - grep -RniE 'mcp|enable|disabled|permission|trust' ~/.config/claude-code ~/.local/state/claude-code ~/.cache/claude-code 2>/dev/null
  - Look for keys like mcpEnabled, mcp.disabled, deniedServers, permissions.json or a similar allow/deny list.
- If you find a file marking MCP disabled or a deny-list including your servers, remove/rename it (back it up first).

D. Minimal config isolation
- Temporarily move the project config out of the way:
  - mv ~/.claude.json ~/.claude.json.bak
- Reduce global config to just the WebSocket Fiedler (no stdio servers) to test for a spawn-abort on stdio:
  - Create ~/.config/claude-code/mcp.json with only:
    {
      "mcpServers": {
        "fiedler": {
          "transport": { "type": "ws", "url": "ws://localhost:8000?upstream=fiedler" }
        }
      }
    }
- Restart Claude Code and watch logs (see Section 5 below). If you now see connection attempts or tools, the issue is a stdio server failing earlier and aborting the loader.

E. Absolute-path test for stdio servers
- If D succeeds, restore stdio servers one by one, but specify absolute paths:
  - Find your npx path:
    - command -v npx  # expect /home/aristotle9/.nvm/versions/node/v22.19.0/bin/npx
  - In mcp.json, change e.g.:
    "desktop-commander": { "command": "/home/aristotle9/.nvm/versions/node/v22.19.0/bin/npx", "args": ["-y", "@executeautomation/desktop-commander-mcp"] }
- Restart and verify. If it works with absolute paths, your PATH was the root cause.

F. Locks/state
- Look for stale locks/pids:
  - find ~/.config/claude-code ~/.local/state/claude-code ~/.cache/claude-code -maxdepth 2 -type f -iregex '.*(lock|\.pid|mcp.*state.*|permissions.*|trust.*)'
  - If present, stop Claude Code and remove them, then relaunch.

3) Recommended solution (apply what matches your findings)
Case 1: PATH/npx not available to Claude Code
- Fix the PATH for the app:
  - Launch it from a login shell that loads NVM: bash -lc 'claude-code'
  - Or define absolute command paths for each stdio MCP in the config (preferred for robustness).
  - Or add PATH explicitly per server:
    "desktop-commander": {
      "command": "/home/aristotle9/.nvm/versions/node/v22.19.0/bin/npx",
      "args": ["-y", "@executeautomation/desktop-commander-mcp"],
      "env": { "PATH": "/home/aristotle9/.nvm/versions/node/v22.19.0/bin:/usr/bin:/bin" }
    }
- After this, restore your full config incrementally.

Case 2: MCP disabled or blocked by permissions/trust state
- Remove the deny/disabled file you found (backup first) and restart.
- If there is a UI setting “Enable MCP servers,” turn it back on and restart.
- If there is a trust/permissions store (allow/deny per server), reset it by removing the permissions file and re-allow when prompted.

Case 3: Config discovery/XDG mismatch
- If strace shows Claude Code reading a different config root, move mcp.json there or set XDG_CONFIG_HOME so it reads ~/.config/claude-code/mcp.json.
- Keep only one active source of MCP configuration during testing (prefer the global file) to avoid overrides.

Case 4: Stale lock/corrupted cache
- With Claude Code stopped:
  - rm -rf ~/.cache/claude-code
  - rm -rf ~/.local/state/claude-code  # if present
  - Remove any mcp.*lock/permissions.* files in ~/.config/claude-code
- Restart Claude Code.

4) Verification
- Process tree:
  - For stdio servers: you should see child processes like node or npx spawned under the claude-code PID.
  - For WebSocket servers: you won’t see children for Fiedler (it’s remote), but you should see:
    - Claude Code logs showing “connecting ws://localhost:8000?upstream=fiedler”
    - Fiedler/Relay/KGB logs with new incoming connections
- In Claude Code, list tools; fiedler_* should appear. You can also exercise a simple tool like fiedler_get_config or fiedler_list_models.
- If using logs:
  - tail -f ~/.config/claude-code/logs/*  # or check where your install writes logs
  - Expect lines about “MCP subsystem initialized,” “loading N servers,” per-server init, and WS connect attempts.

5) How to get diagnostic logs
- Try launching with debug env:
  - ANTHROPIC_LOG_LEVEL=debug CLAUDE_CODE_LOG_LEVEL=debug claude-code
  - If there’s an MCP-specific flag, also set MCP_LOG_LEVEL=debug (harmless if ignored).
- If the app writes logs to XDG state or config dirs, check:
  - ~/.config/claude-code/logs
  - ~/.local/state/claude-code/logs
  - If nothing appears, the strace in step B is the most reliable way to see what it reads and where it fails.

6) Prevention
- Pin absolute paths for stdio MCP servers (npx/node/python/venv) in your config so GUI/launcher environments don’t break spawns when PATH differs.
- Keep WebSocket servers separate in config so a broken stdio spawn can’t block them; during init you can test “remote-first.”
- Add a startup self-check:
  - A small script that, on Claude Code launch, verifies:
    - PATH contains NVM bin (or absolute paths exist)
    - npx -v works
    - ws endpoints are reachable (optional)
- Monitor:
  - Add a watchdog that tails Claude Code logs and Relay/KGB logs; alert if no MCP connect attempts within N seconds after startup.
- Version pinning and change control:
  - After updates, run the minimal-config D step to ensure MCP bootstrap still works.
  - Back up and track ~/.config/claude-code and ~/.claude.json alongside your repo.

Concrete “fast path” to unblock you now
1) Minimal test (WS only)
- Move project config out:
  - mv ~/.claude.json ~/.claude.json.bak
- Reduce global config to only Fiedler WS (as in D).
- Stop Claude Code, ensure no processes remain, then start with:
  - ANTHROPIC_LOG_LEVEL=debug CLAUDE_CODE_LOG_LEVEL=debug bash -lc 'claude-code'
- If you now see WS connection attempts, the blocker was stdio spawn.

2) Bring back stdio with absolute paths
- For each stdio server, set command to the full path of npx or the interpreter in your venv.
- Optionally set an explicit PATH in the server’s env.

3) If still no attempts/logs
- Remove cache/state/locks under:
  - ~/.cache/claude-code
  - ~/.local/state/claude-code
  - Any “mcp.*lock/permissions.*/trust.*” files in ~/.config/claude-code
- Re-run with debug env, verify with strace that mcp.json is read.

Why it worked 17 hours ago but not now
- Most plausibly you launched Claude Code from a login shell (NVM initialized) previously, and from a GUI/session without NVM PATH this time, causing the first stdio spawn to fail and MCP bootstrap to abort, which suppresses even WS connects. The identical config then “appears” broken.
- Alternatively, a setting/permission flip or stale lock disabled MCP between runs.

If you run the minimal WS-only config and it still never attempts to connect, focus on: MCP-disabled settings/permissions and config discovery (XDG paths), then stale locks/state.