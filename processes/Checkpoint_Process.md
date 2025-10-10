# Checkpoint Process - Saving Work State

## Overview
At major checkpoints (completing a feature, end of session, before restart), follow this process to ensure all work is properly saved and recoverable.

---

## When to Checkpoint

**Trigger a checkpoint when:**
- ✅ Completing a major feature or milestone
- ✅ End of work session
- ✅ Before restarting Claude Code
- ✅ After resolving a critical bug
- ✅ Before switching to a different project/task

---

## Checkpoint Steps

### Step 1: Update CURRENT_STATUS.md

**What to update:**
- Last Updated timestamp
- Recent Achievements section
- Project Components Status table
- Next Steps section

**Location:** `/mnt/projects/Joshua/CURRENT_STATUS.md`

**Example:**
```markdown
## Last Updated: 2025-10-10

## Recent Achievements
### MAD V1 Architecture Documentation (2025-10-10)
- Completed corrected v2 with architectural fixes
- Generated 4 professional charts
- 100% triplet approval achieved
```

---

### Step 2: Update Project Documentation (if pertinent)

**Update relevant documentation:**
- Component README.md (usage, installation, features)
- Architecture documents (if design changed)
- Requirements documents (if specs changed)
- Configuration examples
- API documentation
- Troubleshooting guides

**Common locations:**
- `/mnt/projects/Joshua/mads/[component]/README.md`
- `/mnt/projects/Joshua/architecture/`
- `/mnt/projects/Joshua/mads/[component]/requirements/`
- `/mnt/projects/Joshua/knowledge-base/`

**Example updates:**
- Added new feature → Update component README with usage
- Fixed architecture issue → Update architecture docs
- Changed requirements → Update requirements doc
- Discovered solution → Add to knowledge-base

---

### Step 3: Check Git Status

**See what files changed:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git status"
```

**Verify documentation is included:**
- Check that README/docs are staged
- Ensure no untracked important files

---

### Step 4: Update GitHub Issues (if pertinent)

**When to update issues:**
- Bug fixed → Close issue with `fixes #N` in commit
- Feature completed → Close issue
- Progress made → Add comment to issue
- New bug found → Create issue

**Commands:**
```bash
# List open issues
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue list"

# Close issue
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue close N"

# Create issue
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue create --title 'Title' --body 'Description'"
```

---

### Step 5: Commit and Push to Git

**Commit message format:**
```
Brief summary line (50 chars max)

Detailed description:
- What changed
- Why it changed
- Any breaking changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Commands:**
```bash
# Add files
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git add [files]"

# Commit with heredoc message
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git commit -m \"\$(cat <<'EOF'
Your commit message here

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)\""

# Push
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git push origin main"
```

---

### Step 6: Backup CLAUDE.md (if modified)

**If CLAUDE.md was edited during this session:**

**Run backup script:**
```bash
/mnt/projects/Joshua/config/backup_claude_md.sh
```

**Update CHANGELOG:**
- Edit `/mnt/projects/Joshua/config/CLAUDE.md.versions/CHANGELOG.md`
- Document what changed and why

**Commit backup:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git add config/CLAUDE.md.versions/ && git commit -m 'CLAUDE.md backup: [description]' && git push"
```

**See:** `/mnt/projects/Joshua/processes/CLAUDE_MD_Maintenance.md` for details

---

### Step 7: Backup Sessions to Godot (if restart required)

**If Claude Code restart is imminent, backup last 24 hours:**

**Find recent sessions:**
```bash
ls -lht ~/.claude/projects/-home-aristotle9/*.jsonl | head -10 | awk '{print $NF, $6, $7}'
```

**Store each session:**
```
mcp__iccm__godot_conversation_store_messages_bulk
  messages_file: /host/home/aristotle9/.claude/projects/-home-aristotle9/[SESSION-ID].jsonl
  metadata: {"source": "claude_code", "session_date": "2025-10-10", "topic": "work_description"}
```

**Save conversation IDs returned for recovery.**

**⚠️ EXCEPTION: Can skip with user approval if technical blocker exists**
- If Godot/Dewey tools are unavailable due to relay issues, ask user permission to skip
- This is acceptable when the restart is specifically to fix the blocking issue
- Example: "Session backup requires relay tools, but relay is broken. Skip backup and restart to fix relay?"

---

## Checkpoint Checklist

Use this checklist at each checkpoint:

- [ ] CURRENT_STATUS.md updated
- [ ] Project documentation updated (README, architecture, requirements, KB)
- [ ] Git status checked
- [ ] Relevant files committed
- [ ] GitHub issues updated/closed
- [ ] Changes pushed to remote
- [ ] (If CLAUDE.md modified) Backup created and committed
- [ ] (If restart needed) Last 24h sessions backed up to Godot OR skipped with user approval
- [ ] Conversation IDs saved for recovery (if backup performed)

---

## Quick Checkpoint (Minor Changes)

For small updates that don't warrant full checkpoint:

1. Update CURRENT_STATUS.md (optional)
2. Commit and push to git
3. Skip issues/session backup

---

## Example: Full Checkpoint Workflow

**Scenario:** Completed MAD V1 Architecture V2, about to restart

**Steps:**
1. ✅ Updated CURRENT_STATUS.md with completion details
2. ✅ Checked git status - 18 files changed
3. ✅ No GitHub issues to update (new feature, not bug fix)
4. ✅ Committed with detailed message about architectural corrections
5. ✅ Pushed to GitHub (commit bdc76cb)
6. ✅ Backed up 5 sessions from last 3 days to Godot
7. ✅ Saved conversation IDs: `8e83f1b7...`, `ed79a557...`, etc.

**Result:** All work preserved, can safely restart Claude Code

---

## Recovery After Checkpoint

See: `/mnt/projects/Joshua/knowledge-base/Session_Recovery.md` (separate article)

---

*Last Updated: 2025-10-10*
