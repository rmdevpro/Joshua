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

## Checkpoint Checklist

Use this checklist at each checkpoint:

- [ ] Clean up old containers
- [ ] Clean up files that have no ongoing use
- [ ] CURRENT_STATUS.md updated (includes all restart information)
- [ ] Project documentation updated (README, architecture, requirements, KB)
- [ ] Git status checked
- [ ] Relevant files committed
- [ ] GitHub issues updated/closed
- [ ] Changes pushed to remote
- [ ] (If CLAUDE.md modified) Backup created and committed

---

## Quick Checkpoint (Minor Changes)

For small updates that don't warrant full checkpoint:

1. Update CURRENT_STATUS.md (optional)
2. Commit and push to git
3. Skip issues

---

## Example: Full Checkpoint Workflow

**Scenario:** Completed MAD V1 Architecture V2

**Steps:**
1. ✅ Updated CURRENT_STATUS.md with completion details
2. ✅ Checked git status - 18 files changed
3. ✅ No GitHub issues to update (new feature, not bug fix)
4. ✅ Committed with detailed message about architectural corrections
5. ✅ Pushed to GitHub (commit bdc76cb)

**Result:** All work preserved, ready for next session

---

## Recovery After Checkpoint

**On restart, simply:**
1. Read CURRENT_STATUS.md - contains all restart information
2. Check recent git commits
3. Check open GitHub issues
4. Resume work

**All restart information is in CURRENT_STATUS.md - no separate recovery documents needed.**

---

*Last Updated: 2025-10-10*
