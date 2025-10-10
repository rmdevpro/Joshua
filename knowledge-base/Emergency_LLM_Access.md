# Emergency LLM Access - When Relay is Down

## Overview
When the MCP relay is down, you cannot use Fiedler tools (`mcp__fiedler__*`) to call LLMs. This document provides emergency workarounds to directly call LLMs for critical operations.

---

## Problem

**Normal Flow:**
```
Claude Code → MCP Relay → Fiedler MCP → LLM APIs
```

**When Relay Down:**
- Cannot use `mcp__fiedler__fiedler_send`, `fiedler_chat`, etc.
- Blocked on critical operations like:
  - Getting LLM reviews
  - Consulting LLMs for bug fixes
  - Multi-agent development workflows

---

## Solution: Direct Container Access

### Method 1: Execute via Fiedler Container

The Fiedler container has direct access to LLM client tools and API keys.

**Location:** `fiedler-mcp` or `fiedler-green` Docker containers

#### Available Tools in Container:
- Gemini client: `/app/clients/gemini_client.py`
- OpenAI client: `/app/clients/openai_client.py` (if exists)
- Grok client: Check `/app/clients/` for xai/grok tools

**Important:** Tool paths may vary by container. Verify with:
```bash
docker exec fiedler-mcp find /app -name "gemini_client.py"
```

---

## Method 1A: Call Gemini via Fiedler Container

**⚠️ IMPORTANT:** The `gemini_client.py` is a CLI script, NOT a Python module. Do NOT try to import functions from it (`from gemini_client import send_to_gemini` will fail). Always use it as a command-line tool.

### Basic Usage (Inline Prompt)

```bash
docker exec fiedler-mcp python3 /app/clients/gemini_client.py \
  --model "gemini-2.0-flash-exp" \
  "Your prompt here"
```

### With File Input (via stdin) - RECOMMENDED

**✅ CORRECT APPROACH:**
```bash
cat /path/to/file.md | docker exec -i fiedler-mcp python3 /app/clients/gemini_client.py \
  --model "gemini-2.0-flash-exp" \
  --stdin \
  > /path/to/output.md
```

**❌ WRONG APPROACH (Python import):**
```python
# This will fail with ImportError
from gemini_client import send_to_gemini  # NO!
```

### Example: Send Large Consultation Package

```bash
# Send consultation package and save response
cat /mnt/irina_storage/files/temp/logging_consultation.md | \
docker exec -i fiedler-mcp python3 /app/clients/gemini_client.py \
  --model "gemini-2.5-pro" \
  --stdin \
  > /mnt/irina_storage/files/temp/gemini_response.md
```

### Available Models

Check available models:
```bash
docker exec fiedler-mcp python3 /app/clients/gemini_client.py --list-models
```

Common models:
- `gemini-2.0-flash-exp` - Fast, large context (recommended for code)
- `gemini-2.5-pro` - Most capable, slower
- `gemini-pro` - Balanced
- `gemini-pro-vision` - For images

### Options

```bash
docker exec fiedler-mcp python3 /app/clients/gemini_client.py --help
```

Key options:
- `--model MODEL` - Which model to use
- `--temperature TEMP` - 0.0-1.0 (default 0.7)
- `--max-tokens N` - Maximum output length
- `--safety {strict,default,minimal,none}` - Safety filtering
- `--json` - Output as JSON
- `--stdin` - Read prompt from stdin

---

## Method 1B: Call GPT/OpenAI/DeepSeek via Fiedler's `fiedler_send()`

**⚠️ IMPORTANT:** Standalone client scripts like `/app/clients/openai_client.py` and `/app/clients/deepseek_client.py` **DO NOT EXIST**. Only `/app/clients/gemini_client.py` exists as a standalone script.

**For ALL other LLMs (GPT-4o, GPT-5, DeepSeek, Qwen, Llama, Grok), use Fiedler's internal `fiedler_send()` function.**

### How It Works

Fiedler has provider modules in `/app/fiedler/providers/` that handle API calls:
- `/app/fiedler/providers/openai.py` - GPT models
- `/app/fiedler/providers/gemini.py` - Gemini models
- `/app/fiedler/providers/xai.py` - Grok models
- `/app/fiedler/providers/together.py` - Together.ai models (Llama, DeepSeek, Qwen)

The `fiedler_send()` function is the unified interface that routes to these providers.

### Step 1: Create Python Script

Create a Python script in `/mnt/irina_storage/files/temp/` (accessible to container):

```python
#!/usr/bin/env python3
"""Call GPT-4o via Fiedler's fiedler_send()."""
import os
import json

# Set Fiedler config path
os.environ['FIEDLER_CONFIG'] = '/app/fiedler/config/models.yaml'

from fiedler.tools.send import fiedler_send

# Read prompt from file
with open("/mnt/irina_storage/files/temp/my_prompt.md", "r") as f:
    prompt = f.read()

# Call the LLM
result = fiedler_send(
    prompt=prompt,
    models=["gpt-4o"]  # or "gpt-5", "deepseek-r1", "grok-4", etc.
)

# Print result
print(json.dumps(result, indent=2))
```

### Step 2: Execute in Container

```bash
# Execute the script
docker exec fiedler-mcp python3 /mnt/irina_storage/files/temp/call_gpt4o.py \
  > /mnt/irina_storage/files/temp/gpt4o_result.json 2>&1
```

### Step 3: Extract Response from Result

The `fiedler_send()` result is JSON with structure:
```json
{
  "status": "success",
  "correlation_id": "...",
  "output_dir": "/mnt/irina_storage/files/outputs/...",
  "results": {
    "gpt-4o": {
      "status": "success",
      "output_file": "/mnt/irina_storage/files/outputs/.../gpt-4o_output.md",
      "tokens": {"prompt": 1234, "completion": 5678}
    }
  }
}
```

Read the actual LLM response from the `output_file` path in the result.

### Available Models via fiedler_send()

```python
models=["gpt-4o"]        # GPT-4o
models=["gpt-5"]         # GPT-5
models=["deepseek-r1"]   # DeepSeek R1
models=["grok-4"]        # Grok 4
models=["llama-3.3-70b"] # Llama 3.3 70B
models=["qwen-2.5-72b"]  # Qwen 2.5 72B
```

### Example: Send to Multiple LLMs (Parallel)

```python
result = fiedler_send(
    prompt=prompt,
    models=["gpt-4o", "deepseek-r1", "grok-4"]  # All in parallel
)
```

---

## Method 1C: Direct Grok via Standalone Client (if exists)

**Check if Grok client exists:**
```bash
docker exec fiedler-mcp ls /app/clients/ | grep -i grok
```

**If available:**
```bash
cat /path/to/file.md | docker exec -i fiedler-mcp python3 /app/clients/grok_client.py \
  --model "grok-2-1212" \
  --stdin \
  > /path/to/output.md
```

**Note:** As of 2025-10-10, only `gemini_client.py` exists as standalone. For Grok, use Method 1B with `models=["grok-4"]`.

---

## Method 2: Use Host-Mounted Tools

The Fiedler containers may have `/mnt/projects/` mounted, allowing direct execution of tools from the host filesystem.

### Check Mounts

```bash
docker inspect fiedler-mcp --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

### If /mnt/projects Mounted

```bash
# Find gemini client on host
find /mnt/projects -name "gemini_client.py" -type f

# Execute via container (if Python environment available)
docker exec -i fiedler-mcp python3 /mnt/projects/Joshua/mads/fiedler/tools/gemini_client.py \
  --stdin < /path/to/input.md \
  > /path/to/output.md
```

---

## Method 3: Direct API Calls (Last Resort)

If container access fails, use curl with API keys directly.

### Gemini API (curl)

```bash
GEMINI_API_KEY="your-key-here"

curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Your prompt here"
      }]
    }]
  }'
```

### OpenAI API (curl)

```bash
OPENAI_API_KEY="your-key-here"

curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Your prompt here"}
    ]
  }'
```

### xAI (Grok) API (curl)

```bash
XAI_API_KEY="your-key-here"

curl https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-2-1212",
    "messages": [
      {"role": "user", "content": "Your prompt here"}
    ]
  }'
```

---

## Complete Example: Multi-Agent Review Workflow

When relay is down, you can still execute the triplet review process manually:

### Step 1: Send to Gemini (Senior)

```bash
cat /mnt/irina_storage/files/temp/consultation_package.md | \
docker exec -i fiedler-mcp python3 /app/clients/gemini_client.py \
  --model "gemini-2.5-pro" \
  --stdin \
  > /mnt/irina_storage/files/temp/gemini_solution.md

echo "Gemini response saved to gemini_solution.md"
```

### Step 2: Send to GPT-4o (Junior Review)

```bash
# Create review prompt
cat > /tmp/gpt_review_prompt.md << 'EOF'
Please review the following solution for completeness, correctness, and production-readiness.

SOLUTION TO REVIEW:
---
EOF

cat /mnt/irina_storage/files/temp/gemini_solution.md >> /tmp/gpt_review_prompt.md

# Send to GPT
cat /tmp/gpt_review_prompt.md | \
docker exec -i fiedler-mcp python3 /app/clients/openai_client.py \
  --model "gpt-4o" \
  --stdin \
  > /mnt/irina_storage/files/temp/gpt4o_review.md

echo "GPT-4o review saved to gpt4o_review.md"
```

### Step 3: Send to DeepSeek (Junior Review)

```bash
# Same approach, if DeepSeek client available
cat /tmp/gpt_review_prompt.md | \
docker exec -i fiedler-mcp python3 /app/clients/deepseek_client.py \
  --stdin \
  > /mnt/irina_storage/files/temp/deepseek_review.md

echo "DeepSeek review saved to deepseek_review.md"
```

### Step 4: Read Reviews and Check Consensus

```bash
# Read both reviews
echo "=== GPT-4o Review ==="
cat /mnt/irina_storage/files/temp/gpt4o_review.md

echo -e "\n\n=== DeepSeek Review ==="
cat /mnt/irina_storage/files/temp/deepseek_review.md
```

### Step 5: If Issues Found, Send Back to Gemini

```bash
# Create consolidated feedback
cat > /tmp/revision_request.md << 'EOF'
Your solution received the following feedback from junior reviewers.
Please revise to address all concerns.

ORIGINAL SOLUTION:
---
EOF

cat /mnt/irina_storage/files/temp/gemini_solution.md >> /tmp/revision_request.md

echo -e "\n\nGPT-4o FEEDBACK:\n---" >> /tmp/revision_request.md
cat /mnt/irina_storage/files/temp/gpt4o_review.md >> /tmp/revision_request.md

echo -e "\n\nDeepSeek FEEDBACK:\n---" >> /tmp/revision_request.md
cat /mnt/irina_storage/files/temp/deepseek_review.md >> /tmp/revision_request.md

# Send revision request
cat /tmp/revision_request.md | \
docker exec -i fiedler-mcp python3 /app/clients/gemini_client.py \
  --model "gemini-2.5-pro" \
  --stdin \
  > /mnt/irina_storage/files/temp/gemini_solution_v2.md

echo "Gemini revision saved to gemini_solution_v2.md"
```

### Step 6: Repeat Until Both Approve

Iterate Steps 2-5 until both junior LLMs approve the solution.

---

## Finding API Keys

API keys are stored in environment variables in the Fiedler container:

```bash
# Check available API keys
docker exec fiedler-mcp env | grep -E "API_KEY|_KEY"
```

Common keys:
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `XAI_API_KEY`
- `ANTHROPIC_API_KEY`

---

## Troubleshooting

### Container Not Found

```bash
# List Fiedler containers
docker ps --filter "name=fiedler"

# Try fiedler-green if fiedler-mcp doesn't exist
docker exec fiedler-green python3 /app/tools/gemini_client.py --help
```

### Tool Not Found in Container

```bash
# Check what tools are available
docker exec fiedler-mcp ls /app/clients/

# Check alternative locations
docker exec fiedler-mcp find /app -name "*client.py"

# Common locations:
# - /app/clients/  (current Fiedler location)
# - /app/tools/    (older location)
# - /app/fiedler/clients/
```

### Python Import Errors

```bash
# Check if required packages installed
docker exec fiedler-mcp python3 -c "import requests; print('OK')"

# If missing, may need to install (not recommended, use different container)
```

### File Path Issues

When using stdin, files must be accessible from the host (not just inside Claude Code):

```bash
# ✅ Good - host path
cat /mnt/irina_storage/files/temp/file.md | docker exec -i fiedler-mcp ...

# ❌ Bad - local path only in Claude Code session
cat /tmp/file.md | docker exec -i fiedler-mcp ...  # Won't work if /tmp not mounted
```

**Solution:** Always use `/mnt/irina_storage/` for temporary files that need to be accessible by containers.

---

## Restoring Normal Operations

Once the relay is fixed:

1. Verify Fiedler tools are available:
```bash
# Should list all Fiedler tools
claude mcp list | grep fiedler
```

2. Test a simple call:
```bash
# Use appropriate Claude Code tool invocation
mcp__fiedler__fiedler_chat --model "gemini-2.0-flash-exp" --prompt "Test"
```

3. Switch back to normal MCP-based workflow

---

## Security Notes

⚠️ **Warning:** This document shows direct container access which bypasses:
- Fiedler's logging and auditing
- Request queuing and rate limiting
- Centralized cost tracking

**Use only when relay is down and operation is critical.**

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/Relay_Troubleshooting.md` - Fix relay issues
- `/mnt/projects/Joshua/knowledge-base/Emergency_Log_Retrieval.md` - Direct log access
- `/mnt/projects/Joshua/processes/Multi-Agent_Development_Flow_v1.0.md` - Normal workflow

---

*Last Updated: 2025-10-10*
*Created for emergency operations when MCP relay unavailable*
