# SSHFS Projects Mount Setup

**Date:** 2025-10-07
**Status:** Active Reference
**Category:** Infrastructure / Development Environment

---

## Overview

The `/mnt/projects/` directory on the local development machine is an **SSHFS mount** of the remote server's `/mnt/projects/` directory. This allows direct file access to git repositories and project files stored on the physical server (192.168.1.210) without needing SCP or manual file transfers.

---

## Purpose

**Why SSHFS mount instead of local files?**

1. **Single Source of Truth:** All project files live on the physical server
2. **Git repositories work correctly:** Git operations happen on the remote server where repos are located
3. **No sync issues:** File changes are immediately visible on both local and remote
4. **Transparent access:** Read/Write/Edit tools work directly on mounted paths
5. **Backup strategy:** Centralized storage on the physical server with RAID

---

## Mount Configuration

### Source and Destination

- **Remote Source:** `aristotle9@192.168.1.210:/mnt/projects`
- **Local Mount Point:** `/mnt/projects/`
- **Contents:** Git repositories, code, documentation, configuration files

### SSHFS Options Used

- `password_stdin` - Accept password via stdin (used with `echo` or `sshpass`)
- `allow_other` - Allow non-root users to access the mount
- `default_permissions` - Enable standard permission checks

---

## Mounting the Filesystem

### Manual Mount Command

```bash
# Mount with password prompt
sudo mkdir -p /mnt/projects
sudo sshfs aristotle9@192.168.1.210:/mnt/projects /mnt/projects \
    -o allow_other,default_permissions

# Mount with password via stdin (for automation)
echo "Edgar01760" | sudo -S sh -c \
    'echo "Edgar01760" | sshfs -o password_stdin,allow_other,default_permissions \
    aristotle9@192.168.1.210:/mnt/projects /mnt/projects'
```

### Verification

```bash
# Check if mounted
mount | grep projects

# Expected output:
# aristotle9@192.168.1.210:/mnt/projects on /mnt/projects type fuse.sshfs (rw,nosuid,nodev,relatime,user_id=0,group_id=0,allow_other,default_permissions)

# Verify contents accessible
ls -la /mnt/projects/
```

---

## Usage Guidelines

### For Claude Code

**READ operations:**
```python
# Read files directly from mount
from pathlib import Path

readme = Path("/mnt/projects/Joshua/mads/horace/README.md")
content = readme.read_text()
```

**WRITE operations:**
```python
# Write files directly to mount
from pathlib import Path

output = Path("/mnt/projects/Joshua/docs/new_doc.md")
output.write_text("# New Document\n\nContent here...")
```

**EDIT operations:**
```python
# Use native Edit tool on mounted paths
# The tool works transparently on SSHFS mounts
```

**IMPORTANT:**
- **NEVER create local project files** - always write to `/mnt/projects/`
- Use Read/Write/Edit tools directly on `/mnt/projects/` paths
- No need for SCP or manual file transfers

### For Git Operations

Git repositories live on the remote server, so git commands **must run via SSH:**

```bash
# Run git commands on remote server
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no \
    aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git status"

# Example: Commit changes
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no \
    aristotle9@192.168.1.210 "cd /mnt/projects/ICCM && git add -A && git commit -m 'message'"
```

**Why SSH for git?**
- Git metadata is on the remote server
- Running git locally on the mount can cause permission issues
- Remote execution ensures git sees the correct repository state

---

## Troubleshooting

### Mount Point Empty or Files Not Visible

**Check if mounted:**
```bash
mount | grep projects
```

If not mounted, remount using the command above.

### Permission Denied Errors

**Ensure allow_other option is set:**
```bash
# Check current mount options
mount | grep projects

# Remount with correct options if needed
sudo umount /mnt/projects
# Then remount with allow_other
```

### Stale Mount After Network Interruption

**Force unmount and remount:**
```bash
# Force unmount (may require killing processes using the mount)
sudo umount -f /mnt/projects

# If that fails, use lazy unmount
sudo umount -l /mnt/projects

# Then remount
echo "Edgar01760" | sudo -S sh -c \
    'echo "Edgar01760" | sshfs -o password_stdin,allow_other,default_permissions \
    aristotle9@192.168.1.210:/mnt/projects /mnt/projects'
```

### "Transport endpoint is not connected" Error

This indicates a stale mount. Force unmount and remount as shown above.

---

## Session Startup Checklist

At the start of each Claude Code session:

1. **Verify mount exists:**
   ```bash
   mount | grep projects
   ```

2. **If not mounted, remount:**
   ```bash
   echo "Edgar01760" | sudo -S sh -c \
       'echo "Edgar01760" | sshfs -o password_stdin,allow_other,default_permissions \
       aristotle9@192.168.1.210:/mnt/projects /mnt/projects'
   ```

3. **Test accessibility:**
   ```bash
   ls -la /mnt/projects/Joshua/
   ```

---

## Comparison with Other Mounts

The ecosystem uses **two primary SSHFS mounts:**

### 1. /mnt/projects/ (This Document)
- **Purpose:** Git repositories, code, documentation
- **Source:** `aristotle9@192.168.1.210:/mnt/projects`
- **Contents:** Permanent project files
- **Git operations:** Via SSH on remote server

### 2. /mnt/irina_storage/
- **Purpose:** Ecosystem working files (outputs, temp data)
- **Source:** `aristotle9@192.168.1.210:/mnt/irina_storage` (ZFS-backed)
- **Contents:** Fiedler outputs, Playfair diagrams, Gates documents
- **Managed by:** Horace NAS Gateway
- **Details:** See `/mnt/projects/Joshua/mads/horace/README.md`

---

## Performance Considerations

**SSHFS is suitable for:**
- ✅ Small to medium file operations
- ✅ Reading/writing code and documentation
- ✅ Interactive development work

**SSHFS may be slow for:**
- ⚠️ Large file transfers (>100MB) - consider `rsync` instead
- ⚠️ High-frequency small writes - may have latency
- ⚠️ Git operations on very large repos - run git via SSH instead

**Best Practice:**
For large file operations, use `rsync` or `scp` directly instead of relying on the mount.

---

## Security Notes

- Password is stored in CLAUDE.md (local file, not in git)
- SSHFS uses SSH encryption for all data transfer
- Mount requires sudo privileges (password in CLAUDE.md)
- `allow_other` option allows non-root access to mount

---

## Related Documentation

- **CLAUDE.md** - Main session instructions with mount command
- **Horace README** - `/mnt/projects/Joshua/mads/horace/README.md` (for `/mnt/irina_storage/` mount)
- **MCP Tool Naming** - `/mnt/projects/Joshua/knowledge-base/MCP_TOOL_NAMING.md`

---

**Key Takeaway:** The `/mnt/projects/` mount provides transparent access to remote project files. Always verify it's mounted at session startup, and use SSH for git operations.
