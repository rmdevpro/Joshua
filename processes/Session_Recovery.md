# Session Recovery - Resuming Work After Restart

## Overview
After restarting Claude Code, use this process to recover context and resume work seamlessly.

---

## When to Use This Process

**Use this recovery process when:**
- ✅ Starting a new Claude Code session
- ✅ Continuing work after a restart
- ✅ Picking up from where you left off
- ✅ Terminal display issues require restart
- ✅ Need to restore context from previous session

---

## Recovery Steps

### Step 1: Read CURRENT_STATUS.md

**Primary source of context:**
```
Read: /mnt/projects/Joshua/CURRENT_STATUS.md
```

**What to look for:**
- Last Updated timestamp (when was last checkpoint?)
- Recent Achievements (what was just completed?)
- Next Steps (what should be done next?)
- Project Components Status (what's the current state?)
- Any conversation IDs mentioned

---

### Step 2: Check Git Status & Recent Commits

**See what changed recently:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git log --oneline -5"
```

**Check current branch state:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && git status"
```

**What to verify:**
- Are there uncommitted changes?
- What was the last commit about?
- Is the working tree clean?

---

### Step 3: Read Relevant Documentation

**Based on CURRENT_STATUS.md, read:**
- Component README files mentioned
- Architecture documents referenced
- Requirements documents updated
- Knowledge-base articles created

**Common files to check:**
- `/mnt/projects/Joshua/architecture/` - Architecture docs
- `/mnt/projects/Joshua/mads/[component]/README.md` - Component docs
- `/mnt/projects/Joshua/mads/[component]/requirements/` - Requirements
- `/mnt/projects/Joshua/knowledge-base/` - KB articles

---

### Step 4: Check GitHub Issues

**Review open issues:**
```bash
sshpass -p "Edgar01760" ssh aristotle9@192.168.1.210 "cd /mnt/projects/Joshua && gh issue list --assignee @me --state open"
```

**What to look for:**
- High priority bugs
- In-progress features
- Blockers or dependencies

---

### Step 5: Retrieve Recent Conversation from Dewey (If Available)

**⚠️ IMPORTANT:** This step requires Dewey to be available via MCP Relay. If relay tools are not working or Dewey is unavailable, **SKIP THIS STEP** and proceed with the context already gathered from CURRENT_STATUS.md, git log, and documentation.

**If conversation ID is known (from CURRENT_STATUS.md notes):**
```
mcp__iccm__dewey_get_conversation
  conversation_id: "8e83f1b7-4045-44f8-8765-4aa757c4dbdd"
```

**If searching for recent work:**
```
mcp__iccm__dewey_search
  query: "MAD V1 Architecture" (or relevant topic)
  start_date: "2025-10-09"
  limit: 100
```

**Get last conversations:**
```
mcp__iccm__dewey_list_conversations
  limit: 5
  sort_by: "created_at"
```

**Note:** Each conversation can have thousands of messages. Consider retrieving just the conversation metadata first, then pull specific messages if needed.

**If Dewey is unavailable:**
- CURRENT_STATUS.md should contain sufficient context
- Git commit history provides detailed technical changes
- Documentation updates reflect recent work
- Proceed without conversation retrieval

---

### Step 6: Review Recent Messages (Last 100 Lines) - Optional

**⚠️ SKIP THIS STEP if Dewey is unavailable** (see Step 5)

**Once you have the conversation ID, get recent context:**

The Dewey API returns all messages in a conversation. To get the "last 100 lines" equivalent:

1. Retrieve the full conversation
2. Focus on the most recent messages
3. Look for:
   - Last completed task
   - Any pending work
   - Blockers or issues encountered
   - Next steps discussed

**Alternative - Search for specific context:**
```
mcp__iccm__dewey_search
  query: "checkpoint" OR "TODO" OR "next steps"
  conversation_id: "8e83f1b7-..." (if known)
  limit: 50
```

---

## Recovery Checklist

**Core Steps (Always Required):**
- [ ] Read CURRENT_STATUS.md
- [ ] Check recent git commits (last 5)
- [ ] Review git status for uncommitted changes
- [ ] Read relevant documentation mentioned in STATUS
- [ ] Check open GitHub issues
- [ ] Identify next task to work on

**Optional Steps (If Dewey Available):**
- [ ] Retrieve recent conversation from Dewey
- [ ] Review last 100 messages for context

**Note:** If Dewey/MCP tools are unavailable, the core steps provide sufficient context to resume work.

---

## Quick Recovery (Same Day)

If restarting within same work session (hours, not days):

1. Read CURRENT_STATUS.md
2. Check git status
3. Retrieve last conversation from Dewey (if available)
4. Resume work

Skip: Deep dive into docs, issues (unless needed)

**Note:** If MCP tools unavailable, steps 1-2 are usually sufficient for same-day recovery.

---

## Example: Recovery Workflow

**Scenario:** Restarted Claude Code after terminal display issue

**Steps:**
1. ✅ Read CURRENT_STATUS.md
   - Last updated: 2025-10-10 14:04
   - Recent: MAD V1 Architecture V2 completed
   - Next: Begin implementation

2. ✅ Check git log
   - Last commit: `bdc76cb` - MAD V1 Architecture V2
   - Working tree: Clean

3. ✅ Read relevant docs
   - `/mnt/projects/Joshua/architecture/v1/` - All 9 docs + 4 charts

4. ✅ Check GitHub issues
   - No blocking issues

5. ✅ Retrieved conversation `8e83f1b7...` from Dewey
   - 4,001 messages stored
   - Last task: Created Checkpoint_Process.md KB article
   - Next: Create Session_Recovery.md KB article

6. ✅ Reviewed last messages
   - Display issue occurred
   - Sessions backed up successfully
   - Ready to continue with recovery article

**Result:** Full context restored, ready to resume work

---

## Notes

**Conversation IDs:**
- Save important conversation IDs in CURRENT_STATUS.md notes
- Or in a separate `/mnt/projects/Joshua/sessions/conversation_ids.txt`

**Missing Context:**
- If Dewey doesn't have the conversation, check session backup article
- Sessions may not have been backed up if no restart was planned

**Large Conversations:**
- Conversations with 1000+ messages may be large
- Use search instead of retrieving entire conversation
- Focus on recent time ranges

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/Checkpoint_Process.md` - How to checkpoint
- `/mnt/projects/Joshua/knowledge-base/Session_Backup_Recovery.md` - How to backup sessions

---

## Changelog

**2025-10-10 19:45:**
- Made Step 5 (Dewey retrieval) and Step 6 (message review) optional
- Added warnings to skip these steps if MCP relay/Dewey unavailable
- Updated checklist to separate core vs optional steps
- Added note that core steps provide sufficient context without Dewey

**2025-10-10 (Initial):**
- Created Session Recovery process document

---

*Last Updated: 2025-10-10 19:45*
