# File System Architecture - How It All Works

**Created**: 2025-10-07
**Purpose**: Definitive guide to understanding the ecosystem's file system architecture
**Audience**: Claude Code (primary), admins, developers

---

## Executive Summary

There are **TWO file systems** mounted from Irina (192.168.1.210) to the local machine:

1. **ZFS Working File System** - Where all components write/read operational files
2. **Git Projects File System** - Where all code repositories live

**CRITICAL RULES:**
- Both are mounted locally - **NEVER access via SSH or Docker exec**
- Use local mount paths: `/mnt/irina_storage/` and `/mnt/projects/`
- No permission restrictions - everything is open (777) for now
- Works like a Windows file share - just access it directly

---

## The Two File Systems

### 1. ZFS Working File System (Operational Files)

**Purpose**: Shared storage for all ecosystem components to write/read files

**Remote Location**: `aristotle9@192.168.1.210:/mnt/irina_storage/`
**Local Mount**: `/mnt/irina_storage/`
**Mount Type**: NFS
**Permissions**: 777 (fully open, no restrictions)

**Structure**:
```
/mnt/irina_storage/
├── files/              (ZFS dataset: irina/horace/files)
│   ├── temp/           (Temporary workspace - wide open)
│   │   ├── fiedler/    (Fiedler LLM outputs)
│   │   ├── gates/      (Gates document outputs)
│   │   └── playfair/   (Playfair diagram outputs)
│   ├── input/          (Input files for processing)
│   └── fiedler_output/ (Legacy Fiedler output)
└── metadata/           (ZFS dataset: irina/horace/metadata)
    └── .horace/        (Horace internal metadata)
```

**Directory Organization Philosophy**:

**`/temp/` Directory**:
- Wide open workspace for all components
- Each component creates its own subfolder for organization
- Makes it easy to find outputs: know the component, know the folder
- Easy cleanup: delete `/temp/componentname/` or run periodic purge job (7-day, 30-day retention)
- No access restrictions - it's just temp workspace
- No HR records, no accounting data, no sensitive info - just working files

**Future Permanent Folders** (when needed):
- `/documents/` - Finalized documentation
- `/projects/` - Project-specific permanent files
- `/archives/` - Long-term storage
- `/hr/`, `/finance/` - When access control becomes necessary
- Organized by subject matter or function, not by component

**Current State**: Only temp workspace exists. When permanent data needs protection, create structured folders with appropriate permissions then.

**Managed By**: Horace (NAS gateway component on Irina)
**ZFS Pool**: `irina/horace/files` and `irina/horace/metadata`

**How Components Access It**:
- Components run in Docker containers
- Docker volumes bind to local mount: `/mnt/irina_storage/`
- **This is industry best practice** - containers should NOT make network connections directly
- Example (Fiedler):
  ```yaml
  volumes:
    - irina_storage_files:/mnt/irina_storage/files

  irina_storage_files:
    driver: local
    driver_opts:
      type: none
      device: /mnt/irina_storage/files  # ← Binds to local NFS mount
      o: bind
  ```

**Why Docker Volumes (Not Direct Network Mounts from Container)**:

✅ **CORRECT** (current setup):
```
Container → Docker volume → Host NFS mount → Network → ZFS
```

❌ **WRONG** (direct network mount):
```
Container → Network directly → ZFS
```

**Industry Best Practices for Container Storage**:

1. **Portability** - Container definition is self-contained. Moving to different host only requires volume exists there.

2. **Security Isolation** - Container doesn't need network credentials or NFS client tools. Host manages network connection.

3. **Permission Mapping** - Docker handles UID/GID mapping between container and host automatically.

4. **Single Configuration Point** - All mount logic in docker-compose.yml. Easy to audit what's mounted where.

5. **Host Controls Connection** - If NFS goes down, host handles reconnection, caching, error handling. Container is isolated from network issues.

6. **No Network Complexity in Container** - Container just sees a filesystem path. No DNS, no firewalls, no network debugging.

**When to use direct network mounts from container**:
- Legacy apps that MUST control their own NFS client (rare)
- Specialized storage protocols Docker doesn't support (very rare)
- Very specific locking/permission requirements (almost never)

**Our setup is 100% correct - always use Docker volumes to bridge containers to network storage.**

**How Claude Code Accesses It**:
```bash
# Direct access via local mount
ls /mnt/irina_storage/files/temp/fiedler/
cat /mnt/irina_storage/files/temp/fiedler/output.md
```

---

### 2. Git Projects File System (Code Repositories)

**Purpose**: All git repositories and project code

**Remote Location**: `aristotle9@192.168.1.210:/mnt/projects/`
**Local Mount**: `/mnt/projects/`
**Mount Type**: SSHFS (existing mount, already configured)
**Permissions**: Full access for aristotle9 user

**Structure**:
```
/mnt/projects/
├── ICCM/               (Main ICCM repository)
├── Joshua/             (Process docs, implementations)
├── hawkmoth-ecosystem/ (Legacy tools)
└── gemini-tool/        (LLM client tools)
```

**How Components Access It**:
- Read-only mounts for code/tools they need
- Example (Fiedler):
  ```yaml
  volumes:
    - /mnt/projects/ICCM/tools/grok_client.py:/app/clients/grok_client.py:ro
  ```

**How Claude Code Accesses It**:
```bash
# Direct access via local mount
ls /mnt/projects/Joshua/docs/
cat /mnt/projects/ICCM/README.md
```

**Git Operations**:
```bash
# Git commands run on REMOTE machine via SSH
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
  "cd /mnt/projects/ICCM && git status"
```

---

## Critical: MADs Cannot Access Local /tmp/ Directory

**This causes "file not found" errors and missing outputs EVERY time**

### The Problem
MADs run in Docker containers with isolated filesystems. They cannot see or write to the host's `/tmp/` directory. This affects both:
1. **Input files** you send to MADs
2. **Output directories** where MADs write results

### The Solution
**Always use directories that are mounted into the MAD containers:**
- `/mnt/irina_storage/files/temp/` - Best for all temporary files (all MADs have access)
- `/mnt/projects/` - For code/documentation that needs to be processed

### Input File Issues
```bash
# WRONG - MAD can't see this file
echo "review content" > /tmp/review.md
mad_tool_send(files=["/tmp/review.md"])  # ❌ Container can't see /tmp/

# CORRECT - Use mounted directory
echo "review content" > /mnt/irina_storage/files/temp/review.md
mad_tool_send(files=["/mnt/irina_storage/files/temp/review.md"])  # ✅ Works
```

### Output Directory Issues
```bash
# WRONG - MAD can't write here (or writes to its own isolated /tmp/)
mad_set_output(output_dir="/tmp/results")  # ❌ Won't be accessible from host

# CORRECT - Use mounted directory
mad_set_output(output_dir="/mnt/irina_storage/files/temp/mad_name")  # ✅ Works
```

### Why This Happens Every Time
1. Natural workflow: Create temporary file → `/tmp/` is the obvious choice
2. Keep related files together → Set output to same `/tmp/` location
3. MAD appears to succeed but files are inaccessible
4. Must use mounted directory → Now it works

### Default Behavior Pattern
- **Claude Code habit**: Default to `/tmp/` for temporary files (standard Unix practice)
- **Correct behavior**: Always start with `/mnt/irina_storage/files/temp/` when MADs are involved
- **Never use `/tmp/`** for any MAD input or output - it won't work

### Remember
- **Local `/tmp/`** = Only visible to host machine and Claude Code
- **Container `/tmp/`** = Each container has its own isolated `/tmp/` (not accessible from host)
- **Shared temp** = `/mnt/irina_storage/files/temp/` (visible to all)
- **MAD outputs** = Should always go to `/mnt/irina_storage/files/temp/{mad_name}/`

---

## Data Flow: How Files Move Through The System

### Example: Fiedler Writes an LLM Output File

1. **Fiedler application** (in container) writes to `/mnt/irina_storage/files/temp/fiedler/output.md`
2. **Docker volume** maps container path to local Docker volume
3. **Docker volume** has `device: /mnt/irina_storage/files` (binds to local NFS mount)
4. **Local NFS mount** at `/mnt/irina_storage/` connects to `192.168.1.210:/mnt/irina_storage/`
5. **Remote server (Irina)** has ZFS dataset mounted at `/mnt/irina_storage/files/`
6. **Horace** manages the ZFS dataset `irina/horace/files`
7. **File is written** to ZFS storage
8. **Claude Code** reads it directly: `cat /mnt/irina_storage/files/temp/fiedler/output.md`

**The Chain**:
```
Fiedler container
  → Docker volume
  → /mnt/irina_storage/ (local NFS mount)
  → 192.168.1.210:/mnt/irina_storage/ (remote ZFS)
  → Horace-managed ZFS
  → Claude Code reads it
```

---

## Why NFS Instead of SSHFS for ZFS?

**Problem with SSHFS**:
- Multiple SSHFS mounts to same remote path caused connection conflicts
- Docker containers already had root-owned SSHFS mounts
- User-owned SSHFS mounts failed with I/O errors
- SSH connection limits were being hit

**Solution - NFS**:
- Designed for network file sharing (like Windows file shares)
- No connection limits or conflicts
- Multiple clients can mount simultaneously
- Works exactly like "just open the share and it works"

**NFS Configuration**:
```bash
# On remote server (Irina):
/etc/exports:
/mnt/irina_storage 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash,insecure)
/mnt/irina_storage/files 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash,insecure)
/mnt/irina_storage/metadata 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash,insecure)

# On local machine:
/etc/fstab:
192.168.1.210:/mnt/irina_storage /mnt/irina_storage nfs defaults,_netdev 0 0
```

---

## Permission Model

**Current State**: **FULLY OPEN** (777 everywhere)

**Rationale**:
- We need unrestricted access for development
- No security boundaries needed yet
- Like a Windows file share - "just works"
- aristotle9 user should access everything everywhere

**Future**: When security matters, we can add restrictions folder-by-folder

**How to Check**:
```bash
# On remote (Irina):
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
  "ls -la /mnt/irina_storage/"

# Should show: drwxrwxrwx aristotle9 aristotle9
```

---

## Common Mistakes to Avoid

### ❌ DON'T: Access files via SSH
```bash
# WRONG
sshpass -p "..." ssh aristotle9@192.168.1.210 "cat /mnt/irina_storage/files/output.md"
```

### ✅ DO: Use local mount
```bash
# CORRECT
cat /mnt/irina_storage/files/output.md
```

### ❌ DON'T: Access files via Docker exec
```bash
# WRONG
docker exec fiedler-mcp cat /mnt/irina_storage/files/output.md
```

### ✅ DO: Use local mount
```bash
# CORRECT
cat /mnt/irina_storage/files/output.md
```

### ❌ DON'T: Try to git clone locally
```bash
# WRONG - local /mnt/projects is NOT a git repo
git clone /mnt/projects/ICCM
```

### ✅ DO: Git operations on remote via SSH
```bash
# CORRECT
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
  "cd /mnt/projects/ICCM && git status"
```

---

## Troubleshooting

### Mount not showing files?

1. Check if mount exists:
   ```bash
   mount | grep irina_storage
   ```

2. If missing, remount:
   ```bash
   echo "Edgar01760" | sudo -S mount -t nfs 192.168.1.210:/mnt/irina_storage /mnt/irina_storage
   ```

3. Verify access:
   ```bash
   ls /mnt/irina_storage/files/
   ```

### Permission denied errors?

1. Check remote permissions:
   ```bash
   sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
     "ls -la /mnt/irina_storage/"
   ```

2. Should be 777, if not:
   ```bash
   sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
     "echo 'Edgar01760' | sudo -S chmod -R 777 /mnt/irina_storage"
   ```

### I/O errors or connection issues?

- This happened with SSHFS, should NOT happen with NFS
- If it does, check NFS service on remote:
  ```bash
  sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
    "systemctl status nfs-kernel-server"
  ```

---

## Quick Reference

**ZFS Working Files**:
- Local path: `/mnt/irina_storage/`
- Remote: `aristotle9@192.168.1.210:/mnt/irina_storage/`
- Type: NFS
- Access: Direct (no sudo needed)

**Git Projects**:
- Local path: `/mnt/projects/`
- Remote: `aristotle9@192.168.1.210:/mnt/projects/`
- Type: SSHFS
- Git ops: SSH to remote, run git commands there

**aristotle9 credentials**:
- User: aristotle9
- Password: Edgar01760
- Access: Root-level everywhere (no restrictions)

**Golden Rule**:
> "Use the local mounts. Never SSH. Never Docker exec. Just read the files directly like they're local."

---

**Remember**: This is designed to work like a Windows file share - simple, open, reliable. No complex permission schemes. No connection limits. It just works.
