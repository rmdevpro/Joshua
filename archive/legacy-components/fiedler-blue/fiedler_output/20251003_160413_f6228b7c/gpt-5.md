Short answer first: put Fiedler back into the claude-code config and run it over stdio via docker exec. Don’t use the Stable Relay, don’t use ~/.claude.json for the bare‑metal CLI, and don’t use "type": "ws". That’s why you’re seeing “no such tool” and no connection attempts.

What to change

1) Use the claude-code config file (this is the one bare‑metal claude-code actually reads):
~/.config/claude-code/mcp.json

2) Add Fiedler as an stdio server invoked through docker exec, matching your architecture’s blue solid line:

{
  "mcpServers": {
    "desktop-commander": {
      "command": "docker",
      "args": ["exec", "-i", "desktop-commander", "desktop-commander"]
    },
    "fiedler": {
      "command": "docker",
      "args": ["exec", "-i", "fiedler-mcp", "fiedler"]
    }
  }
}

Notes:
- Keep -i (stdin). Do not add -t (TTY), it will corrupt the stdio stream.
- If your Fiedler build requires an explicit stdio flag, change the args to one of these variants (pick the one your container supports):
  - ["exec", "-i", "fiedler-mcp", "fiedler", "--stdio"]
  - ["exec", "-i", "fiedler-mcp", "fiedler", "mcp", "stdio"]
  - ["exec", "-i", "fiedler-mcp", "fiedler", "--transport", "stdio"]

Why this will work when the 8 attempts didn’t

- Wrong file: bare‑metal claude-code doesn’t read ~/.claude.json. That file is for Claude Desktop/VS Code. Putting the WebSocket config there guaranteed “silent” failure and no connection attempts.
- Wrong transport key: even where WebSocket is supported, the transport type must be "websocket", not "ws". Using "ws" is ignored by clients.
- Architecture mismatch: your architecture explicitly uses direct docker exec (stdio). Publishing 9010 and proving WS reachability was useful for diagnostics, but irrelevant to the bare‑metal path you must use.

Verification

- Sanity check the server binary:
  docker exec -it fiedler-mcp which fiedler
  docker exec -it fiedler-mcp fiedler --help  (look for stdio flags; if present, pick the matching variant above)

- Restart claude-code and confirm tools appear. They should be named like:
  mcp__fiedler__fiedler_list_models

Optional WebSocket (only if you later switch clients)

If you ever do need WS and your client supports it, the correct stanza would be placed in ~/.config/claude-code/mcp.json (not ~/.claude.json) and must use "type": "websocket", for example:
"fiedler": {
  "transport": {
    "type": "websocket",
    "url": "ws://127.0.0.1:9010"
  }
}

But per your immutable architecture, the stdio/docker‑exec config above is the correct, working solution now.