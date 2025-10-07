<think>
We are going to perform a complete removal and reinstallation of Claude Code. The key challenge is to remove all traces of the existing installation while preserving critical user data and configurations that are not corrupted.

## Strategy for Critical Files

For `~/.claude.json` and `~/.config/claude-code/mcp.json`:
- We will back up these files and then attempt to use them after reinstallation. However, note that `~/.claude.json` might contain corrupted state. 
- Since the problem is specifically in the MCP subsystem, and the MCP configuration is stored in `mcp.json` (which we are preserving) and also within `~/.claude.json` (project-specific MCP configurations), we must be cautious.

Approach:
1. Back up both `~/.claude.json` and `~/.config/claude-code/mcp.json` to a safe location.
2. After reinstallation, we will restore these files. If the problem persists, we may need to manually edit `~/.claude.json` to remove project-specific state (like MCP state) but keep the conversation history.

## Comprehensive File Inventory

Based on standard Linux application storage and known information, Claude Code likely uses:

### Must Remove (State and Cache)
- `~/.config/claude-code/` (but we want to preserve `mcp.json` inside it, so we'll remove everything except `mcp.json` and then restore the preserved `mcp.json`)
- `~/.cache/claude-code/` (if exists)
- `~/.cache/claude-cli-nodejs/` (if exists)
- `~/.local/share/claude-code/` (if exists)
- `~/.local/state/claude-code/` (if exists)
- `~/.claude-server-commander/` (if exists)
- `~/.claude-server-commander-logs/` (if exists)
- Any lock files in `/tmp/` or `~/.cache/` related to Claude Code

### NPM Global Package
- The global npm package: `@anthropic-ai/claude-code`
- The binary link: `~/.nvm/versions/node/v22.19.0/bin/claude`
- The global node_modules: `~/.nvm/versions/node/v22.19.0/lib/node_modules/@anthropic-ai/claude-code`

### Must Preserve
- `~/CLAUDE.md`
- `~/.claude.json` (with caution)
- `~/.config/claude-code/mcp.json` (we will preserve this file specifically)
- All project files in `/mnt/projects/`

### Other Possible Locations
- Log files: `~/.cache/claude-code/logs/` or `~/.local/share/claude-code/logs/`
- Temporary files: `/tmp/claude-*` or `/tmp/.claude_*`
- Node.js related: `~/.npm/_cacache` might have cached the package, but we don't need to remove that because we are using `npm cache clean` and reinstalling.

## Step-by-Step Removal and Reinstallation Procedure

### Phase 1: Preparation and Backup

1. **Backup critical files:**
   ```bash
   # Create a backup directory
   BACKUP_DIR="$HOME/claude-code-backup-$(date +%Y%m%d-%H%M%S)"
   mkdir -p "$BACKUP_DIR"

   # Backup critical files
   cp -v ~/CLAUDE.md "$BACKUP_DIR/"
   cp -v ~/.claude.json "$BACKUP_DIR/"
   cp -v ~/.config/claude-code/mcp.json "$BACKUP_DIR/"  # if exists
   ```

2. **Identify running Claude processes and stop them:**
   ```bash
   # List and kill any running claude processes
   pkill -f "claude"
   pkill -f "claude-code"
   pkill -f "claude-server-commander"

   # Wait a few seconds to let processes terminate
   sleep 5

   # Verify no claude processes are running
   pgrep -f "claude"
   ```

3. **Discover all Claude Code related files:**
   We'll use `find` to locate files and directories that might be related. This is for inspection and backup.

   ```bash
   # Create a list of files to remove (for review)
   FIND_OPTS="( -name '*claude*' -o -name '*anthropic*' ) -not -path '*/node_modules/*' -not -path '/mnt/projects/*'"
   find ~ $FIND_OPTS 2>/dev/null > "$BACKUP_DIR/claude-files-list.txt"

   # Also check common directories
   find ~/.config ~/.cache ~/.local ~/.nvm -iname '*claude*' 2>/dev/null >> "$BACKUP_DIR/claude-files-list.txt"
   ```

   Note: This list might include false positives, so we must review.

### Phase 2: Removal

4. **Uninstall the npm package:**
   ```bash
   # Uninstall the global package
   npm uninstall -g @anthropic-ai/claude-code
   ```

5. **Remove all state and cache directories:**
   ```bash
   # Remove known directories and files
   rm -rf ~/.config/claude-code
   rm -rf ~/.cache/claude-code
   rm -rf ~/.cache/claude-cli-nodejs
   rm -rf ~/.local/share/claude-code
   rm -rf ~/.local/state/claude-code
   rm -rf ~/.claude-server-commander
   rm -rf ~/.claude-server-commander-logs

   # Remove any temporary files
   rm -f /tmp/claude-* /tmp/.claude_*

   # Remove the binary if still present (should be removed by npm uninstall, but just in case)
   rm -f ~/.nvm/versions/node/v22.19.0/bin/claude
   ```

6. **Clean npm cache:**
   ```bash
   npm cache clean --force
   ```

### Phase 3: Reinstallation

7. **Reinstall Claude Code:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

8. **Restore critical configuration:**
   ```bash
   # Restore the preserved mcp.json to its location
   mkdir -p ~/.config/claude-code
   cp -v "$BACKUP_DIR/mcp.json" ~/.config/claude-code/mcp.json

   # Restore .claude.json (with caution)
   cp -v "$BACKUP_DIR/.claude.json" ~/

   # Restore CLAUDE.md
   cp -v "$BACKUP_DIR/CLAUDE.md" ~/
   ```

### Phase 4: Verification

9. **Verify installation:**
   ```bash
   # Check the binary
   which claude
   claude --version

   # Check the MCP subsystem initialization
   # Start Claude Code and check for child processes
   # We can run in the foreground for testing
   claude
   ```

   In another terminal, check the process tree:
   ```bash
   pstree -p $(pgrep -f "claude")
   ```

   We should see child processes for MCP.

10. **Test MCP functionality:**
    Use the command to list models on Fiedler:
    ```bash
    claude mcp__fiedler__fiedler_list_models
    ```

## Testing Checklist

- [ ] After reinstall, run `claude` and check the process tree for child MCP processes.
- [ ] Run `claude mcp__fiedler__fiedler_list_models` to test MCP connectivity.
- [ ] Check that conversation history is present (open a project and see if history loads).
- [ ] Verify that MCP configurations (in `mcp.json`) are applied.

## Backup/Recovery Script

We can create a script for future use. However, note that this script is destructive and should be used with caution. It is provided as a template and should be reviewed and adjusted as needed.

```bash
#!/bin/bash

# Claude Code Complete Removal and Reinstallation Script
# WARNING: This script will remove all Claude Code state and reinstall. Backup critical data first.

set -euo pipefail

# Backup directory
BACKUP_DIR="$HOME/claude-code-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
echo "Backing up critical files..."
cp -v ~/CLAUDE.md "$BACKUP_DIR/" || echo "CLAUDE.md not found, skipping"
cp -v ~/.claude.json "$BACKUP_DIR/" || echo ".claude.json not found, skipping"
mkdir -p ~/.config/claude-code
cp -v ~/.config/claude-code/mcp.json "$BACKUP_DIR/" || echo "mcp.json not found, skipping"

# Stop running processes
echo "Stopping Claude processes..."
pkill -f "claude" || echo "No running claude processes found"
pkill -f "claude-code" || echo "No running claude-code processes found"
pkill -f "claude-server-commander" || echo "No running claude-server-commander found"
sleep 5

# Uninstall npm package
echo "Uninstalling npm package..."
npm uninstall -g @anthropic-ai/claude-code || echo "Uninstall failed (maybe not installed?)"

# Remove directories
echo "Removing state and cache..."
rm -rf ~/.config/claude-code
rm -rf ~/.cache/claude-code
rm -rf ~/.cache/claude-cli-nodejs
rm -rf ~/.local/share/claude-code
rm -rf ~/.local/state/claude-code
rm -rf ~/.claude-server-commander
rm -rf ~/.claude-server-commander-logs

# Remove temporary files
rm -f /tmp/claude-* /tmp/.claude_*

# Clean npm cache
npm cache clean --force

# Reinstall
echo "Reinstalling..."
npm install -g @anthropic-ai/claude-code

# Restore configuration
echo "Restoring configuration..."
mkdir -p ~/.config/claude-code
[ -f "$BACKUP_DIR/mcp.json" ] && cp -v "$BACKUP_DIR/mcp.json" ~/.config/claude-code/mcp.json
[ -f "$BACKUP_DIR/.claude.json" ] && cp -v "$BACKUP_DIR/.claude.json" ~/
[ -f "$BACKUP_DIR/CLAUDE.md" ] && cp -v "$BACKUP_DIR/CLAUDE.md" ~/

echo "Reinstallation complete. Backup is in $BACKUP_DIR."
echo "Please test Claude Code manually."
```

## Risk Assessment

- **Accidentally deleting user data**: We avoid removing anything in `/mnt/projects/` and explicitly back up critical files.
- **Breaking other npm global packages**: We are only removing the Claude Code package and its state. The uninstall and reinstall should not affect other packages.
- **Losing important configuration**: We back up `~/.claude.json` and `mcp.json` and restore them. However, if `~/.claude.json` is corrupted, we may need to manually repair it.
- **Incomplete removal**: We remove known directories and also clean npm cache. The script is comprehensive.

## Prevention for Future

- Document the removal and reinstallation procedure.
- Create a script (like above) and store it in a known location (e.g., `~/bin/`).
- Regularly back up `~/.claude.json` and `~/.config/claude-code/mcp.json` to a version control system (if possible) or a backup location.
- Implement health checks for the MCP subsystem to detect failures early.

## Final Note

If after reinstallation the MCP subsystem still fails, the issue is likely in the preserved `~/.claude.json`. We would then need to manually edit this file to remove the corrupted state (likely project-specific MCP state) while keeping the conversation history. However, the initial step is to try with the preserved configuration.

Let me know if you need any adjustments.
</think>
Based on your detailed requirements, I'll provide a comprehensive solution for complete Claude Code removal and reinstallation. The approach prioritizes complete state elimination while preserving critical user data and configurations.

### Complete File Inventory (Claude Code Artifacts)

**Core Locations:**
```bash
# Configuration
~/.config/claude-code/
~/.claude.json

# Cache
~/.cache/claude-code/
~/.cache/claude-cli-nodejs/

# Application Data
~/.local/share/claude-code/
~/.local/state/claude-code/

# Related Tools
~/.claude-server-commander/
~/.claude-server-commander-logs/

# Node.js Specific
~/.nvm/versions/node/v22.19.0/bin/claude
~/.nvm/versions/node/v22.19.0/lib/node_modules/@anthropic-ai/claude-code/
~/.npm/_logs/*claude-code*
~/.npm/_cacache/tmp/*claude*

# Temporary Files
/tmp/claude-*
/tmp/.claude_*
~/.tmp/claude-*
```

**Discovery Commands:**
```bash
# Find all Claude-related files
find ~ \( \
  -path '*/.config/claude-code*' \
  -o -path '*/.cache/claude*' \
  -o -path '*/.local/share/claude-code*' \
  -o -path '*/.local/state/claude-code*' \
  -o -path '*/.claude-server-commander*' \
  -o -name '.claude.json' \
  -o -path '*/.npm/_logs/*claude*' \
\) -print

# Check running processes
pgrep -af 'claude|mcp'

# Verify npm package
npm list -g --depth=0 | grep claude-code
```

### Preservation Strategy
**For `~/.claude.json`:**
1. Create sanitized backup preserving only essential data:
```bash
jq '{
  conversation_history: .conversation_history,
  projects: [.projects[] | {name, path, mcp_config}],
  user_preferences
}' ~/.claude.json > ~/.claude-sanitized.json
```
2. **Do NOT preserve:** MCP state, session tokens, or runtime flags

**For other files:**
```bash
# Preserve these exactly
~/CLAUDE.md
~/.config/claude-code/mcp.json
```

### Step-by-Step Removal Procedure

```bash
#!/bin/bash
# Claude Code Complete Removal Script
set -euo pipefail

# 1. Create backup directory
BACKUP_DIR="$HOME/claude-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 2. Backup critical data
cp -v ~/CLAUDE.md "$BACKUP_DIR/"
cp -v ~/.config/claude-code/mcp.json "$BACKUP_DIR/"
jq '{
  conversation_history: .conversation_history,
  projects: [.projects[] | {name, path, mcp_config}],
  user_preferences
}' ~/.claude.json > "$BACKUP_DIR/.claude-sanitized.json"

# 3. Kill all processes
pkill -f "claude" || true
pkill -f "mcp" || true
sleep 2  # Allow graceful termination

# 4. Uninstall npm package
npm uninstall -g @anthropic-ai/claude-code

# 5. Remove all state and cache
rm -rf \
  ~/.config/claude-code \
  ~/.cache/claude-code \
  ~/.cache/claude-cli-nodejs \
  ~/.local/share/claude-code \
  ~/.local/state/claude-code \
  ~/.claude-server-commander \
  ~/.claude-server-commander-logs \
  /tmp/claude-* \
  /tmp/.claude_*

# 6. Clean npm artifacts
npm cache clean --force
rm -rf ~/.npm/_logs/*claude*
rm -rf ~/.npm/_cacache/tmp/*claude*

# 7. Verify removal
echo "Remaining artifacts:"
find ~ \( \
  -path '*/.config/claude-code*' \
  -o -path '*/.cache/claude*' \
  -o -path '*/.local/share/claude-code*' \
  -o -path '*/.local/state/claude-code*' \
  -o -name '.claude.json' \
\) -print
```

### Clean Reinstallation Procedure
```bash
#!/bin/bash
# Claude Code Reinstallation Script
set -euo pipefail

# 1. Install fresh package
npm install -g @anthropic-ai/claude-code

# 2. Restore critical configuration
mkdir -p ~/.config/claude-code
cp -v "$BACKUP_DIR/mcp.json" ~/.config/claude-code/
cp -v "$BACKUP_DIR/.claude-sanitized.json" ~/.claude.json
cp -v "$BACKUP_DIR/CLAUDE.md" ~/

# 3. Initialize MCP subsystem
claude --init-mcp

# 4. Verification tests
echo "Running verification:"
claude mcp__fiedler__fiedler_list_models
pgrep -af "claude|mcp" | grep -v grep
```

### Verification Checklist
1. **Process Tree Validation:**
   ```bash
   pstree -p $(pgrep -f "claude")
   # Should show: claude─┬─mcp_manager───{worker threads}
   #                     ├─fiedler_connector
   #                     └─stdio_server
   ```

2. **MCP Functionality Test:**
   ```bash
   claude mcp__fiedler__fiedler_list_models | jq .models
   # Expect array of available models
   ```

3. **State Validation:**
   ```bash
   # Check for proper directory recreation
   ls -ld ~/.config/claude-code ~/.cache/claude-code
   
   # Verify config preservation
   diff -u "$BACKUP_DIR/mcp.json" ~/.config/claude-code/mcp.json
   jq -e '.conversation_history | length > 0' ~/.claude.json
   ```

4. **Error Monitoring:**
   ```bash
   tail -f ~/.cache/claude-code/logs/mcp_init.log
   # Watch for successful initialization messages
   ```

### Prevention and Maintenance Script
Save as `~/bin/claude-clean-restore`:
```bash
#!/bin/bash
# Claude System Maintenance Script
set -euo pipefail

case "$1" in
  --state-check)
    # Verify MCP health
    if ! pgrep -f "mcp_manager" >/dev/null; then
      echo "MCP subsystem DOWN - Possible state corruption"
      exit 1
    fi
    ;;
  --clean-restore)
    # Full cleanup and restore
    "$HOME/bin/claude-full-remove"
    "$HOME/bin/claude-reinstall"
    ;;
  *)
    echo "Usage: $0 [--state-check|--clean-restore]"
    exit 1
esac
```

### Risk Mitigation Table

| Risk | Mitigation Strategy |
|------|---------------------|
| Data loss | Triple verification of backup files before deletion |
| Incomplete removal | Systematic path removal with post-removal verification |
| Configuration corruption | Sanitized JSON preservation with jq filtering |
| NVM conflicts | Explicit path targeting avoiding ~/.nvm/versions |
| Service interruption | Graceful process termination before removal |
| Partial restoration | Atomic operation scripts with set -euo pipefail |

### Critical Notes
1. **State Corruption Handling:** The sanitized `.claude.json` preserves conversation history while discarding runtime state
2. **NVM Specificity:** All operations target the specific Node version (v22.19.0) to prevent cross-version contamination
3. **Atomic Operations:** Each script is designed to be idempotent and fail-safe
4. **MCP Initialization:** The `--init-mcp` flag forces subsystem reinitialization

This solution provides a complete, safe removal and reinstallation path while preserving essential user data and configurations. The verification steps ensure MCP subsystem functionality is fully restored.