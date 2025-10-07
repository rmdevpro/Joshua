# Fiedler Docker Workaround for Triplet Consultation

## Overview

This document describes the workaround method for consulting the Fiedler's default triplet when Fiedler MCP tools are not available in Claude Code.

**When to Use:** If Fiedler MCP integration is broken and you need to consult multiple LLMs for architecture/bug guidance.

**Status:** Tested and working as of 2025-10-03

---

## The Problem

When Fiedler MCP tools (`mcp__fiedler__fiedler_send`, etc.) are not available in Claude Code, you cannot use the standard MCP interface to consult the triplet. However, Fiedler can still be used directly via Docker.

---

## The Workaround

### Method: Direct Python Call to fiedler_send Function

Instead of using the MCP tools, call the `fiedler_send` function directly inside the Fiedler container using `docker exec`.

### Step-by-Step Process

**1. Create consultation document:**

```bash
cat > /tmp/consultation_package.md << 'EOF'
# Your consultation request here
# Include:
# - Problem statement
# - Architecture context
# - Evidence/logs
# - Specific questions
EOF
```

**2. Send to triplet via Docker:**

```bash
docker exec -i fiedler-mcp python3 << 'PYTHON_EOF'
import sys
import json
sys.path.insert(0, '/app')

from fiedler.tools.send import fiedler_send

consultation_text = """
[Your consultation text here - can be very long]
"""

print("Sending consultation to triplet...", file=sys.stderr)

try:
    result = fiedler_send(
        prompt=consultation_text
        # Uses Fiedler's default triplet models (configured in models.yaml)
    )

    print(json.dumps(result, indent=2))

except Exception as e:
    print(f"ERROR: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

PYTHON_EOF
```

**3. Read responses:**

The output will show paths to response files. Read them with:

```bash
# Get the correlation_id from the output (e.g., "f6228b7c")
CORRELATION_ID="<from_output>"

# Read Gemini response
docker exec fiedler-mcp cat /app/fiedler_output/*/gemini-2.5-pro.md

# Read GPT-5 response
docker exec fiedler-mcp cat /app/fiedler_output/*/gpt-5.md

# Read DeepSeek response
docker exec fiedler-mcp cat /app/fiedler_output/*/deepseek-ai_DeepSeek-R1.md
```

---

## Complete Example: Bug Consultation

```bash
# 1. Create consultation package
cat > /tmp/bug_consultation.md << 'EOF'
# URGENT: System Bug - Need Triplet Analysis

## Problem
[Describe the bug]

## Architecture Context
[Reference architecture PNG or key architecture facts]

## Evidence
[Logs, configuration, test results]

## Questions
1. What is the root cause?
2. What is the correct fix within existing architecture?
3. Provide exact configuration/code changes
EOF

# 2. Send to triplet
docker exec -i fiedler-mcp python3 << 'PYTHON_EOF'
import sys
import json
sys.path.insert(0, '/app')

from fiedler.tools.send import fiedler_send

# Read consultation file
with open('/tmp/bug_consultation.md', 'r') as f:
    consultation = f.read()

print("=" * 80, file=sys.stderr)
print("Sending consultation to triplet...", file=sys.stderr)
print("=" * 80, file=sys.stderr)

result = fiedler_send(
    prompt=consultation
    # Uses Fiedler's default triplet models (configured in models.yaml)
)

print(json.dumps(result, indent=2))
PYTHON_EOF

# 3. Read responses (use correlation_id from output)
CORR_ID="<from_above_output>"
docker exec fiedler-mcp cat /app/fiedler_output/*_${CORR_ID}/gemini-2.5-pro.md
docker exec fiedler-mcp cat /app/fiedler_output/*_${CORR_ID}/gpt-5.md
docker exec fiedler-mcp cat /app/fiedler_output/*_${CORR_ID}/deepseek-ai_DeepSeek-R1.md
```

---

## Model Selection

**Default behavior:** When `models` parameter is omitted, Fiedler uses its configured default models.

**To use specific models:** Pass `models=[...]` parameter with model IDs:
```python
result = fiedler_send(
    prompt=consultation,
    models=["gemini-2.5-pro"]  # Single model
)

result = fiedler_send(
    prompt=consultation,
    models=["gemini-2.5-pro", "gpt-4o", "grok-4-0709"]  # Multiple models
)
```

**To check available models:** See `/app/fiedler/config/models.yaml` in the container.

---

## Output Location

Fiedler stores all outputs in the container at:

```
/app/fiedler_output/YYYYMMDD_HHMMSS_correlationid/
├── summary.json              # Run metadata
├── fiedler.log              # Progress log
├── gemini-2.5-pro.md        # Gemini response
├── gpt-5.md                 # GPT-5 response
└── deepseek-ai_DeepSeek-R1.md  # DeepSeek response
```

To copy outputs to host:

```bash
docker cp fiedler-mcp:/app/fiedler_output/20251003_160413_f6228b7c /tmp/
```

---

## Troubleshooting

### Error: "No module named 'fiedler'"

**Cause:** Python path not set correctly

**Fix:** Ensure `sys.path.insert(0, '/app')` is at the top of the script

### Error: "API key not found"

**Cause:** API keys not configured in Fiedler container

**Fix:** Check environment variables or keyring:

```bash
docker exec fiedler-mcp env | grep -E '(GEMINI|OPENAI|TOGETHER|XAI)_API_KEY'
```

### Error: "FileNotFoundError" when copying consultation file

**Cause:** File created on host, not visible in container

**Fix:** Either:
1. Use heredoc in the Python script (as shown above)
2. Copy file into container: `docker cp /tmp/file.md fiedler-mcp:/tmp/`

### Error: "OSError: [Errno 98] address already in use"

**Cause:** Trying to run `fiedler` command which starts WebSocket server

**Fix:** Don't use `docker exec fiedler-mcp fiedler` - use the Python method shown above

---

## Real-World Usage Example

**Date:** 2025-10-03 16:04 EDT
**Situation:** Fiedler MCP tools not loading after 8 configuration attempts
**Action:** Used this workaround to consult triplet on root cause
**Result:** All 3 LLMs responded successfully in 76 seconds
**Outcome:** Unanimous diagnosis - wrong transport type (WebSocket vs stdio)

**Success Metrics:**
- Gemini: 32.2s, 1113 tokens
- DeepSeek: 41.2s, 2707 tokens
- GPT-5: 76.3s, 4284 tokens
- Total: 3/3 models succeeded

---

## Why This Works

1. **Direct Function Call:** Bypasses MCP layer entirely
2. **Container-Internal:** Runs inside Fiedler container where all dependencies exist
3. **Proven Infrastructure:** Uses same provider code that MCP tools use
4. **Full Features:** Access to all models, parallel execution, retry logic

---

## Limitations

- Cannot use from Claude Code directly (must use Bash tool)
- Output must be manually read from container
- No automatic integration with conversation history
- Requires manual copying of files in/out of container

---

## Related Documentation

- `/mnt/projects/ICCM/fiedler/README.md` - Fiedler MCP server documentation
- `/mnt/projects/ICCM/architecture/BUG_TRACKING.md` - Bug investigation process
- `/mnt/projects/ICCM/architecture/CURRENT_STATUS.md` - System status and configuration

---

## Maintenance Notes

**Last Verified:** 2025-10-03
**Fiedler Version:** 1.0.0
**Container:** fiedler-mcp
**Python Version:** 3.11

**Update History:**
- 2025-10-03: Initial documentation after successful Attempt #9 consultation
