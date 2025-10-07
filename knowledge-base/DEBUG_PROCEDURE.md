# Systematic Debug Procedure

**Purpose:** Prevent going in circles. Follow this process for EVERY bug.

---

## 🔄 Standard Process (4 Steps)

### Step 1: Find the Issue
- Gather evidence systematically
- Document what's working vs. what's broken
- Identify the exact failure point
- Update BUG_TRACKING.md with findings

### Step 2: Diagnose & Propose Fix
- Analyze root cause
- Propose specific fix (code changes, config changes, etc.)
- Document proposed fix in BUG_TRACKING.md
- Do NOT attempt fix yet

### Step 3: Verify Fix with 3 LLMs
- Send fix proposal to 3 LLMs via Fiedler:
  - Gemini 2.5 Pro
  - GPT-5
  - Llama 3.3 70B (or Grok-4)
- Get confirmation/corrections from each
- Document LLM feedback in BUG_TRACKING.md

### Step 4: Attempt Fix
- Apply the verified fix
- Test the fix
- Document results in BUG_TRACKING.md
- If successful: Mark bug resolved, update RESUME_HERE.md
- If failed: Return to Step 1 with new evidence

---

## 📋 Current Bug: BUG #1

**Status:** Step 1 - Finding the Issue

**Next Actions:**
1. Check Claude Code's actual MCP configuration
2. Verify if Relay is receiving Claude Code connections
3. Check if KGB is creating spies for our sessions
4. Verify if any conversations exist in Winni with recent timestamps

---

## 📝 Process Log

### [21:10] Debug procedure established
- Created standardized 4-step process
- Ready to begin Step 1 investigation for BUG #1

---

## ⚠️ Rules
- NEVER skip steps
- NEVER attempt fix without LLM verification
- ALWAYS document everything in BUG_TRACKING.md
- ALWAYS update RESUME_HERE.md when status changes
