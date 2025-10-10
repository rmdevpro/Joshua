# Backing Up Claude Code Sessions to Godot/Dewey

## Overview
Claude Code sessions are stored locally as JSONL files. This guide shows how to back them up to Godot/Dewey for long-term storage.

---

## Session Storage Location

**Local path:** `~/.claude/projects/-home-aristotle9/*.jsonl`

Each session is stored as a separate JSONL file with a UUID filename.

---

## Quick Backup Commands

### Backup Current Session (Most Recent)
```bash
# Find the most recent session
ls -lht ~/.claude/projects/-home-aristotle9/*.jsonl | head -1
```

Then send to Godot/Dewey using the conversation ID tool.

### Backup Last N Days of Sessions

**Example: Last 3 days**
```bash
# List sessions from last 3 days
ls -lht ~/.claude/projects/-home-aristotle9/*.jsonl | head -20 | awk '{print $NF, $6, $7}'
```

---

## Storing Sessions in Dewey

### Single Session Backup

**Step 1:** Find the session file
```bash
ls -lht ~/.claude/projects/-home-aristotle9/*.jsonl | head -1
```

**Step 2:** Use Godot's bulk import (container path prefix required)

The key is using `/host/home/aristotle9/` prefix instead of `/home/aristotle9/` because Godot runs in a container.

**Example:**
```
mcp__iccm__godot_conversation_store_messages_bulk
  messages_file: /host/home/aristotle9/.claude/projects/-home-aristotle9/48f1ad23-1114-4d3c-8b22-981a68344e16.jsonl
  metadata: {"source": "claude_code", "session_date": "2025-10-10", "topic": "your_topic"}
```

**Response:**
```json
{
  "conversation_id": "8e83f1b7-4045-44f8-8765-4aa757c4dbdd",
  "messages_stored": 4001,
  "status": "success"
}
```

### Multiple Sessions Backup

Send multiple tool calls in parallel:

```
# Call mcp__iccm__godot_conversation_store_messages_bulk multiple times
# One for each session file
```

---

## Container Path Mapping

**CRITICAL:** Godot container sees paths differently:

| Your System | Godot Container |
|-------------|-----------------|
| `/home/aristotle9/` | `/host/home/aristotle9/` |
| `/tmp/` | `/host/tmp/` |

**Always use the container path** when calling Godot tools.

---

## Common Issues

### "File not found" Error
**Problem:** Used local path instead of container path

**Solution:**
- ❌ `/home/aristotle9/.claude/...`
- ✅ `/host/home/aristotle9/.claude/...`

### Session Not Showing
**Problem:** Session file might still be locked by Claude Code

**Solution:** Wait a few seconds or close/reopen Claude Code

---

## Best Practices

1. **Backup after major work sessions** - Don't lose important context
2. **Use descriptive metadata** - Makes searching easier later
3. **Regular backups** - Store sessions at end of day
4. **Tag topics** - Include topic/project name in metadata

---

## Example Workflow

**At end of work session:**

1. Find recent sessions:
   ```bash
   ls -lht ~/.claude/projects/-home-aristotle9/*.jsonl | head -5
   ```

2. Store each to Dewey with proper metadata
3. Save conversation IDs for future reference
4. Optionally: Add note to CURRENT_STATUS.md with conversation IDs

---

*Last Updated: 2025-10-10*
