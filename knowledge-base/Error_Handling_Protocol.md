# Error Handling Protocol

## Overview
This protocol defines how to handle tool failures, command errors, and systematic issues during development.

---

## Core Principle

**Every tool call is a try/catch with implicit timeout.**

When something fails, diagnose and fix the root cause - don't loop retrying the same failing operation.

---

## Failure Response Protocol

### First Failure

**When a tool/command returns error or no output:**

1. **Note the failure** - What failed, what was the error?
2. **Try ONE alternative approach** - Different tool, different parameters, different method
3. **Document what you tried**

**Example:**
```
❌ Attempted: mcp__iccm__fiedler_send (no such tool available)
✅ Alternative: Check relay status → Relay working perfectly
✅ Diagnosis: What changed? Was backend restarted? Check backend connection
```

---

### Second Consecutive Failure

**If the alternative also fails (same operation, different approach):**

**STOP - It's a BUG**

**Do NOT:**
- ❌ Try the same thing a third time
- ❌ Loop through variations hoping one works
- ❌ Assume it will eventually work

**DO:**
- ✅ Treat as a bug
- ✅ Follow bug handling process
- ✅ Escalate if needed

---

## Bug Handling Process

### Step 1: Document the Bug

**Record:**
- What operation was attempted
- What failed
- What alternatives were tried
- Error messages received
- Expected vs actual behavior

---

### Step 2: Attempt Reasonable Fix

**Diagnose root cause:**
- Is it a configuration issue?
- Is it a permission problem?
- Is it an environmental issue?
- Is it a dependency problem?

**Apply fix (different approach, not same tool again):**
- Fix configuration
- Check permissions
- Verify environment
- Install missing dependencies

**ONE fix attempt only.**

---

### Step 3: Escalate if Still Failing

**If fix attempt doesn't resolve:**

**Option A: Consult triplets**
- Send problem to Fiedler trio
- Get multiple perspectives
- Implement consensus solution

**Option B: Ask user for guidance**
- Present diagnosis
- Show what was tried
- Request direction

**DO NOT continue looping.**

---

### Step 4: Update BUG_TRACKING.md

**Document for future reference:**
```markdown
## [Date] - [Component] - [Brief Description]

**Issue:** [What failed]
**Attempts:** [What was tried]
**Solution:** [How it was resolved OR still open]
**Lesson:** [What was learned]
```

---

## Pattern Recognition

### Systematic Issues

**2+ tools fail with same/similar error:**
- NOT coincidence
- Systematic problem
- Escalate immediately
- Don't try more tools

**Example:**
```
❌ Read file fails (permission denied)
❌ Write file fails (permission denied)
🚨 SYSTEMATIC ISSUE: Permission problem, escalate
```

---

### Empty/Null Results

**Tool returns empty/nothing when response expected:**
- Treat as failure
- Don't assume "it worked but returned nothing"
- Investigate why empty

---

### Hook Blocks

**Command blocked by user hook:**
- Don't retry blindly
- Ask user about hook configuration
- May be intentional security measure

---

## Progress Checkpoints

**Use TodoWrite for progress tracking:**

**Every 3-5 steps, add checkpoint:**
```
{
  "content": "Checkpoint: Evaluate if forward progress made",
  "status": "pending",
  "activeForm": "Evaluating progress"
}
```

**At checkpoint:**
- Review last 3-5 steps
- Forward progress? → Continue
- No progress/repeated failures? → Trigger bug handling
- Self-correct without user intervention if possible

---

## Self-Correction

**When stuck:**

1. **Stop the current approach**
2. **Review what's been tried**
3. **Identify the pattern** (what's failing repeatedly?)
4. **Change strategy** (not just parameters)
5. **If still stuck** → Escalate

**Example:**
```
Stuck pattern:
- Tried tool A 3 times with different parameters (all failed)

Self-correction:
- Stop using tool A
- Ask: "Is there a different way to accomplish this?"
- Try fundamentally different approach
- Or escalate if no alternative known
```

---

## Anti-Patterns (Don't Do This)

### Infinite Retry Loops

```python
# ❌ DON'T
while not success:
    try_same_thing_again()  # Will loop forever
```

### Trying Every Variation

```python
# ❌ DON'T
for param in all_possible_values:
    try_tool(param)  # Hoping one will work
```

### Ignoring Errors

```python
# ❌ DON'T
try:
    tool()
except:
    pass  # Pretend it worked
```

---

## Best Practices

### Quick Failure

```python
# ✅ DO
result = try_operation()
if failed:
    try_alternative()
    if still_failed:
        escalate()  # Don't keep trying
```

### Clear Error Messages

```python
# ✅ DO
"Failed to read file: /tmp/file.txt
Error: File not found
Attempted: Direct read, checking with ls
Next: Need to verify file location"
```

### Document Attempts

```python
# ✅ DO
# Track what's been tried in todo or notes
# Prevents repeating same failures
```

---

## Escalation Matrix

| Failure Type | Response |
|--------------|----------|
| First failure | Try alternative approach |
| Second failure (same op) | Treat as bug, attempt fix |
| Third failure (after fix) | Consult triplets OR ask user |
| Systematic (2+ tools) | Escalate immediately |
| Critical system | Ask user before any fix |

---

## Example: Good Error Handling

```
Task: Read configuration file

Attempt 1:
❌ Read /tmp/config.json (File not found)

Attempt 2 (alternative):
✅ List /tmp directory → File not there
✅ Check /etc/config.json → Found!
✅ Read /etc/config.json → Success

Lesson: Config files in /etc, not /tmp
```

---

## Example: Bug Escalation

```
Task: Connect to database

Attempt 1:
❌ Connect to postgres (Connection refused)

Attempt 2 (alternative):
❌ Check if postgres running → Not running
✅ Start postgres service → Started
❌ Connect again → Still fails (different error: auth failed)

Diagnosis: Systematic issue, not just service down

Escalation:
→ Consult triplets about postgres auth configuration
→ OR ask user for correct credentials
```

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| First failure | Try ONE alternative |
| Second failure | Stop, treat as bug |
| After fix attempt | Escalate if not resolved |
| Systematic errors | Escalate immediately |
| Making progress | Continue current approach |
| No progress (3-5 steps) | Self-correct or escalate |

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/Relay_Troubleshooting.md` - Relay-specific errors
- `/mnt/projects/Joshua/knowledge-base/TROUBLESHOOTING_WORKING_SYSTEMS.md` - Diagnosis techniques

---

*Last Updated: 2025-10-10*
