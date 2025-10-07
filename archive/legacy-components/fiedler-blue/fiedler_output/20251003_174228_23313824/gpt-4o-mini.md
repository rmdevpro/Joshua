To assist you with the complete removal and reinstallation of Claude Code while ensuring preservation of critical data, we will provide a structured approach that covers your requests comprehensively. Let's break this down into the necessary outputs.

### 1. Complete File Inventory

**Comprehensive List of Claude Code Files/Directories:**

#### Known Locations (Must Remove)
1. `~/.config/claude-code/` - Configuration files
2. `~/.cache/claude-code/` - Cache files
3. `~/.cache/claude-cli-nodejs/` - CLI cache
4. `~/.local/share/claude-code/` - Application data (if exists)
5. `~/.local/state/claude-code/` - State files (if exists)
6. `~/.claude-server-commander/` - Tool directory
7. `~/.claude-server-commander-logs/` - Logs related to the above tool

#### NPM Package Location (Must Remove)
- Global NPM package: `@anthropic-ai/claude-code`
  - Typically found in `~/.nvm/versions/node/v22.19.0/lib/node_modules/@anthropic-ai/claude-code`

#### User Data Locations (Must Preserve)
1. `~/CLAUDE.md` - Session instructions
2. `~/.claude.json` - User preferences and settings (contains potentially corrupted state)
3. `~/.config/claude-code/mcp.json` - Global MCP server configurations
4. All project files in `/mnt/projects/`

#### Shell Commands to Discover Files
You can use the following command to locate Claude Code-related files:

```bash
find ~ \( -name "claude*" -o -name "*claude-code*" \) -print
```

### 2. Step-by-Step Removal Script

#### Step 2.1: Backup Critical Files
```bash
mkdir -p ~/claude_backup
cp ~/CLAUDE.md ~/claude_backup/CLAUDE.md
cp ~/.claude.json ~/claude_backup/claude.json
cp ~/.config/claude-code/mcp.json ~/claude_backup/mcp.json
```

#### Step 2.2: Verify What Will Be Removed
```bash
echo "Files that will be removed:"
find ~/.config/claude-code
find ~/.cache/claude-code
find ~/.local/share/claude-code
find ~/.local/state/claude-code
find ~/.claude-server-commander
find ~/.claude-server-commander-logs
npm list -g --depth=0 | grep @anthropic-ai/claude-code
```

#### Step 2.3: Safely Remove All Claude Code Artifacts
```bash
rm -rf ~/.config/claude-code/ ~/.cache/claude-code/ ~/.local/share/claude-code/ ~/.local/state/claude-code/ ~/.claude-server-commander/ ~/.claude-server-commander-logs/
npm uninstall -g @anthropic-ai/claude-code
```

#### Step 2.4: Verification Steps to Ensure Complete Removal
Use the earlier `find` command to ensure that all files have been deleted:
```bash
find ~ \( -name "claude*" -o -name "*claude-code*" \) -print
```

### 3. Reinstallation Procedure

#### Clean Install Commands
```bash
npm install -g @anthropic-ai/claude-code
```

#### Restore Preserved Configurations
After installation, you can restore your configurations:
```bash
cp ~/claude_backup/claude.json ~/.claude.json
cp ~/claude_backup/mcp.json ~/.config/claude-code/mcp.json
```

#### Verification of MCP Subsystem Initialization
After restoring configurations, start Claude Code and verify initialization:
```bash
claude
```
Once running, check for processes:
```bash
ps aux | grep "mcp"
```

### 4. Testing Checklist

#### Verify Complete Removal
- Ensure that running `find` commands shows no remaining Claude Code files.
- Run `npm list -g --depth=0 | grep @anthropic-ai/claude-code` should return nothing.

#### Verify Successful Reinstall
- Check that Claude Code starts without errors.
- Ensure no npm install warnings/errors.

#### Confirm MCP Subsystem Working
- Test MCP functionality through the app dashboard or command line.

### 5. Backup/Recovery Script
```bash
#!/bin/bash

# Backup critical Claude Code files
mkdir -p ~/claude_backup
cp ~/CLAUDE.md ~/claude_backup/CLAUDE.md
cp ~/.claude.json ~/claude_backup/claude.json
cp ~/.config/claude-code/mcp.json ~/claude_backup/mcp.json

echo "Backup complete. Files saved in ~/claude_backup."

# Verify and Remove Claude Code Files
echo "Verifying files to remove..."
find ~/.config/claude-code ~/.cache/claude-code ~/.local/share/claude-code ~/.local/state/claude-code ~/.claude-server-commander ~/.claude-server-commander-logs/ 

echo "Removing Claude Code files..."
rm -rf ~/.config/claude-code/ ~/.cache/claude-code/ ~/.local/share/claude-code/ ~/.local/state/claude-code/ ~/.claude-server-commander/ ~/.claude-server-commander-logs/ 

echo "Uninstalling npm package..."
npm uninstall -g @anthropic-ai/claude-code

echo "Removal complete. Ensure all files are deleted using the find command."
```

### Considerations Regarding Preservation Strategy
- Considering the possibility of data corruption, it’s advisable to take option **B: Extract only specific data from `~/.claude.json`** if possible. You may want to create a temporary copy and clean it up as needed before restoring.

### Final Note
Ensure you have adequate backups before attempting the whole process. The scripts provided can be adjusted to fit your specific workflows and user preferences. Let me know if you need further customization!