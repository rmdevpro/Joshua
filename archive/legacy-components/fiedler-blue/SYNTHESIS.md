# Fiedler Implementation Synthesis Plan

## Source Implementations

**Gemini 2.5 Pro (38KB):**
- Lightweight JSON-RPC over stdio (no MCP SDK dependency)
- stderr logging, stdout for data only
- ConfigurationManager singleton (in-memory)
- Timestamped output directories
- Subprocess-based Gemini/Grok providers
- ThreadPoolExecutor parallelism

**GPT-5 (45KB - Most Comprehensive):**
- Official MCP SDK (mcp.Server)
- Persistent state (~/.fiedler/state.yaml)
- Streaming outputs to disk
- Correlation IDs for traceability
- Token estimation + preflight checks
- summary.json per run
- OpenAI SDK for OpenAI/Together

**Grok 4 (40KB):**
- JSON-RPC over stdio
- Persistent YAML state
- Exponential backoff retries
- File-based logging with correlation IDs
- Token estimation
- In-memory fallbacks

---

## Synthesis Decisions

### 1. MCP Integration
**Choice:** Official MCP SDK (from GPT-5)
**Rationale:** Cleaner than hand-rolled JSON-RPC, better integration with Claude Code
**Implementation:** Use `mcp.Server`, `mcp.types.Tool`, stdio transport

### 2. State Management
**Choice:** Persistent YAML (from GPT-5/Grok)
**Location:** `~/.fiedler/state.yaml`
**Structure:**
```yaml
models: [gemini-2.5-pro, gpt-5, llama-3.1-70b]
output_dir: /path/to/output
```
**Fallback:** Load from config/models.yaml defaults if state file missing

### 3. Logging Strategy
**Choice:** Dual logging (from all three)
- stderr: Real-time progress
- file: Per-run log with correlation ID
**Never log to stdout:** Corrupts MCP JSON-RPC transport
**Correlation ID:** UUID per run, included in all logs and filenames

### 4. Output Structure
**Choice:** Timestamped directories + summary.json (from Gemini + GPT-5)
**Structure:**
```
output_dir/
  20251002_143000_abc123/
    gemini-2_5-pro_Response.md
    gpt-5_Response.md
    llama-3_1-70b_Response.md
    summary.json
    progress.log
```

### 5. Provider Architecture
**Choice:** Hybrid (best from all three)
**BaseProvider:**
- Abstract class with `send()` method
- Retry logic with exponential backoff (from Grok)
- Token estimation (from GPT-5/Grok)
- Streaming to disk (from GPT-5)

**Concrete Providers:**
- GeminiProvider: Subprocess wrapper to `/mnt/projects/gemini-tool/gemini_client.py`
- OpenAIProvider: Direct OpenAI SDK
- TogetherProvider: OpenAI SDK with base_url override
- XAIProvider: Subprocess wrapper to `/mnt/projects/ICCM/tools/grok_client.py`

### 6. Retry Strategy
**Choice:** Exponential backoff (from Grok)
**Implementation:**
```python
max_attempts = 3
for attempt in range(max_attempts):
    try:
        return self._send_impl(...)
    except RetryableError:
        if attempt < max_attempts - 1:
            wait = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait)
        else:
            raise
```

### 7. Token Tracking
**Choice:** Track + estimate (from GPT-5/Grok)
- Extract from API responses where available (OpenAI, Together)
- Estimate for subprocess wrappers (Gemini, Grok) ~4 chars/token
- Preflight check: warn if package > 80% of model's max_tokens

### 8. Tool Design
**Choice:** 5 MCP tools with optional override (updated requirement)

**fiedler_send:**
```python
{
  "prompt": "Review this",
  "files": ["doc.md"],  # optional
  "models": ["deepseek-r1"]  # optional override of defaults
}
```

**fiedler_set_models, fiedler_set_output, fiedler_get_config, fiedler_list_models:**
(as specified in requirements)

---

## File Structure

```
fiedler/
├── pyproject.toml
├── README.md
├── SYNTHESIS.md (this file)
├── fiedler/
│   ├── __init__.py
│   ├── server.py           # MCP server main
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py        # BaseProvider with retries
│   │   ├── gemini.py      # Subprocess wrapper
│   │   ├── openai.py      # OpenAI SDK
│   │   ├── together.py    # OpenAI SDK + base_url
│   │   └── xai.py         # Subprocess wrapper
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── send.py        # fiedler_send
│   │   ├── config.py      # set/get config, set output
│   │   └── models.py      # list_models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py      # ProgressLogger
│   │   ├── package.py     # compile_package
│   │   ├── state.py       # State management
│   │   └── tokens.py      # Token estimation
│   └── config/
│       └── models.yaml    # Provider/model registry
└── tests/
    └── test_basic.py
```

---

## Implementation Order

1. ✅ Config file (models.yaml) - DONE
2. ✅ pyproject.toml - DONE
3. utils/logger.py - Thread-safe logger
4. utils/state.py - Persistent YAML state
5. utils/tokens.py - Token estimation
6. utils/package.py - File compilation
7. providers/base.py - Abstract provider with retries
8. providers/{gemini,openai,together,xai}.py - Concrete implementations
9. tools/models.py - list_models
10. tools/config.py - set_models, set_output, get_config
11. tools/send.py - fiedler_send (main orchestrator)
12. server.py - MCP server with tool registration
13. __init__.py files
14. README.md
15. tests/test_basic.py

---

## Key Features from Each

### From Gemini:
- Clean module separation
- Timestamped output directories
- Clear per-model result files

### From GPT-5:
- MCP SDK integration (cleanest approach)
- Persistent state
- Streaming to disk
- Token estimation
- summary.json

### From Grok:
- Exponential backoff retries
- Correlation ID logging
- Persistent YAML state
- In-memory fallbacks

---

## Testing Strategy

1. **Unit tests:** Provider retries, token estimation, alias resolution
2. **Integration test:** Mock API calls, verify parallel execution
3. **End-to-end test:** Real API call to one cheap model (gpt-4o-mini)
4. **Triplet review:** Send implementation for final validation

---

## Status

- [x] Synthesis plan created
- [ ] Build implementation
- [ ] Send to triplets for review
- [ ] Apply feedback
- [ ] Deploy and test
