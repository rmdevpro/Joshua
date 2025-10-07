Recommendation summary
- Primary: Add an application-layer Anthropic Gateway (thin reverse proxy) that mirrors the Anthropic API surface, forwards requests to api.anthropic.com, and logs sanitized request/response pairs to Dewey/Winni. Point Claude Code to this gateway using ANTHROPIC_API_URL if supported. This avoids TLS interception and minimizes security risk while keeping complexity low.
- Fallback: If Claude Code cannot change its base URL, run an explicit HTTPS forward proxy (mitmproxy-based) and configure HTTPS_PROXY/HTTP_PROXY env vars. Install the proxy CA into the Claude Code runtime trust store. Use a mitmproxy addon that redacts credentials and streams logs to Dewey.
- Last resort: Network capture is not recommended (complex, brittle, harder to sanitize and correlate).

Why this fits ICCM
- Preserves the “KGB as central egress/logging” pattern while adding HTTP(S) capability alongside the existing WebSocket spy.
- Keeps the Dewey/Winni storage model intact: the new gateway/proxy just emits events in the same Dewey ingestion flow used today.
- Works on bare metal and in containers by toggling a known environment variable or proxy variables.
- Minimizes credential exposure by redacting at the proxy/gateway boundary and never persisting API keys.

Architecture (ASCII)
Legend: [component], --> normal traffic, ==>> logging event

Preferred (Anthropic Gateway) when Claude Code supports ANTHROPIC_API_URL

User
  |
Claude Code (CLI/container)
  |  HTTPS to base_url = http(s)://kgb-gateway[:port]/v1
  v
[KGB-HTTP Anthropic Gateway]
  |  HTTPS to api.anthropic.com
  v
Anthropic API (cloud)

[KGB-HTTP Anthropic Gateway] ==>> [Dewey] ==>> [Winni (Postgres)]

Alternative (HTTPS forward proxy) when base URL cannot be changed

User
  |
Claude Code (CLI/container) -- HTTPS via HTTPS_PROXY/HTTP_PROXY -->
  v
[KGB-HTTP MITM Proxy (mitmproxy + addon)]
  |  HTTPS to api.anthropic.com
  v
Anthropic API (cloud)

[KGB-HTTP MITM Proxy] ==>> [Dewey] ==>> [Winni (Postgres)]

Integration with existing ICCM components
- KGB: Add an HTTP(S) capability next to the existing WebSocket spy. You can package it as:
  - KGB-HTTP-Gateway (preferred) or
  - KGB-HTTP-Proxy (mitmproxy-based fallback).
  Both publish sanitized events to Dewey using the same transport Dewey already accepts from KGB (HTTP ingest or the existing internal RPC if available).
- Dewey: Add/confirm a generic ingest endpoint/schema for “anthropic_api” events:
  - Common fields: ts_start, ts_end, host/container, client_app=claude-code, direction=request/response, duration_ms.
  - Request: method, path, query, headers_sanitized, body (bounded/truncated).
  - Response: status, headers_sanitized, body (bounded/truncated), stream_info (if SSE).
  - Correlation: request_id (proxy-generated UUID), upstream x-request-id, and optional session tags.
- Winni: No change; Dewey continues to store in Postgres.

Detailed implementation steps

Phase 0 – Capability probe (1 hour)
1) Check if Claude Code honors ANTHROPIC_API_URL:
   - Launch claude-code with ANTHROPIC_API_URL=http://127.0.0.1:8089/v1 and ANTHROPIC_API_KEY set.
   - If it works, choose the Gateway approach.
   - If not, verify HTTPS_PROXY/HTTP_PROXY support: set HTTPS_PROXY=http://127.0.0.1:8080 and test a request; if it routes through a local proxy, choose the mitmproxy approach.

Phase 1A – Anthropic Gateway (preferred)
1) Build a minimal reverse proxy (Go/Node/Python) that:
   - Accepts requests under /v1/* and forwards 1:1 to https://api.anthropic.com/v1/*.
   - Copies all headers except it never logs or forwards Proxy-Authorization.
   - Injects ANTHROPIC_API_KEY from its own environment (optional) or passes through from client; do not log the key.
   - Supports streaming responses (SSE) and non-streaming; passes through chunked transfer.
2) Logging in the gateway:
   - Sanitize headers: drop x-api-key, authorization, cookie; mask other sensitive headers.
   - For body: log JSON fields with size limits; truncate large text (e.g., 128 KB per field) to protect DB and privacy.
   - Aggregate SSE streams server-side to reconstruct final messages for storage while retaining raw chunks if needed; mark stream boundaries and durations.
   - Attach correlation:
     - request_uuid (new UUIDv4),
     - upstream x-request-id if present,
     - client_app=claude-code,
     - container_id/hostname,
     - optional iccm_session_id tag from an env var or query param if provided.
3) Emit to Dewey:
   - POST to Dewey’s ingest endpoint (e.g., http://dewey:7000/ingest) with event type=anthropic_api.
   - Use the same authentication Dewey expects from KGB (token or mTLS).
4) Security:
   - Never persist API keys or CA private keys in logs.
   - Gate the gateway with network policy (only ICCM network) and optional mTLS from Claude Code container.
   - Rate-limit and set timeouts to avoid becoming a bottleneck (connect/read/write timeouts, retries).
5) Packaging:
   - Dockerfile for kgb-http-gateway; embed config via env vars (UPSTREAM=https://api.anthropic.com, DEWEY_URL, MAX_BODY_LOG_BYTES, REDACTION_RULES).
   - Docker Compose: place claude-code and kgb-http-gateway on the same network. Set ANTHROPIC_API_URL=http://kgb-http-gateway:8089/v1 in claude-code environment.
   - Bare metal: run gateway on localhost:8089 and export ANTHROPIC_API_URL=http://127.0.0.1:8089/v1 before launching claude-code.

Phase 1B – HTTPS forward proxy (fallback)
1) Run mitmproxy in transparent or forward mode; forward mode is simpler:
   - Start mitmdump with an addon anthro_logger.py.
   - Ensure large streaming bodies are supported: set stream_large_bodies=10m.
2) Trust chain:
   - Generate/install mitmproxy CA on host and in the Claude Code container image:
     - Copy mitmproxy-ca-cert.pem into /usr/local/share/ca-certificates/mitmproxy.crt; run update-ca-certificates (Debian/Ubuntu) or trust anchors (Alpine).
     - For bare metal macOS/Windows, install into OS trust store.
3) Configure Claude Code:
   - Set HTTPS_PROXY=http://kgb-http-proxy:8080 and NO_PROXY=localhost,127.0.0.1.
4) Addon logic (anthro_logger.py):
   - Filter only flows to api.anthropic.com.
   - On request:
     - Capture method, URL, query, headers (drop x-api-key, authorization, cookie), and body (truncate).
   - On response:
     - Handle streaming: buffer SSE “data:” lines; store both raw and assembled logical messages (bounded).
     - Record status, headers (sanitized), duration.
   - Post sanitized event JSON to Dewey.
   - Do not forward Proxy-Authorization upstream; redact before logging.
5) Hardening:
   - Bind proxy to internal interface only.
   - Protect mitmproxy CA private key; rotate periodically; do not store in the repo.
   - Health checks and circuit breaker to avoid blocking Claude Code if Dewey is down (queue to disk with size cap, drop oldest policy).

Phase 2 – Dewey integration
1) Define/extend the Dewey schema for anthropic_api:
   - conversation_key: nullable; can be backfilled by correlation logic (see below).
   - request: method, path, query, headers_sanitized, body_preview, size_bytes.
   - response: status, headers_sanitized, body_preview, size_bytes, sse_chunk_count.
   - timings: ts_start, ts_first_byte, ts_end, duration_ms.
   - meta: client_app, host/container, iccm_session_id (optional), upstream_x_request_id, proxy_request_uuid.
2) Ingest endpoint:
   - Add POST /ingest/anthropic_api with auth and schema validation.
   - Back-pressure strategy if DB slow (async queue, bounded channel, retries with jitter).
3) Linkage with existing MCP logs:
   - Correlate by:
     - time window overlap,
     - container/host id,
     - process labels or compose service name,
     - optionally a generated iccm_session_id env var shared by both Claude Code and gateway/proxy at container start and stamped into logs (recommended).
   - Dewey can run a periodic join to attach anthropic_api records to the nearest MCP session by host + time proximity + iccm_session_id when available.

Phase 3 – Operational playbook
- Health: expose /healthz on gateway/proxy; add Compose/Swarm/K8s liveness/readiness.
- Observability: Prometheus metrics (requests_total by upstream, errors_total, queue_depth, dropped_logs_total, log_bytes_total).
- Privacy: configurable redaction rules (regex and header allowlist). Optionally encrypt stored request/response bodies at rest via DB column-level encryption.
- Failure modes:
  - Dewey down: buffer locally to a bounded file queue; drop oldest beyond cap with a visible metric.
  - Proxy/gateway down: allow operator to bypass by unsetting ANTHROPIC_API_URL or HTTPS_PROXY; document a “break-glass” env var.

Security and reliability considerations
- Credential leakage:
  - Strip or mask x-api-key, authorization, cookie, set-cookie before storing.
  - Do not mirror secrets into logs via query strings; consider stripping known sensitive JSON fields (api_key, token, secret, password) with a redaction map and regex.
- TLS:
  - Gateway mode avoids TLS interception entirely; best for security and compliance.
  - MITM mode requires CA trust; keep CA private key in a secrets manager; rotate regularly; scope the proxy to internal network only.
- Data minimization:
  - Truncate prompt/response bodies to sane limits; consider opt-in full capture per session for audits.
  - Support opt-out labels to skip logging sensitive workspaces.
- Reliability:
  - Set upstream timeouts and retries with idempotency awareness (don’t repeat POSTs without a retry-safe strategy unless Claude Code/Anthropic supports idempotency keys).
  - Use streaming passthrough with low memory footprint (chunked copy).

Concrete deliverables/checklist
- Repo: kgb-http-gateway
  - Reverse proxy implementation with SSE passthrough
  - Redaction and truncation middleware
  - Dewey emitter client
  - Dockerfile and docker-compose.yaml (adds service next to existing KGB)
  - Helm chart or Compose for containerized deployment
- Repo: kgb-http-proxy
  - mitmproxy addon anthro_logger.py
  - Dockerfile (mitmproxy base), CA management notes, Compose file
- Dewey
  - /ingest/anthropic_api endpoint + schema + migrations for Winni
  - Correlation job linking anthropic_api records with MCP sessions
- Ops docs
  - How to enable in bare metal and containers
  - CA install steps (fallback path)
  - Break-glass bypass steps

Possible simpler approach to evaluate
- Built-in Claude Code debug logs: If Claude Code has a verbose/trace flag that prints request/response JSON, you could tail and ship those logs to Dewey (sidecar filebeat/vector). This is the least invasive but depends on the CLI exposing complete and structured logs, and you must ensure no API keys are printed. If available, it can be a low-effort Phase 0.5; otherwise, proceed with the gateway/proxy plan.

Summary decision matrix
- If Claude Code supports ANTHROPIC_API_URL: choose Anthropic Gateway (simplest, most secure, easiest to maintain).
- If not, but supports HTTPS_PROXY: choose mitmproxy-based KGB-HTTP-Proxy with strict redaction and CA management.
- Avoid tcpdump/pcap parsing due to complexity and sanitization difficulty unless used for one-off diagnostics.

This plan satisfies:
- Full conversation capture (requests and streamed responses)
- Storage in Winni via Dewey
- Works bare metal and containerized
- Protects credentials and sensitive data
- Keeps complexity low by reusing proxy/gateway patterns consistent with existing KGB/Dewey design.