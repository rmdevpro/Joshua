# Fiedler Multimodal Support Requirements
**Version:** 1.3 (Draft)
**Date:** 2025-10-07
**Status:** Fourth Triplet Review (Post v1.2 Feedback)
**Previous Reviews:**
- v1.0 → v1.1: GPT-5, Gemini 2.5 Pro, Grok-4
- v1.1 → v1.2: GPT-5 (NEEDS REVISION), Gemini (NEEDS REVISION minor), Grok-4 (APPROVED)
- v1.2 → v1.3: GPT-5 (NEEDS REVISION), Gemini (APPROVED), Grok-4 (APPROVED)

**Changes from v1.2 (GPT-5 critical fixes for small lab):**
- **FIX 1**: Removed Anthropic from streaming examples (Anthropic uses base64 only)
- **FIX 2**: Unified all Response examples to canonical schema
- **FIX 3**: Removed "zero breaking changes" language (acknowledged breaking change)
- **FIX 4**: NO duplicates allowed in trio selection (enforced uniqueness)
- **FIX 5**: Clarified max_cost applies to total cost (all models + subrequests)
- **FIX 6**: Added currency field ("USD") to all cost metadata
- **FIX 7**: Documented HEAD fallback to GET Range for URL validation
- **DEFER**: IPv6 SSRF (noted for production), Webhook security (TBD when implemented)

---

## 1. Overview

### 1.0 Deferred Items (Production Enhancements)

**The following items were identified in reviews but DEFERRED for small lab use case:**

1. **IPv6 SSRF Protection** - Comprehensive IPv6 private range blocking (::1, fc00::/7, fe80::/10)
   - **Status**: Defer to production deployment
   - **Reason**: Small lab doesn't use IPv6 internally
   - **Action**: Add note "IPv6 SSRF TBD for production" in security section

2. **Async Webhook Security** - HMAC signing, replay protection, full callback authentication
   - **Status**: Defer until webhooks implemented
   - **Reason**: Webhooks not critical for initial implementation
   - **Action**: Add note "Webhook security spec TBD when callbacks implemented"

These items remain in GPT-5's feedback but are intentionally out-of-scope for v1.3 small lab deployment.

### 1.1 Purpose
Extend Fiedler LLM Gateway to support multimodal capabilities (images, audio, video, documents) across all supported LLM providers, enabling applications to leverage the full capabilities of modern multimodal LLMs.

### 1.2 Design Philosophy
- **Expand capabilities, never limit options** - Support every capability each provider offers
- **Provider-specific configurations** - Respect each LLM's unique limits and preferences
- **Zero breaking changes** - All existing text-only calls continue to work unchanged
- **Multiple input methods** - Support base64, file paths, and URLs
- **Intelligent defaults** - Auto-detect, validate, and guide users
- **Complete observability** - Log everything, return detailed metadata

### 1.3 Scope

**In Scope (v1.0):**
- Images, audio, video, PDF documents, structured data files
- Multiple attachment input methods (base64, path, URL)
- Provider-specific validation and optimization
- Enhanced logging and metadata tracking
- Database schema updates for attachment storage
- **Streaming uploads** (CRITICAL: Required for large file support)
- **Security hardening** (path traversal, SSRF protection)
- **LLM trio presets** (sr_trio, std_trio, jr_trio with tag-based random selection)
- **Multi-step flow tracking** (subrequests metadata for Whisper→GPT flows)
- **Asynchronous processing** (fiedler_send_async for large files)
- **Cost estimation** (dry-run mode before execution)
- **Content hashing** (SHA256 for deduplication and auditability)

**Out of Scope (Future):**
- Real-time streaming video/audio analysis
- Attachment preprocessing/transcoding (use provider native formats)
- PII redaction (document as user responsibility)
- Virus scanning (integration point defined, not implemented)

---

## 2. Functional Requirements

### 2.1 Extended API Interface

#### 2.1.1 fiedler_send Tool Enhancement

**Current Interface:**
```python
fiedler_send(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> str
```

**New Interface:**
```python
fiedler_send(
    prompt: str,
    model: Optional[str | List[str]] = None,  # Support trio presets
    system_prompt: Optional[str] = None,
    attachments: Optional[List[Attachment]] = None,

    # Validation controls
    strict_validation: bool = True,
    max_total_bytes: Optional[int] = None,
    max_attachments: Optional[int] = None,

    # Cost & safety
    estimate_only: bool = False,  # Dry-run for cost estimation
    max_cost: Optional[float] = None,  # NEW v1.2: Total budget limit (USD)
    force_indirect_upload: bool = False,  # Prevent MCP payload bloat
) -> Response

# max_cost semantics (v1.3 clarification):
# - Applies to TOTAL estimated cost across ALL models + subrequests
# - Currency: USD (all costs normalized to USD)
# - If estimate exceeds max_cost, fail fast BEFORE dispatch
# - If runtime cost exceeds during execution, cancel remaining and return partial_success

Attachment = {
    "type": "base64" | "path" | "url" | "reference",  # NEW: reference type
    "content": str,  # base64 data, absolute file path, URL, or asset ID
    "mime_type": Optional[str],  # Auto-detected if omitted

    # NEW: Enhanced metadata
    "filename": Optional[str],           # Original filename
    "display_name": Optional[str],       # User-friendly name
    "checksum": Optional[str],           # SHA256 for TOCTOU prevention
    "size_bytes": Optional[int],         # Hint for pre-validation
    "id": Optional[str],                 # Client correlation ID
    "purpose": Optional[str],            # "prompt" | "reference" | "context"

    # URL-specific (NEW)
    "fetch_policy": Optional[str],       # "provider_fetch" | "gateway_fetch"
    "auth_profile": Optional[str],       # Secret reference (not token!)

    # Path-specific (NEW)
    "require_hash_match": Optional[bool], # Fail if checksum doesn't match

    "metadata": Optional[dict]           # Provider-specific hints
}

Response = {
    "ok": bool,                    # True if ANY model succeeded
    "status": str,                 # "success" | "partial_success" | "failed"
    "error": Optional[dict],       # Top-level error (if all models failed)
    "request_id": str,             # Trace correlation

    # ALWAYS a list, even for single-model calls (CRITICAL FIX from v1.1)
    "responses": [
        {
            "model": str,
            "response": Optional[str],     # LLM text response (or None if error)
            "error": Optional[dict],       # Per-model error
            "metadata": {
                "tokens_used": int,
                "cost": float,
                "currency": str,  # NEW v1.3: "USD" (all costs normalized)
                "processing_time_ms": int,
                "provider_request_ids": List[str],
                "attachments_processed": List[AttachmentMetadata],
                "subrequests": List[SubRequest]
            }
        }
    ],

    # Summary across all models
    "aggregate_metadata": {
        "total_tokens": int,
        "total_cost": float,
        "currency": str,            # NEW v1.3: "USD" (all costs normalized)
        "total_processing_time_ms": int,
        "models_used": List[str],
        "success_count": int,       # How many models succeeded
        "failure_count": int        # How many models failed
    }
}

# Status field values:
# - "success": All models succeeded
# - "partial_success": Some models succeeded, some failed
# - "failed": All models failed

AttachmentMetadata = {
    "input_index": int,          # NEW: Maps to input list
    "input_id": Optional[str],   # NEW: Client-provided ID
    "mime_type": str,
    "size_bytes": int,
    "format": str,
    "dimensions": Optional[str],  # For images/video: "1920x1080"
    "duration": Optional[float],  # For audio/video: seconds
    "pages": Optional[int],  # For PDFs
    "validation_status": "success" | "warning" | "error",
    "validation_message": Optional[str],

    # NEW: Provider-specific metadata
    "provider_asset_id": Optional[str],  # For reuse in follow-up calls
    "bytes_transferred": int,
    "transcoded": bool,
    "fetch_mode": Optional[str],  # "url_pass_through" | "downloaded"
    "file_hash": Optional[str]    # SHA256 of content
}

SubRequest = {
    "kind": str,  # "transcription" | "ingestion" | "upload" | "inference"
    "provider": str,
    "model": str,
    "bytes_in": int,
    "bytes_out": int,
    "cost": float,
    "duration_ms": int,
    "status": str,  # "success" | "failed" | "partial"
    "request_id": str,
    "error": Optional[dict],
    "retry_count": Optional[int],  # NEW: Number of retries
    "retry_errors": Optional[List[dict]]  # NEW: Transient failure history
}
```

#### 2.1.2 LLM Trio Presets

**Purpose:** Enable parallel execution across multiple LLMs with predefined presets using tag-based random selection for variation.

**Model Tag Classification with Weighted Selection:**
```python
MODEL_TAGS = {
    "premium": [
        {"model": "gpt-5", "weight": 0.5},            # 50% chance
        {"model": "claude-opus", "weight": 0.05},     # 5% chance
        {"model": "gemini-2.5-pro", "weight": 0.5},   # 50% chance
        {"model": "grok-2", "weight": 0.05}           # 5% chance (moved from standard)
    ],
    "standard": [
        {"model": "gpt-4o", "weight": 0.5},           # 50% chance
        {"model": "gpt-4o-mini", "weight": 0.5},      # 50% chance
        {"model": "claude-3-sonnet", "weight": 0.5},  # 50% chance
        {"model": "deepseek", "weight": 0.5},         # 50% chance
        {"model": "qwen-2.5", "weight": 0.5}          # 50% chance
    ],
    "open_source": [
        {"model": "llama-3.3", "weight": 0.5},        # 50% chance (Together AI)
        {"model": "llama-3.1", "weight": 0.5},        # 50% chance (Together AI)
        {"model": "mixtral-8x7b", "weight": 0.5},     # 50% chance (Together AI)
        {"model": "qwen-2.5-coder", "weight": 0.5}    # 50% chance (Together AI)
    ]
}
```

**Weighted Selection Logic:**
Models with higher weights are selected more frequently. Weights don't need to sum to 1.0 within a tier - they represent relative probability.

**CRITICAL: NO DUPLICATES ALLOWED**
Trio selection MUST select 3 different models. Duplicates are not allowed (wastes money, defeats diversity purpose).

**Example Selection:**
```python
import random

def select_trio(preset_name: str) -> List[str]:
    """Select models for trio with NO duplicates (enforced uniqueness)"""
    preset = TRIO_PRESETS[preset_name]
    selected = []

    for tier in preset["composition"]:
        # Pick one model from tier that's NOT already selected
        available = [m for m in MODEL_TAGS[tier] if m["model"] not in selected]

        if not available:
            raise ValueError(f"Cannot select unique model from {tier} - all already selected")

        weights = [m["weight"] for m in available]
        model = random.choices(available, weights=weights, k=1)[0]
        selected.append(model["model"])

    return selected

# Example trio selections (always 3 DIFFERENT models):
# sr_trio: ["gpt-5", "gemini-2.5-pro", "grok-2"]
# sr_trio: ["gemini-2.5-pro", "gpt-5", "claude-opus"]
# std_trio: ["gpt-4o", "llama-3.3", "gemini-2.5-pro"]
#
# NEVER: ["gpt-5", "gpt-5", "gemini-2.5-pro"] ❌ REJECTED - duplicate
```

**Rationale for Weights:**
- **Opus (5%)**: Expensive, use sparingly
- **Grok-2 (5%)**: Premium model but less proven, lower selection rate
- **GPT-5, Gemini 2.5 Pro (50%)**: Primary premium models
- **All standard/open_source (50%)**: Equal likelihood within their tiers

**Model Parameter Enhancement:**
```python
# Single model (existing behavior)
model="gemini-2.5-pro"

# Custom set of models
model=["gemini-2.5-pro", "gpt-4o", "claude-3-sonnet"]

# Preset trios with random selection
model="sr_trio"   # 3x premium (randomly selected each request)
model="std_trio"  # 1 premium + 1 standard + 1 open source (random)
model="jr_trio"   # 1 standard + 2x open source (random)
```

**Preset Selection Logic:**
```python
TRIO_PRESETS = {
    "sr_trio": {
        "composition": ["premium", "premium", "premium"],
        "description": "3 randomly selected premium models"
    },
    "std_trio": {
        "composition": ["premium", "standard", "open_source"],
        "description": "1 premium + 1 standard + 1 open source (random)"
    },
    "jr_trio": {
        "composition": ["standard", "open_source", "open_source"],
        "description": "1 standard + 2 open source models (random)"
    }
}

# Example execution results (different each time)
# Request 1 - sr_trio: [gpt-5, claude-opus, gemini-2.5-pro]
# Request 2 - sr_trio: [gemini-2.5-pro, gpt-5, claude-opus]
# Request 1 - std_trio: [gemini-2.5-pro, gpt-4o, llama-3.3]
# Request 2 - std_trio: [gpt-5, deepseek, mixtral-8x7b]
# Request 1 - jr_trio: [gpt-4o-mini, llama-3.1, qwen-2.5-coder]
# Request 2 - jr_trio: [deepseek, llama-3.3, mixtral-8x7b]
```

**Response Format for Multiple Models:**
```python
Response = {
    "responses": [
        {
            "model": "gemini-2.5-pro",
            "response": str,
            "metadata": { ... }
        },
        {
            "model": "gpt-4o-mini",
            "response": str,
            "metadata": { ... }
        },
        {
            "model": "deepseek",
            "response": str,
            "metadata": { ... }
        }
    ],
    "aggregate_metadata": {
        "total_tokens": int,
        "total_cost": float,
        "total_processing_time_ms": int,
        "models_used": List[str]
    }
}
```

**Execution Behavior:**
- Execute requests in parallel to all models in the set
- Return all responses in a list
- Include per-model metadata and aggregate metadata
- If any model fails, include error in that model's response but continue with others
- For single model requests, maintain backward-compatible response format

#### 2.1.3 Backward Compatibility & Migration

**BREAKING CHANGE from v0.x:** Return type changed from `str` to `Response` dict

**v1.2 CRITICAL CHANGE:** Response structure unified (always use `responses` list)

**Rationale:**
- v1.0-v1.1: Mixed single/multi-model response shapes forced `isinstance()` checks
- v1.2: All three reviewers agreed - always return same structure

**v1.2 Response Structure (Unified):**
```python
# Text-only call (no attachments, single model)
response = fiedler_send(
    prompt="What is 2+2?",
    model="gpt-4o"
)

# Returns (always same structure):
{
    "ok": True,
    "status": "success",
    "request_id": "req_abc123",

    # ALWAYS a list, even for single model
    "responses": [
        {
            "model": "gpt-4o",
            "response": "4",
            "error": None,
            "metadata": {
                "tokens_used": 10,
                "cost": 0.00015,
                "processing_time_ms": 120,
                "provider_request_ids": ["req_openai_xyz"],
                "attachments_processed": [],
                "subrequests": []
            }
        }
    ],

    "aggregate_metadata": {
        "total_tokens": 10,
        "total_cost": 0.00015,
        "total_processing_time_ms": 120,
        "models_used": ["gpt-4o"],
        "success_count": 1,
        "failure_count": 0
    }
}

# Access response: response["responses"][0]["response"]
```

**Migration Guide:**

**From v0.x (str return):**
```python
# v0.x code:
result = fiedler_send(prompt="test")
print(result)  # Was string

# v1.2+ migration:
result = fiedler_send(prompt="test")
print(result["responses"][0]["response"])
```

**From v1.0-v1.1 (mixed dict return):**
```python
# v1.0-v1.1 code:
result = fiedler_send(prompt="test")
print(result["response"])  # Single model

# v1.2+ migration:
result = fiedler_send(prompt="test")
print(result["responses"][0]["response"])
```

**Backward-Compatible Wrapper:**
```python
def fiedler_send_legacy(prompt: str, **kwargs) -> str:
    """Wrapper returning string for v0.x compatibility"""
    response = fiedler_send(prompt, **kwargs)
    if not response["ok"]:
        raise Exception(f"Error: {response['error']}")
    return response["responses"][0]["response"]

# Usage:
result = fiedler_send_legacy(prompt="test")  # Returns string
print(result)
```

**Why This is Worth the Breaking Change:**
1. Consistent, predictable API (no type checking)
2. Full metadata always available
3. Trio presets work seamlessly
4. Future-proof for new features

### 2.2 Attachment Input Methods

#### 2.2.1 Base64 Inline
**Use case:** Small files, data already in memory
```python
attachments=[{
    "type": "base64",
    "content": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "mime_type": "image/png"  # Optional, auto-detected from base64 header
}]
```

#### 2.2.2 File Path
**Use case:** Local files, large files
```python
attachments=[{
    "type": "path",
    "content": "/mnt/irina_storage/files/audio/recording.m4a",
    "mime_type": "audio/m4a"  # Optional, auto-detected from file
}]
```

**Requirements:**
- Fiedler must have read access to the file path
- Auto-detect mime type from file extension and magic bytes
- Support relative paths (resolved from Fiedler's working directory)
- Validate file exists before attempting to send

#### 2.2.3 URL Reference
**Use case:** Files hosted externally, avoid data transfer
```python
attachments=[{
    "type": "url",
    "content": "https://example.com/image.jpg",
    "mime_type": "image/jpeg"  # Optional, auto-detected from Content-Type header
}]
```

**Requirements:**
- Validate URL is accessible before sending
- Auto-detect mime type from Content-Type header
- Support authentication headers if needed (future enhancement)
- Provider determines whether to fetch URL or pass through

**URL Validation Strategy (v1.3):**
```python
def validate_url(url: str) -> tuple[bool, dict]:
    """Validate URL accessibility and extract metadata"""
    try:
        # Try HEAD request first (fast, doesn't download content)
        response = requests.head(url, timeout=10, allow_redirects=True)
        return True, {
            "size": response.headers.get("Content-Length"),
            "mime_type": response.headers.get("Content-Type")
        }
    except requests.exceptions.MethodNotAllowed:
        # Fallback: Some servers don't support HEAD
        # Use GET with Range header to download only first few bytes
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"Range": "bytes=0-2047"}  # First 2KB only
        )
        return True, {
            "mime_type": response.headers.get("Content-Type"),
            "size": response.headers.get("Content-Range")  # If supported
        }
```

### 2.3 MIME Type Auto-Detection

**CRITICAL CHANGE from v1.0:** Magic bytes detection now precedes file extension

**Rationale:** All three reviewers identified that trusting file extensions before content inspection is a security risk. Users can rename `.exe` to `.jpg` and bypass validation.

**Detection Strategy (in order of precedence):**
1. Explicitly provided `mime_type` parameter (user override)
2. **Magic bytes inspection** (most reliable - reads first N bytes of content)
3. Content-Type HTTP header (url type only)
4. File extension mapping (fallback for unrecognized magic bytes)
5. `application/octet-stream` (final fallback)

**Security Note:** Many providers reject `application/octet-stream`. If detection fails, error message guides user to specify `mime_type` explicitly.

**TOCTOU Prevention:** When `checksum` provided in Attachment, verify hash after reading to detect file modifications between validation and processing.

**Supported MIME Types (Initial Implementation):**

**Images:**
- `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- `image/svg+xml`, `image/bmp`, `image/tiff`

**Audio:**
- `audio/mpeg` (mp3), `audio/mp4` (m4a), `audio/wav`
- `audio/ogg`, `audio/webm`, `audio/flac`, `audio/aac`

**Video:**
- `video/mp4`, `video/webm`, `video/quicktime` (mov)
- `video/x-msvideo` (avi), `video/mpeg`

**Documents:**
- `application/pdf`
- `text/plain`, `text/csv`, `text/html`, `text/markdown`
- `application/json`, `application/xml`

**Archives/Data:**
- `application/zip`, `application/x-tar`
- `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 2.4 Asynchronous Processing

**NEW REQUIREMENT from v1.0 feedback:** Critical for large file processing (Gemini emphasized)

**Problem:** Synchronous `fiedler_send` will timeout for large files (e.g., 1GB video takes minutes to process).

**Solution: NEW fiedler_send_async tool**

```python
fiedler_send_async(
    prompt: str,
    model: str,
    attachments: List[Attachment],
    callback_url: Optional[str] = None  # Webhook when complete
) -> {
    "job_id": str,
    "status": "queued",
    "estimated_completion_ms": int
}

fiedler_get_status(job_id: str) -> {
    "job_id": str,
    "status": "pending" | "processing" | "completed" | "failed",
    "progress": float,  # 0.0 to 1.0
    "result": Optional[Response],  # Present when completed
    "error": Optional[dict],        # Present when failed
    "created_at": str,
    "started_at": Optional[str],
    "completed_at": Optional[str]
}

fiedler_cancel_job(job_id: str) -> {"ok": bool, "message": str}
```

**Database Support:**
```sql
CREATE TABLE async_jobs (
    job_id VARCHAR(100) PRIMARY KEY,
    status VARCHAR(20),
    progress FLOAT DEFAULT 0.0,
    request_payload JSONB,
    response_payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error JSONB,
    callback_url TEXT
);
```

**Usage Guidance:**
- Use `fiedler_send_async` for attachments > 100MB
- Use for video files (always slow to process)
- Use for trio presets with many attachments (parallel execution takes time)
- Poll with `fiedler_get_status` or provide `callback_url`

### 2.5 Provider-Specific Configuration

#### 2.4.1 Provider Capabilities Matrix

Each provider has different multimodal capabilities:

| Provider | Images | Audio | Video | PDFs | Max File Size | Notes |
|----------|--------|-------|-------|------|---------------|-------|
| **Gemini 2.5 Pro** | ✅ | ✅ | ✅ | ✅ | 2GB | Native multimodal, supports all formats |
| **GPT-4o** | ✅ | ⚠️ | ⚠️ | ⚠️ | 20MB | Vision API for images, Whisper for audio |
| **GPT-5** | ✅ | ⚠️ | ⚠️ | ⚠️ | 20MB | Vision API for images, Whisper for audio |
| **Claude 3.7 Sonnet** | ✅ | ❌ | ❌ | ✅ | 5MB | Images and PDFs only |
| **Grok 2** | ✅ | ❌ | ❌ | ❌ | 10MB | Images only |
| **Llama 3.3** | ⚠️ | ❌ | ❌ | ❌ | Varies | Depends on deployment |
| **DeepSeek** | ⚠️ | ❌ | ❌ | ❌ | Varies | Limited multimodal |
| **Qwen 2.5** | ⚠️ | ❌ | ❌ | ❌ | Varies | Limited multimodal |

Legend: ✅ Full support, ⚠️ Limited/requires preprocessing, ❌ Not supported

#### 2.4.2 Provider Configuration Storage

Store provider capabilities in Fiedler configuration:

```python
PROVIDER_CONFIGS = {
    "gemini-2.5-pro": {
        "supports_multimodal": True,
        "max_file_size": 2 * 1024 * 1024 * 1024,  # 2GB
        "supported_mime_types": [
            "image/*", "audio/*", "video/*", "application/pdf", "text/*"
        ],
        "preferred_input_method": "path",  # or "base64", "url"
        "max_attachments": 10,
        "cost_multiplier": {
            "image": 1.5,
            "audio": 2.0,
            "video": 3.0,
            "pdf": 1.2
        }
    },
    "gpt-4o": {
        "supports_multimodal": True,
        "max_file_size": 20 * 1024 * 1024,  # 20MB
        "supported_mime_types": ["image/*"],
        "preferred_input_method": "base64",
        "max_attachments": 10,
        "vision_api_endpoint": "https://api.openai.com/v1/chat/completions"
    },
    # ... other providers
}
```

### 2.5 Validation & Error Handling

#### 2.5.1 Pre-Send Validation

**Validate before sending to provider:**
1. File exists and is readable (path type)
2. URL is accessible (url type)
3. MIME type is supported by provider
4. File size within provider limits
5. Attachment count within provider limits
6. Total payload size within MCP protocol limits

#### 2.5.2 Error Response Format

```python
{
    "error": True,
    "error_code": "ATTACHMENT_TOO_LARGE",
    "message": "Audio file (15MB) exceeds GPT-4o limit (20MB)",
    "details": {
        "attachment_index": 0,
        "file_size": 15728640,
        "max_size": 20971520,
        "provider": "gpt-4o",
        "suggested_action": "Use Gemini 2.5 Pro (supports up to 2GB) or compress file"
    }
}
```

**Error Codes (EXPANDED from v1.0):**

**File/Path Errors:**
- `ATTACHMENT_NOT_FOUND` - File path doesn't exist
- `ATTACHMENT_NOT_READABLE` - Permission denied
- `PATH_OUTSIDE_ALLOWLIST` - Path traversal attempt detected
- `SYMLINK_FORBIDDEN` - Symlink points outside allowed roots
- `CHECKSUM_MISMATCH` - File changed during processing (TOCTOU)

**Validation Errors:**
- `ATTACHMENT_TOO_LARGE` - Exceeds provider limit
- `ATTACHMENT_UNSUPPORTED_TYPE` - MIME type not supported by provider
- `ATTACHMENT_COUNT_EXCEEDED` - Too many attachments
- `MIME_TYPE_DETECTION_FAILED` - Cannot determine file type
- `MIME_MISMATCH` - Detected type doesn't match declared type
- `UNSUPPORTED_COMBINATION` - Invalid provider+attachment combo

**URL Errors:**
- `URL_NOT_ACCESSIBLE` - URL fetch failed
- `URL_FORBIDDEN` - SSRF protection blocked URL
- `URL_AUTH_REQUIRED` - URL requires authentication
- `UNSAFE_URL` - HTTP instead of HTTPS
- `HEAD_UNSUPPORTED` - Server doesn't support HEAD request

**Base64 Errors:**
- `INVALID_BASE64` - Malformed base64 data

**Provider Errors:**
- `PROVIDER_NOT_MULTIMODAL` - Selected model doesn't support attachments
- `PROVIDER_UPLOAD_FAILED` - Provider-specific upload error
- `TRANSCRIPTION_FAILED` - Audio transcription error
- `RATE_LIMITED` - Provider rate limit hit

**System Errors:**
- `TIMEOUT` - Operation exceeded time limit
- `PAYLOAD_TOO_LARGE_MCP` - Would exceed MCP message limits
- `INTERNAL_STREAM_ERROR` - Streaming upload failure

#### 2.5.3 Logging

**Log to Godot (via logger_log tool):**
- Every attachment validation (success/failure)
- File size, mime type, detection method
- Provider selection and capability matching
- Processing time per attachment
- Errors with full context

**Example log entry:**
```python
{
    "component": "fiedler",
    "level": "INFO",
    "message": "Multimodal request processed",
    "data": {
        "model": "gemini-2.5-pro",
        "attachments": [
            {
                "type": "path",
                "mime_type": "audio/m4a",
                "size_bytes": 11534336,
                "validation": "success",
                "detection_method": "file_extension"
            }
        ],
        "tokens_used": 1250,
        "cost": 0.035,
        "processing_time_ms": 3420
    }
}
```

### 2.6 Security Requirements

**NEW SECTION from v1.0 feedback:** All three reviewers emphasized security gaps

#### 2.6.1 Path Traversal Prevention

**Requirements:**
- Maintain allowlist of base directories (e.g., `/mnt/irina_storage`, `/app/allowed_files`)
- Resolve all paths to canonical absolute paths using `realpath()`
- Reject paths containing `..`, `.`, or symlinks escaping allowed roots
- Validate resolved path is under an allowed root before processing

**Implementation:**
```python
ALLOWED_FILE_ROOTS = [
    "/mnt/irina_storage/files",
    "/app/allowed_files",
    "/app/fiedler_output"
]

def validate_path(path: str) -> tuple[bool, str]:
    """Returns (is_valid, canonical_path or error_message)"""
    resolved = os.path.realpath(path)
    for root in ALLOWED_FILE_ROOTS:
        if resolved.startswith(root + "/") or resolved == root:
            return True, resolved
    return False, f"Path outside allowed roots: {resolved}"
```

**Test Cases (MUST pass):**
- `../../../etc/passwd` → REJECTED
- `/etc/shadow` → REJECTED
- Symlink to `/home/user/.ssh/id_rsa` → REJECTED
- `/mnt/irina_storage/../../../etc/passwd` → REJECTED
- `/mnt/irina_storage/files/valid.pdf` → ACCEPTED

#### 2.6.2 SSRF (Server-Side Request Forgery) Protection

**Requirements:**
- Block private IP ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`
- Block cloud metadata endpoints: `169.254.169.254`, `fd00:ec2::254`
- Enforce HTTPS-only (reject `http://` URLs)
- Optional domain allowlist/denylist (configurable per environment)
- Redact query strings from logs (may contain secrets)
- Timeout URL fetches (default: 10 seconds)
- Follow redirects max 3 hops, re-validate each hop

**Configuration:**
```python
URL_ACCESS_POLICY = {
    "mode": "permissive",  # or "allowlist" or "denylist"
    "allowed_domains": ["*.example.com", "trusted-cdn.com"],
    "blocked_domains": ["*.internal.company.com"],
    "block_private_ips": True,
    "block_cloud_metadata": True,
    "require_https": True,
    "max_redirects": 3,
    "timeout_seconds": 10
}
```

**Test Cases (MUST pass):**
- `http://169.254.169.254/` → REJECTED (metadata)
- `http://localhost:8080/admin` → REJECTED (private)
- `http://192.168.1.1/` → REJECTED (private)
- `http://example.com/file.pdf` → REJECTED (HTTP)
- `https://example.com/file.pdf` → ACCEPTED

#### 2.6.3 Content Scanning & Malicious Files

**Requirements:**
- Enforce file size hard caps before reading (prevent memory exhaustion)
- Limit magic byte inspection to first 8KB (prevent processing exploits)
- Gracefully handle malformed files without crashing
- Add integration point for virus scanning (ClamAV) - optional, not required v1.0

**Test Cases (MUST pass):**
- Zip bomb (extremely compressed) → REJECTED (size check)
- Malformed PDF → HANDLED gracefully with clear error
- `fake_image.jpg.exe` → Detected as `application/x-executable` via magic bytes
- Unicode null byte injection `file_\x00_bypass.txt` → Sanitized

#### 2.6.4 Data Privacy & Retention

**Requirements:**
- Add `attachments_expires_at` timestamp to database
- Implement purge policy (default: 30 days, configurable)
- Optional: Store only file hash, not full path (`store_file_paths: bool = True`)
- Redact secrets from logs (never log full URLs with query params, never log full file paths in production)
- Secure deletion: Wipe temporary files on cleanup

**Configuration:**
```python
PRIVACY_POLICY = {
    "retention_days": 30,
    "store_file_paths": True,   # If False, only store hash
    "redact_logs": True,         # Remove paths/URLs from logs
    "secure_temp_deletion": True # Wipe temp files
}
```

---

## 3. Technical Requirements

### 3.1 MCP Protocol Changes

**No breaking changes to MCP protocol.** Attachments are passed as structured JSON within existing tool parameter framework.

**Payload size considerations:**
- Base64 encoding increases size by ~33%
- Large files (>10MB base64) may hit MCP message size limits
- Prefer `path` or `url` types for large files

### 3.2 Streaming Uploads

**CRITICAL CHANGE from v1.0:** Streaming is NOW REQUIRED in Phase 1 (not future enhancement)

**Rationale:** All three reviewers identified that without streaming, the stated 2GB support is impossible:
- Base64 encoding 100MB creates ~133MB string in memory
- Naive file reading loads entire file into memory
- This causes OOM errors under concurrent load

**Implementation Requirements:**

#### 3.2.1 For Path → Provider Flows
```python
# Use streaming where provider supports it
def upload_with_streaming(file_path: str, provider: str):
    with open(file_path, 'rb') as f:
        if provider == "gemini":
            # Gemini supports chunked upload
            upload_id = gemini.start_upload(metadata)
            while chunk := f.read(8 * 1024 * 1024):  # 8MB chunks
                gemini.upload_chunk(upload_id, chunk)
            return gemini.finalize_upload(upload_id)

        elif provider in ["openai", "anthropic"]:
            # Direct streaming upload
            return provider_api.upload_stream(f)
```

#### 3.2.2 For Providers Requiring Pre-Upload (S3 Presigned URLs)
```python
# Implement chunked multipart upload
def upload_to_s3_presigned(file_path: str, urls: List[str]):
    part_size = 5 * 1024 * 1024  # 5MB minimum for S3 multipart
    with open(file_path, 'rb') as f:
        parts = []
        for i, url in enumerate(urls):
            chunk = f.read(part_size)
            etag = requests.put(url, data=chunk).headers['ETag']
            parts.append({'PartNumber': i+1, 'ETag': etag})
    return complete_multipart_upload(parts)
```

#### 3.2.3 Fallback for Non-Streaming Providers
- Enforce strict size limits (e.g., 20MB max)
- Clear error messages: "File too large for base64, use streaming-capable provider or reduce size"
- Guidance in error: "Use Gemini (supports up to 2GB with streaming)"

**Memory Budget:**
- Maximum 2x file size in memory during processing
- Stream directly from disk to network where possible
- No intermediate buffering of entire file

### 3.2 Provider Implementation Changes

#### 3.2.1 Gemini Provider
- Native multimodal support via `genai.upload_file()` API
- Support all attachment types natively
- Return detailed metadata (tokens, processing time)

#### 3.2.2 OpenAI Provider (GPT-4o, GPT-5)
- Images: Use Vision API (`messages` with `image_url` content type)
- Audio: Route through Whisper API first, then send transcript
- Combine multiple API calls transparently

#### 3.2.3 Anthropic Provider (Claude)
- Images/PDFs: Use Messages API with base64 content blocks
- Validate file size < 5MB before encoding

#### 3.2.4 xAI Provider (Grok)
- Images only: Use messages API
- Validate and reject other attachment types early

#### 3.2.5 Together AI / DeepSeek / Qwen
- Check deployment-specific capabilities
- Gracefully degrade or error if multimodal not supported

### 3.3 Database Schema Changes

#### 3.3.1 Conversation Storage (Dewey/Winni)

**Add attachment metadata to messages table:**

```sql
ALTER TABLE messages ADD COLUMN attachments JSONB;

-- Example data:
{
    "attachments": [
        {
            "type": "path",
            "mime_type": "audio/m4a",
            "size_bytes": 11534336,
            "file_path": "/mnt/irina_storage/files/audio/recording.m4a",
            "file_hash": "sha256:abc123...",
            "processed_at": "2025-10-07T12:00:00Z"
        }
    ]
}
```

#### 3.3.2 Cost Tracking

**Extend cost tracking to include multimodal charges:**

```sql
ALTER TABLE llm_usage ADD COLUMN attachment_cost DECIMAL(10, 4);
ALTER TABLE llm_usage ADD COLUMN attachment_count INTEGER;
ALTER TABLE llm_usage ADD COLUMN attachment_types JSONB;
```

#### 3.3.3 Provider Capabilities Table (New)

```sql
CREATE TABLE provider_capabilities (
    provider_name VARCHAR(100) PRIMARY KEY,
    supports_images BOOLEAN DEFAULT FALSE,
    supports_audio BOOLEAN DEFAULT FALSE,
    supports_video BOOLEAN DEFAULT FALSE,
    supports_documents BOOLEAN DEFAULT FALSE,
    max_file_size_bytes BIGINT,
    max_attachments INTEGER,
    supported_mime_types JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 File Access & Security

#### 3.4.1 File Path Access
- Fiedler container must have read access to attachment directories
- Mount `/mnt/irina_storage` as read-only in container
- Validate all paths are within allowed directories (no path traversal)
- Support both absolute and relative paths

#### 3.4.2 URL Access
- Validate URLs before fetching (allowlist domains if needed)
- Follow redirects up to N hops
- Timeout after T seconds
- Support HTTPS only (no HTTP for security)

#### 3.4.3 Base64 Validation
- Validate base64 encoding before processing
- Check decoded size against limits
- Inspect magic bytes to confirm mime type

---

## 4. Non-Functional Requirements

### 4.1 Performance

**Target Metrics:**
- Attachment validation: < 100ms per file
- Base64 encoding: < 500ms for 10MB file
- Total overhead: < 1s for typical multimodal request
- Provider API calls: As fast as provider allows

**Optimization Strategies:**
- Lazy loading: Only read file when needed
- Streaming: For large files, stream to provider without loading into memory
- Caching: Cache file metadata (size, mime type) temporarily
- Parallel: Process multiple attachments concurrently

### 4.2 Reliability

**Error Handling:**
- Graceful degradation: If attachment fails, provide clear error
- Retry logic: Retry transient failures (network, etc.)
- Fallback: Suggest alternative providers if current one fails
- Validation: Fail fast with clear messages

**Logging:**
- Log every attachment operation (Godot MCP logger)
- Include full context for debugging
- Track success/failure rates per provider

### 4.3 Usability

**Developer Experience:**
- Clear error messages with suggested fixes
- Auto-detection reduces boilerplate
- Multiple input methods for flexibility
- Rich metadata for debugging

**Documentation:**
- Examples for each attachment type
- Provider capability matrix
- Common error scenarios and solutions
- Best practices guide

### 4.4 Maintainability

**Code Organization:**
- Separate attachment handling from core LLM logic
- Provider-specific code in provider modules
- Shared validation/detection utilities
- Comprehensive test coverage

**Testing:**
- Unit tests for mime type detection
- Unit tests for validation logic
- Integration tests with mock providers
- End-to-end tests with real files

---

## 5. Implementation Plan

**REVISED from v1.0 based on triplet feedback**

### 5.1 Phase 1: Core Infrastructure (CRITICAL PATH)

**Data Structures:**
1. Define enhanced `Attachment` structure (checksum, id, purpose, etc.)
2. Define `Response` structure with `ok` flag, `subrequests`, unified format
3. Define `SubRequest` structure for multi-step tracking

**Security (CRITICAL - Phase 1):**
4. Implement path traversal prevention (allowlist, realpath validation)
5. Implement SSRF protection (private IP blocking, HTTPS enforcement)
6. Implement symlink resolution and validation

**MIME Detection (with corrected precedence):**
7. Implement magic bytes detection (using `python-magic` or `filetype`)
8. Implement fallback to file extension
9. Implement TOCTOU prevention (checksum verification)

**Streaming Uploads (CRITICAL - Phase 1):**
10. Implement streaming for path→Gemini (chunked upload)
11. Implement streaming for path→OpenAI (direct stream for audio/Whisper only)
12. Implement S3 presigned URL multipart upload (if needed)
13. Anthropic: Base64 only with strict <5MB size limit (NO streaming support)

**Internal Module Structure:**
14. Build `AttachmentResolver` module
15. Build `CapabilityMatcher` module
16. Build `MimeDetector` module with security limits
17. Build `Validators` module (path, URL, size, type)
18. Build `Orchestrator` module for multi-step flows

**API & Logging:**
19. Update MCP tool definitions with new parameters
20. Implement error unification (always return Response dict)
21. Implement logging with redaction (no secrets, no full paths)
22. Add `request_id` generation for trace correlation

**Estimated Duration:** 3-4 weeks

### 5.2 Phase 2: Provider Integration

**Gemini Provider (Full Multimodal):**
1. Implement streaming upload via `genai.upload_file()`
2. Test all attachment types (images, audio, video, PDFs)
3. Implement provider_asset_id tracking for reuse
4. Test deduplication via content hashing

**OpenAI Provider (Vision + Whisper):**
5. Implement multi-step orchestration (Whisper→GPT-4o)
6. Implement subrequests metadata tracking
7. Test cost roll-up accuracy
8. Implement retry logic for transient failures

**Anthropic Provider (Images/PDFs):**
9. Implement base64 conversion with size validation (<5MB)
10. Test images and PDFs

**xAI Provider (Images Only):**
11. Implement with early validation (reject non-images)

**Trio Preset Routing:**
12. Implement tag-based model selection (sr_trio, std_trio, jr_trio)
13. Implement parallel execution to all models
14. Implement aggregate metadata collection
15. Test partial failure handling

**Provider Capability Management:**
16. Implement database-backed capabilities table
17. Implement `update_provider_capabilities()` refresh function
18. Add model-variant granularity

**Estimated Duration:** 3-4 weeks

### 5.3 Phase 2.5: Asynchronous Processing (NEW)

**Critical for Large Files:**
1. Implement `fiedler_send_async()` tool
2. Implement `fiedler_get_status()` tool
3. Implement `fiedler_cancel_job()` tool
4. Create `async_jobs` database table
5. Build background worker for job processing
6. Implement progress tracking
7. Optional: Webhook callback support
8. Test with 1GB+ files

**Estimated Duration:** 1-2 weeks

### 5.4 Phase 3: Database & Observability

**Database Schema:**
1. Update messages table (add attachments JSONB with file_hash, provider_asset_id)
2. Create async_jobs table
3. Update llm_usage table (add subrequest cost tracking)
4. Add retention timestamps (attachments_expires_at)

**Cost Tracking:**
5. Implement subrequest cost aggregation
6. Implement `estimate_cost()` function for dry-run
7. Implement budget enforcement (max_cost parameter)
8. Test cost roll-up with multi-step flows

**Content Hashing & Deduplication:**
9. Implement SHA256 calculation for path attachments
10. Implement deduplication query before upload
11. Implement provider_asset_id reuse
12. Add "reference" attachment type for reuse

**Enhanced Logging:**
13. Structured logs with request_id/trace_id in every line
14. Per-attachment success/failure metrics
15. Provider-specific error tracking

**Estimated Duration:** 2 weeks

### 5.5 Phase 4: Testing & Documentation

**Security Testing (CRITICAL):**
1. Path traversal battery (50+ test cases)
2. SSRF attempts (private IPs, metadata endpoints)
3. Malicious file handling (zip bombs, malformed PDFs)
4. TOCTOU scenarios (file modified during processing)
5. Fuzzing tests for MIME detection and base64 decoder

**Performance Testing:**
6. Load testing with Locust (100+ concurrent requests)
7. Memory profiling (ensure <2x file size)
8. Large file streaming validation (100MB, 500MB, 2GB)
9. Concurrent upload stress testing

**Trio Preset Testing:**
10. All combinations (sr_trio, std_trio, jr_trio)
11. Partial failure handling
12. Cost aggregation accuracy
13. Random selection variation (10+ runs per preset)

**Documentation:**
14. Update Fiedler README with v1.1 features
15. Security best practices guide
16. Cost management guide
17. Troubleshooting common errors
18. Examples for all attachment types and trio presets

**Estimated Duration:** 2 weeks

**Total Estimated Duration:** 11-13 weeks

---

## 6. Testing Strategy

### 6.1 Unit Tests
- Mime type detection (50+ file types)
- Validation logic (all error conditions)
- Base64 encoding/decoding
- Provider capability matching

### 6.2 Integration Tests
- Each provider with sample files
- Multi-attachment requests
- Error scenarios (file not found, too large, etc.)
- Backward compatibility (text-only still works)

### 6.3 End-to-End Tests
- Real audio transcription (Gemini)
- Real image analysis (GPT-4o Vision)
- Real PDF processing (Claude)
- Cost tracking accuracy

### 6.4 Performance Tests
- Large file handling (up to 2GB)
- Multiple attachments (10+)
- Concurrent requests
- Memory usage profiling

---

## 7. Migration & Deployment

### 7.1 Backward Compatibility
- ✅ All existing text-only calls work unchanged
- ✅ No changes to existing tool parameters
- ✅ Optional attachments parameter
- ✅ Existing response format preserved (when no attachments)

### 7.2 Deployment Strategy
- **Blue/Green Deployment:** Build new version in fiedler-blue
- **Testing:** Comprehensive testing before switching
- **Rollback:** Keep current version running until verified
- **Documentation:** Update all docs before switching

### 7.3 Database Migration
- **Schema updates:** Add columns to existing tables
- **Backward compatible:** New columns are nullable
- **Data migration:** No existing data needs updating
- **Testing:** Verify queries work with new schema

---

## 8. Success Criteria

### 8.1 Functional Success
- [ ] All attachment types (base64, path, url) work
- [ ] All supported mime types detected correctly
- [ ] Provider-specific validation works
- [ ] Errors are clear and actionable
- [ ] Metadata tracking is complete

### 8.2 Quality Success
- [ ] 100% backward compatibility (all existing calls work)
- [ ] 90%+ test coverage
- [ ] < 1s overhead for typical multimodal request
- [ ] Zero security vulnerabilities (path traversal, etc.)
- [ ] Complete logging and observability

### 8.3 User Success
- [ ] Audio transcription works (Gemini)
- [ ] Image analysis works (GPT-4o, Gemini)
- [ ] PDF processing works (Claude, Gemini)
- [ ] Documentation is clear and complete
- [ ] Developer experience is smooth

---

## 9. Open Questions

### 9.1 For Triplet Review
1. **Attachment preprocessing:** Should Fiedler auto-convert formats (e.g., HEIC→JPEG)?
2. **Caching:** Should processed attachments be cached to avoid re-processing?
3. **Streaming:** For very large files, implement streaming upload?
4. **Authentication:** Support authenticated URLs (OAuth, API keys)?
5. **Batch processing:** Support multiple files in single request efficiently?
6. **Rate limiting:** Apply separate rate limits for multimodal vs text-only?
7. **Cost estimation:** Provide cost estimates before processing?
8. **Progress tracking:** For long-running processing, provide progress updates?

### 9.2 Future Enhancements
- Real-time streaming audio/video analysis
- Attachment preprocessing and optimization
- Multi-modal output (generate images, audio, etc.)
- Attachment caching and deduplication
- Enhanced security (virus scanning, content filtering)

---

## 10. Appendices

### 10.1 Example Usage

**Example 1: Audio Transcription**
```python
response = fiedler_send(
    prompt="Transcribe this audio and summarize the key points.",
    model="gemini-2.5-pro",
    attachments=[{
        "type": "path",
        "content": "/home/aristotle9/Downloads/Oct 7 at 11-22 AM.m4a"
    }]
)
```

**Example 2: Image Analysis**
```python
response = fiedler_send(
    prompt="What's in this image? Describe in detail.",
    model="gpt-4o",
    attachments=[{
        "type": "url",
        "content": "https://example.com/photo.jpg"
    }]
)
```

**Example 3: PDF + Image**
```python
response = fiedler_send(
    prompt="Compare the diagram in the PDF with this photo. What are the differences?",
    model="gemini-2.5-pro",
    attachments=[
        {
            "type": "path",
            "content": "/mnt/irina_storage/files/docs/architecture.pdf"
        },
        {
            "type": "base64",
            "content": "iVBORw0KGgo...",
            "mime_type": "image/png"
        }
    ]
)
```

### 10.2 Provider API References
- **Gemini:** https://ai.google.dev/gemini-api/docs/vision
- **OpenAI Vision:** https://platform.openai.com/docs/guides/vision
- **OpenAI Whisper:** https://platform.openai.com/docs/guides/speech-to-text
- **Anthropic:** https://docs.anthropic.com/claude/reference/messages
- **xAI:** https://docs.x.ai/api

### 10.3 MIME Type Reference
Standard MIME type registry: https://www.iana.org/assignments/media-types/media-types.xhtml

---

**Document End**

**Next Steps:**
1. Submit to triplets (Gemini 2.5 Pro, GPT-5, Grok-4) for review
2. Aggregate feedback
3. Synthesize final requirements
4. User approval
5. Implementation planning
