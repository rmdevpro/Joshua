# CLAUDE.md Maintenance Process

## Overview
CLAUDE.md is a critical configuration file that controls Claude Code behavior across all sessions. It lives locally at `/home/aristotle9/CLAUDE.md` and is NOT tracked in git. This process ensures changes are managed safely.

---

## Critical Facts

**Location:** `/home/aristotle9/CLAUDE.md` (local to Claude Code instance)

**NOT in git because:**
- Contains local system paths
- Contains credentials (sudo password, API key locations)
- Specific to this machine's configuration

**BUT needs versioning because:**
- Changes affect all future sessions
- Mistakes can break workflows
- Need history for troubleshooting

---

## CLAUDE.md Change Process

### Step 1: Review Current Content

**Before any changes:**
```
Read: /home/aristotle9/CLAUDE.md
```

**Understand:**
- What sections exist?
- What's the current structure?
- What references external docs?

---

### Step 2: Plan the Change

**Determine change type:**

**A. Adding new guidance**
- Is it verbose? → Create KB/process doc, add reference
- Is it concise principle? → Add directly to CLAUDE.md

**B. Updating existing section**
- Has it become verbose? → Extract to external doc
- Still concise? → Update in place

**C. Removing content**
- Being moved to external doc? → Add reference
- Truly obsolete? → Remove completely

---

### Step 3: Follow Best Practices

#### Keep CLAUDE.md Concise

**CLAUDE.md should contain:**
- ✅ Critical rules (Rule #1: Don't change working systems)
- ✅ Essential system info (paths, passwords, mounts)
- ✅ Quick reference (session startup checklist)
- ✅ References to detailed docs

**Move to external docs:**
- ❌ Detailed procedures (> 10 lines)
- ❌ Step-by-step workflows
- ❌ Troubleshooting guides
- ❌ Complete command examples

#### Use External Documentation

**When content exceeds ~10 lines:**

1. Create KB or process document
2. Add reference in CLAUDE.md:

```markdown
## Section Title

Brief 1-2 sentence summary.

**Detailed guide:** See `/mnt/projects/Joshua/processes/Detail_Process.md`

Quick reference:
- Key point 1
- Key point 2
```

---

### Step 4: Make the Change

**Edit CLAUDE.md:**
```
Edit: /home/aristotle9/CLAUDE.md
  old_string: [current content]
  new_string: [updated content]
```

**Verify:**
- Syntax correct?
- Paths valid?
- References to external docs correct?

---

### Step 5: Backup to Git

**CRITICAL: Every change to CLAUDE.md MUST be backed up to git.**

**Backup location:** `/mnt/projects/Joshua/config/CLAUDE.md.versions/`

**Copy with timestamp:**
```bash
cp /home/aristotle9/CLAUDE.md /mnt/projects/Joshua/config/CLAUDE.md.versions/CLAUDE.md.$(date +%Y%m%d_%H%M%S)
```

**Or use provided script:**
```bash
/mnt/projects/Joshua/config/backup_claude_md.sh
```

---

### Step 6: Commit to Git

**Add to git:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git add config/CLAUDE.md.versions/"
```

**Commit with clear message:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git commit -m 'CLAUDE.md backup: [brief description of change]

Changes:
- [What changed]
- [Why it changed]

Date: $(date +%Y-%m-%d)
'"
```

**Push:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git push origin main"
```

---

### Step 7: Document the Change

**Update change log:**
Add entry to `/mnt/projects/Joshua/config/CLAUDE.md.versions/CHANGELOG.md`

```markdown
## 2025-10-10 14:30

**Changed:** Simplified relay troubleshooting section

**Before:**
- 20 lines of detailed troubleshooting steps

**After:**
- 5 line summary with reference to Relay_Troubleshooting.md

**Reason:** Keep CLAUDE.md concise, detailed guide in KB

**Backup:** CLAUDE.md.20251010_143000
```

---

## Best Practices

### 1. Keep It Concise

**Target:** CLAUDE.md should be ~200-250 lines

**If growing beyond 250 lines:**
- Review each section
- Extract verbose content to external docs
- Keep only essential references

### 2. Structure Sections Consistently

**Pattern for each section:**
```markdown
## 🔴 SECTION TITLE

Brief principle or rule (1-2 lines)

**Detailed guide:** See [link to external doc]

Quick reference:
- Key point 1
- Key point 2
```

### 3. Cross-Reference External Docs

**When creating external doc, update CLAUDE.md:**
```markdown
Before:
## Error Handling
[20 lines of detailed steps]

After:
## ⏱️ ERROR HANDLING
**Protocol:** See /mnt/projects/Joshua/knowledge-base/Error_Handling_Protocol.md

Quick rules:
1. First failure → Try ONE alternative
2. Second failure → STOP, it's a bug
```

### 4. Version Every Change

**Never skip backup:**
- Even "small" changes
- Even typo fixes
- Every edit gets versioned

**Why:**
- CLAUDE.md controls all behavior
- Need rollback capability
- Troubleshooting requires history

### 5. Test After Changes

**After editing CLAUDE.md:**
1. Read it back to verify
2. Check references are valid
3. Verify paths exist
4. Test in new Claude Code session (if major change)

---

## Rollback Process

**If CLAUDE.md change causes issues:**

**Step 1: Identify last good version**
```bash
ls -lht /mnt/projects/Joshua/config/CLAUDE.md.versions/
```

**Step 2: Review changelog**
```
Read: /mnt/projects/Joshua/config/CLAUDE.md.versions/CHANGELOG.md
```

**Step 3: Restore previous version**
```bash
cp /mnt/projects/Joshua/config/CLAUDE.md.versions/CLAUDE.md.20251010_120000 /home/aristotle9/CLAUDE.md
```

**Step 4: Verify restored version**
```
Read: /home/aristotle9/CLAUDE.md
```

**Step 5: Document rollback**
```
# Add rollback entry to CHANGELOG.md
# Note what was wrong with rolled-back version
```

---

## Change Checklist

**Before committing CLAUDE.md change:**

- [ ] Change follows best practices (concise, uses external docs)
- [ ] Verbose content extracted to KB/process docs
- [ ] External doc references are correct
- [ ] Backup created in config/CLAUDE.md.versions/
- [ ] Backup committed to git
- [ ] CHANGELOG.md updated
- [ ] Changes pushed to remote
- [ ] Tested (if major change)

---

## Example: Complete Change Workflow

**Scenario:** Adding session management guidance to CLAUDE.md

**Step 1: Review current**
```
Read: /home/aristotle9/CLAUDE.md
# Check current structure
```

**Step 2: Plan**
```
# Decision: Add new "SESSION MANAGEMENT" section
# Content: 3 subsections (Checkpoint, Recovery, Backup)
# Strategy: Brief summary + links to process docs (already exist)
```

**Step 3: Create external docs if needed**
```
# Already exist:
# - Checkpoint_Process.md
# - Session_Recovery.md
# - Session_Backup_Recovery.md
# No new docs needed
```

**Step 4: Make change**
```
Edit: /home/aristotle9/CLAUDE.md
# Add SESSION MANAGEMENT section
# Keep each subsection to 3-4 lines
# Reference detailed process docs
```

**Step 5: Backup**
```bash
cp /home/aristotle9/CLAUDE.md /mnt/projects/Joshua/config/CLAUDE.md.versions/CLAUDE.md.20251010_143000
```

**Step 6: Commit**
```bash
git add config/CLAUDE.md.versions/CLAUDE.md.20251010_143000
git commit -m "CLAUDE.md backup: Add session management section"
git push
```

**Step 7: Document**
```
# Update CHANGELOG.md with change details
```

---

## Directory Structure

```
/home/aristotle9/
  CLAUDE.md                          # Live file (NOT in git)

/mnt/projects/Joshua/config/
  backup_claude_md.sh                # Automated backup script
  CLAUDE.md.versions/
    CHANGELOG.md                     # Change history
    CLAUDE.md.20251010_120000        # Timestamped backups
    CLAUDE.md.20251010_143000
    CLAUDE.md.20251009_100000
    [etc...]
```

---

## Backup Script

**Auto-backup script at `/mnt/projects/Joshua/config/backup_claude_md.sh`:**

```bash
#!/bin/bash
# Backup CLAUDE.md with timestamp

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp /home/aristotle9/CLAUDE.md /mnt/projects/Joshua/config/CLAUDE.md.versions/CLAUDE.md.$TIMESTAMP

echo "Backed up to: CLAUDE.md.$TIMESTAMP"
echo "Don't forget to:"
echo "1. Update CHANGELOG.md"
echo "2. Commit to git"
echo "3. Push to remote"
```

**Usage:**
```bash
/mnt/projects/Joshua/config/backup_claude_md.sh
```

---

## Common Mistakes

**DON'T:**
- ❌ Change CLAUDE.md without backup
- ❌ Add verbose content directly to CLAUDE.md
- ❌ Skip git commit
- ❌ Forget to update CHANGELOG.md
- ❌ Make changes without testing

**DO:**
- ✅ Backup before every change
- ✅ Extract verbose content to external docs
- ✅ Commit to git immediately
- ✅ Update CHANGELOG.md
- ✅ Test major changes

---

## See Also

- `/mnt/projects/Joshua/processes/Checkpoint_Process.md` - When to backup CLAUDE.md
- `/mnt/projects/Joshua/knowledge-base/` - KB articles referenced in CLAUDE.md
- `/mnt/projects/Joshua/processes/` - Process docs referenced in CLAUDE.md

---

*Last Updated: 2025-10-10*
