REFINE

Core Conclusion
LLM-native development replaces human-centric abstractions with code as the single source of truth and defaults to a Cellular Monolith: a monolithic-first, modular in‑process core with a hardened DMZ gateway and sandboxed periphery. Systems evolve primarily via governed regeneration, and distribution is a deliberate, trigger-based decision driven by measurable needs, not a default.

Key Consensus Points
1) Everything-as-Code
- Design, testing, deployment, and operations are expressed as literate code (embedded rationale/diagrams as code) and executable scripts/tests.
2) Cellular Monolith by Default
- Start with modular classes and an in‑memory bus; expose a single boundary (DMZ/MCP gateway). Sandbox high-risk capabilities (e.g., web, file, untrusted tools).
3) Governed Regeneration
- Prefer regenerating from updated requirements to avoid technical debt; permit small patches for minor fixes. Govern with pinned model versions, semantic diffs, token/cost budgets, and mandatory end‑to‑end tests as gates.
4) Trigger‑Based Distribution
- Distribute only when explicit thresholds are met, e.g., untrusted or multi‑tenant code, polyglot/runtime needs, sustained resource/SLO pressure (e.g., CPU > ~75% or p95 latency misses), concurrent users ≈100–150+, or code/context exceeding model windows (~≥2MB, model‑dependent).
5) Security by Design
- Single DMZ ingress, capability/RBAC for tools, encrypted storage, audit logging, and minimal external surfaces; in‑process communication avoids unnecessary network attack surface.

Unified Recommendations
- Adopt the Cellular Monolith blueprint: single-repo modular codebase, in‑memory bus, one hardened DMZ/MCP gateway, and sandboxed periphery (e.g., WASM/gVisor).
- Implement a GenOps toolchain: automated regeneration with model pinning, semantic diffing, cost/token budgeting, and E2E test orchestration integrated into CI/CD (deploy/test as code).
- Design pluggable boundaries: abstract transport so the in‑memory bus can be promoted to Redis/NATS and modules can be lifted to processes/containers without logic changes.
- Instrument for decisions: track users, CPU/memory, latency SLOs, and code/context size; act on thresholds to introduce distribution selectively.

When to Apply
- Monolithic: Trusted environments; single‑language (e.g., Python); I/O‑bound LLM workloads; codebases within model context (≈500KB–2MB, model‑dependent); ≤~150 concurrent users; no strict regulatory isolation.
- Distributed: Untrusted or multi‑tenant code; polyglot stacks; sustained high load or SLO breaches; geographic/regulatory isolation; or code/context beyond available model windows.

This summary reflects the collective consensus and resolves prior wording/threshold differences while preserving shared conclusions.