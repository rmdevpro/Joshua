Of course. This is a well-defined problem, and the detailed context is excellent. Based on your request, here is a comprehensive consultation and a set of procedures to safely and completely remove and reinstall Claude Code.

## Consultation & Strategy

This plan is designed around a core principle: **"Backup, Sanitize, Remove, Reinstall, Restore, Verify."** We will treat the potentially corrupt `~/.claude.json` file with surgical precision to preserve its valuable data while discarding the corrupted state.

### Answering Your Critical Questions

First, let's address your specific questions, as the answers will inform the script and procedures.

**1. Complete File Discovery:**
A Node.js/npm-based CLI tool like Claude Code primarily uses standard locations. The comprehensive list for your system (`/home/aristotle9`) would be:

*   **NPM Global Package:**
    *   **Package Files:** `~/.nvm/versions/node/v22.19.0/lib/node_modules/@anthropic-ai/claude-code/`
    *   **Binary Symlink:** `~/.nvm/versions/node/v22.19.0/bin/claude`
*   **User Configuration (XDG Spec):**
    *   `~/.config/claude-code/` (You've identified this)
*   **User Cache (XDG Spec):**
    *   `~/.cache/claude-code/`
    *   `~/.cache/claude-cli-nodejs/` (Good catch, likely from the underlying CLI framework)
*   **User State/Data (XDG Spec):**
    *   `~/.local/share/claude-code/` (For persistent data)
    *   `~/.local/state/claude-code/` (This is the most likely location for the **corrupted MCP state files**, lock files, or runtime data)
*   **Legacy/Home Directory Config:**
    *   `~/.claude.json` (The main state/config file you identified)
    *   `~/.claude-server-commander/` (Related tool state)
    *   `~/.claude-server-commander-logs/` (Related tool logs)
*   **Temporary Files:**
    *   `/tmp/claude-*` or `/tmp/claude-code-*` (Often used for sockets, lock files, or temporary process data)
*   **NPM Cache:**
    *   `~/.npm/_cacache/` (The global npm cache. We'll clear this to ensure a fresh download.)

**2. Preservation Strategy for `~/.claude.json`:**
Your intuition is correct. The best approach is **(B) Extract only specific data and rebuild the file.**

*   **Why not A?** Restoring the entire file is highly likely to reintroduce the corrupted state that is causing the MCP initialization failure.
*   **Why not C?** This violates the constraint to preserve conversation history.

**Our Strategy:** We will use a command-line JSON processor like `jq` to extract the `conversationHistory` and any other known-good configuration keys into a new, clean file. We will discard keys that might be related to runtime state (e.g., `activeProcesses`, `sessionState`, `mcpStatus`, etc. - these are hypothetical names for the kind of data that gets corrupted).

**3. Safe Removal Procedure:**
The safest order is:
1.  **Stop all related processes:** Ensure no Claude Code processes are running or trying to respawn.
2.  **Backup:** Create a timestamped archive of all identified files before touching anything.
3.  **Uninstall the npm package:** `npm uninstall -g @anthropic-ai/claude-code`. This is generally cleaner to do first, as it removes the binary and package files cleanly.
4.  **Remove residual files:** Manually delete all the configuration, cache, and state directories identified above.
5.  **Clear npm cache:** `npm cache clean --force` to ensure the next install is from a fresh download.

**4. Verification Before Removal:**
We will use `find` commands to list all files and directories that will be deleted. The script will present this list to you for confirmation before proceeding (a "dry run" a "wet run").

**5. Clean Reinstallation:**
The procedure will be:
1.  Run `npm install -g @anthropic-ai/claude-code`.
2.  Manually restore the preserved global `mcp.json` from your backup.
3.  Manually restore the *sanitized* `claude.json` containing only the history and essential settings.
4.  Launch Claude Code and verify the MCP subsystem initializes.

**6. Node.js/NVM Considerations:**
The process is well-contained within the NVM environment.
*   **NVM Cleanup:** No NVM-specific cleanup is needed beyond what's listed above. The files are all within `~/.nvm/...` or your home directory.
*   **NPM Cache:** Yes, clearing the npm cache (`npm cache clean --force`) is a crucial step to prevent reinstalling from a potentially corrupted cached package tarball.
*   **Global Artifacts:** The primary artifacts are the package directory and the binary symlink, which `npm uninstall -g` handles. Our manual cleanup will handle the rest.

**7. Prevention for Future:**
*   **Scripting:** The backup/recovery script we create today should be saved as `~/bin/reset-claude-code.sh`.
*   **Version Control:** Consider placing your non-sensitive configuration files (`mcp.json`) in a private Git repository for tracking changes.
*   **Documentation:** Add a section to your `~/CLAUDE.md` that documents the reset procedure and the location of the script.
*   **Early Detection:** A simple health check script could be written to periodically check `ps` for MCP child processes and alert you if they are missing after a startup.

**8. Risk Assessment:**
*   **Accidental Data Deletion:** Mitigated by a comprehensive, timestamped backup created at the very beginning of the script.
*   **Breaking Other NPM Packages:** Mitigated by specifically targeting `@anthropic-ai/claude-code` for uninstallation and only deleting Claude-specific config/cache files. Clearing the *entire* npm cache is safe; it just forces re-downloading of packages on next install.
*   **Losing Configuration:** Mitigated by explicitly backing up `~/.claude.json` and `~/.config/claude-code/mcp.json`.
*   **Incomplete Removal:** Mitigated by using a comprehensive `find` command based on our file inventory to hunt down all related files, not just the obvious ones.

---

## The Procedure: Scripts & Checklists

Here is the complete, actionable plan.

### Step 1: File Inventory & Backup Script

This script will perform the backup and show you what will be deleted.

**File:** `pre-removal-audit.sh`

```bash
#!/bin/bash
set -euo pipefail

# --- Configuration ---
# All paths are relative to the user's home directory.
# Using explicit paths for clarity and safety.
HOME_DIR="/home/aristotle9"
BACKUP_DIR="${HOME_DIR}/claude_code_backup_$(date +%Y%m%d_%H%M%S)"
NVM_NODE_PATH="${HOME_DIR}/.nvm/versions/node/v22.19.0"

# List of files/dirs to explicitly back up before any action
FILES_TO_PRESERVE=(
  "${HOME_DIR}/.claude.json"
  "${HOME_DIR}/.config/claude-code/mcp.json"
  "${HOME_DIR}/CLAUDE.md"
)

# List of patterns/locations to find for complete removal
# This is the search list for our "seek and destroy" mission
TARGETS_FOR_REMOVAL=(
  "${NVM_NODE_PATH}/lib/node_modules/@anthropic-ai" # Target the parent to be safe
  "${NVM_NODE_PATH}/bin/claude"
  "${HOME_DIR}/.config/claude-code"
  "${HOME_DIR}/.cache/claude-code"
  "${HOME_DIR}/.cache/claude-cli-nodejs"
  "${HOME_DIR}/.local/share/claude-code"
  "${HOME_DIR}/.local/state/claude-code"
  "${HOME_DIR}/.claude-server-commander"
  "${HOME_DIR}/.claude-server-commander-logs"
)

# --- 1. Backup Critical Files ---
echo "--- Step 1: Backing up critical files ---"
mkdir -p "${BACKUP_DIR}/preserved_configs"
echo "Backup directory created at: ${BACKUP_DIR}"

for f in "${FILES_TO_PRESERVE[@]}"; do
  if [ -e "$f" ]; then
    echo "Backing up: $f"
    cp -a "$f" "${BACKUP_DIR}/preserved_configs/"
  else
    echo "Warning: File to preserve not found, skipping: $f"
  fi
done
echo "Critical files backed up successfully."
echo

# --- 2. Sanitize .claude.json ---
echo "--- Step 2: Sanitizing .claude.json to extract safe data ---"
CLAUDE_JSON_BACKUP="${BACKUP_DIR}/preserved_configs/.claude.json"
SANITIZED_JSON="${BACKUP_DIR}/claude.json.sanitized"

if [ -f "${CLAUDE_JSON_BACKUP}" ]; then
  echo "Extracting 'conversationHistory' and project-specific MCP configs..."
  # This jq command creates a new JSON object containing ONLY the keys we specify.
  # Add any other known-good, non-state keys to this object if needed.
  jq '{ conversationHistory: .conversationHistory, projects: .projects }' "${CLAUDE_JSON_BACKUP}" > "${SANITIZED_JSON}"
  echo "Sanitized configuration saved to: ${SANITIZED_JSON}"
  echo "Please inspect this file. It will be used for restoration."
else
  echo "Warning: .claude.json backup not found. Cannot sanitize."
fi
echo

# --- 3. Dry Run: Identify All Files to be Removed ---
echo "--- Step 3: DRY RUN - Identifying all Claude Code artifacts for removal ---"
echo "The following files and directories will be deleted in the main script:"
echo "----------------------------------------------------------------------"
find "${TARGETS_FOR_REMOVAL[@]}" -mindepth 0 -prune 2>/dev/null || true
echo "----------------------------------------------------------------------"
echo "Additionally, the npm package '@anthropic-ai/claude-code' will be uninstalled."
echo "And the npm cache will be cleared."
echo
echo "Audit complete. If this looks correct, you can proceed with the main removal script."
```

### Step 2: Complete Removal, Reinstallation, and Restoration Script

This is the main script. **Run it only after reviewing the output of the audit script.** It is interactive and will ask for confirmation before deleting files.

**File:** `reinstall-claude-code.sh`

```bash
#!/bin/bash
set -euo pipefail

# --- Configuration (should match the audit script) ---
HOME_DIR="/home/aristotle9"
BACKUP_DIR="" # This will be set by the user
NVM_NODE_PATH="${HOME_DIR}/.nvm/versions/node/v22.19.0"
PACKAGE_NAME="@anthropic-ai/claude-code"

TARGETS_FOR_REMOVAL=(
  # NOTE: We do not include the npm module path here, as npm uninstall handles it.
  # We are removing the residual config/cache/state files.
  "${HOME_DIR}/.config/claude-code"
  "${HOME_DIR}/.cache/claude-code"
  "${HOME_DIR}/.cache/claude-cli-nodejs"
  "${HOME_DIR}/.local/share/claude-code"
  "${HOME_DIR}/.local/state/claude-code"
  "${HOME_DIR}/.claude-server-commander"
  "${HOME_DIR}/.claude-server-commander-logs"
)

# --- Main Execution ---
main() {
  echo "Claude Code Complete Removal and Reinstallation"
  echo "================================================="
  
  # --- Phase 0: User Input ---
  # shellcheck disable=SC2162
  read -p "Please enter the full path to your backup directory: " BACKUP_DIR
  if [ ! -d "${BACKUP_DIR}" ]; then
    echo "Error: Backup directory not found at '${BACKUP_DIR}'"
    exit 1
  fi
  SANITIZED_JSON="${BACKUP_DIR}/claude.json.sanitized"
  PRESERVED_MCP_JSON="${BACKUP_DIR}/preserved_configs/mcp.json"
  if [ ! -f "${SANITIZED_JSON}" ]; then
      echo "Error: Sanitized JSON file not found at '${SANITIZED_JSON}'"
      exit 1
  fi


  # --- Phase 1: Stop Processes ---
  echo -e "\n--- Phase 1: Stopping any running Claude Code processes ---"
  pkill -f "claude" || echo "No running Claude Code processes found."
  sleep 2

  # --- Phase 2: Removal ---
  echo -e "\n--- Phase 2: Removing Claude Code ---"
  echo "Step 2.1: Uninstalling npm package..."
  if npm list -g --depth=0 | grep -q "${PACKAGE_NAME}"; then
    npm uninstall -g "${PACKAGE_NAME}"
  else
    echo "Package ${PACKAGE_NAME} not found in global npm list. Skipping uninstall."
  fi

  echo -e "\nStep 2.2: Removing residual files and directories..."
  echo "The following will be PERMANENTLY DELETED:"
  find "${TARGETS_FOR_REMOVAL[@]}" -mindepth 0 -prune 2>/dev/null || true
  
  # shellcheck disable=SC2162
  read -p "ARE YOU SURE you want to delete these files? (y/N): " CONFIRM
  if [[ "${CONFIRM}" != "y" ]]; then
    echo "Aborted by user."
    exit 1
  fi

  # The actual deletion
  find "${TARGETS_FOR_REMOVAL[@]}" -mindepth 0 -prune -exec rm -rf {} + 2>/dev/null || true
  echo "Residual files removed."

  echo -e "\nStep 2.3: Clearing npm cache..."
  npm cache clean --force

  # --- Phase 3: Verification of Removal ---
  echo -e "\n--- Phase 3: Verifying Removal ---"
  if npm list -g --depth=0 | grep -q "${PACKAGE_NAME}"; then
    echo "ERROR: npm package still found!"
    exit 1
  else
    echo "✅ npm package successfully uninstalled."
  fi
  
  local found_files
  found_files=$(find "${TARGETS_FOR_REMOVAL[@]}" -mindepth 0 -prune 2>/dev/null || true)
  if [ -n "${found_files}" ]; then
      echo "ERROR: Some residual files were not removed:"
      echo "${found_files}"
      exit 1
  else
      echo "✅ All residual files and directories successfully removed."
  fi

  # --- Phase 4: Reinstallation ---
  echo -e "\n--- Phase 4: Clean Reinstallation ---"
  echo "Installing ${PACKAGE_NAME}..."
  npm install -g "${PACKAGE_NAME}"
  echo "✅ Claude Code reinstalled."

  # --- Phase 5: Restoration ---
  echo -e "\n--- Phase 5: Restoring Sanitized Configuration ---"
  echo "Restoring global MCP configuration..."
  mkdir -p "${HOME_DIR}/.config/claude-code"
  cp "${PRESERVED_MCP_JSON}" "${HOME_DIR}/.config/claude-code/mcp.json"
  echo "✅ mcp.json restored."

  echo "Restoring sanitized user configuration (history & projects)..."
  cp "${SANITIZED_JSON}" "${HOME_DIR}/.claude.json"
  echo "✅ .claude.json restored from sanitized backup."

  # --- Phase 6: Final Testing ---
  echo -e "\n--- Phase 6: Final Verification ---"
  echo "Reinstallation complete. Please perform the following manual tests:"
  echo "1. Launch Claude Code in a new terminal."
  echo "2. Check the process tree to confirm MCP child processes are running:"
  echo "   ps -ef --forest | grep -i claude"
  echo "3. Run a test command that requires the MCP subsystem:"
  echo "   claude mcp__fiedler__fiedler_list_models"
  echo "4. Verify your conversation history is present."
}

main
```

### Step 3: Testing Checklist

After running the `reinstall-claude-code.sh` script, follow this checklist to confirm success.

1.  **✅ Initial Launch:**
    *   Open a **new** terminal (to ensure the shell's command path is updated).
    *   Run `claude`. Does it start without any immediate errors related to initialization?

2.  **✅ MCP Subsystem Verification:**
    *   In another terminal, run: `ps -ef --forest | grep -i claude`
    *   **Expected Output:** You should see the main `claude` process with one or more child processes indented underneath it. You should no longer see "zero child processes."

3.  **✅ MCP Functionality Test:**
    *   Run the command you provided: `claude mcp__fiedler__fiedler_list_models`
    *   **Expected Output:** A list of models from the Fiedler MCP server, not an error related to the subsystem being unavailable.

4.  **✅ Data Preservation Verification:**
    *   Run a command to check your conversation history (e.g., `claude log` or whatever command is appropriate).
    *   **Expected Outcome:** Your previous conversation history is intact.
    *   Check that your project-specific configurations are still present.

5.  **✅ General Functionality:**
    *   Engage in a new conversation with Claude Code to ensure all functionality is working as expected.

This comprehensive plan provides a high degree of safety through backups and user confirmation while being thorough enough to eliminate the corrupted state causing your issue.
