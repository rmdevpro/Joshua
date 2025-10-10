# GitHub Issue Management Process

## Overview
This process defines how to manage GitHub issues throughout the development lifecycle.

---

## Issue Workflow

### 1. Session Startup

**Check assigned issues:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue list --assignee @me --state open"
```

**Check high-priority bugs:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue list --label bug --state open"
```

---

### 2. Working on Issues

**Reference in commits:**
```bash
git commit -m "Fix authentication timeout

Resolves issue with session expiration.

fixes #42

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Keywords that auto-close issues:**
- `fixes #N`
- `closes #N`
- `resolves #N`

**Keywords for reference only (doesn't close):**
- `relates to #N`
- `see #N`
- `ref #N`

---

### 3. Creating Issues

**When to create:**
- Bug discovered
- Feature requested
- Tech debt identified
- Documentation needed

**Create issue:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue create --title 'Brief description' --body 'Detailed description

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
...

## Actual Behavior
...'
```

---

### 4. Closing Issues

**Auto-close via commit:**
- Use `fixes #N` in commit message
- Issue closes when commit pushed

**Manual close:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue close N"
```

**With comment:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue close N --comment 'Fixed in commit abc123'"
```

---

### 5. Updating Issues

**Add comment:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue comment N --body 'Progress update...'"
```

**Change labels:**
```bash
# Add label
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue edit N --add-label 'in-progress'"

# Remove label
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue edit N --remove-label 'bug'"
```

---

## Issue Checkpoint Integration

**During checkpoint process:**

1. **Check if work relates to issue**
   - Bug fix? → Use `fixes #N`
   - Feature? → Use `fixes #N` or `closes #N`
   - Partial progress? → Add comment to issue

2. **Update issue status**
   - Add labels as appropriate
   - Comment on progress
   - Close if completed

3. **Create new issues if needed**
   - Bugs discovered during work
   - Follow-up tasks identified

---

## Common Issue Labels

- `bug` - Something broken
- `feature` - New functionality
- `enhancement` - Improvement to existing feature
- `documentation` - Docs needed
- `tech-debt` - Code quality improvement
- `in-progress` - Currently being worked on
- `blocked` - Cannot proceed
- `help-wanted` - Need assistance

---

## Best Practices

1. **One issue per bug/feature** - Don't combine unrelated items
2. **Clear titles** - "Auth timeout" not "Fix bug"
3. **Reproducible steps** - For bugs, always include how to reproduce
4. **Link to commits** - Reference commits in issue comments
5. **Close when done** - Don't leave stale open issues

---

## Quick Reference

| Task | Command |
|------|---------|
| List my issues | `gh issue list --assignee @me --state open` |
| List bugs | `gh issue list --label bug --state open` |
| Create issue | `gh issue create --title "..." --body "..."` |
| Close issue | `gh issue close N` |
| Add comment | `gh issue comment N --body "..."` |
| View issue | `gh issue view N` |

**All commands require SSH prefix:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && [command]"
```

---

## See Also

- `/mnt/projects/Joshua/processes/Checkpoint_Process.md` - When to update issues
- `/mnt/projects/Joshua/CURRENT_STATUS.md` - Current project status

---

*Last Updated: 2025-10-10*
