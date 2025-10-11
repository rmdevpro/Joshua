REFINE

Core Conclusion
LLM-native development treats code as the single source of truth and defaults to a Cellular Monolith: a modular, in-process architecture with a hardened DMZ gateway and sandboxed peripheries for high-risk tasks. Design, testing, deployment, and operations move from prose to executable, literate code. Distribution becomes a deliberate, trigger-based choice. Major evolution is achieved via governed regeneration; minor changes use incremental patches gated by end-to-end tests.

Key Consensus Points
- Everything as Code: Replace design docs, test plans, and runbooks with a literate codebase (embedded rationale/diagrams-as-code) plus executable tests, deployment, and ops scripts.
- Cellular Monolith by Default: Use modular classes and an in-memory bus for simplicity and speed; expose a single gateway; sandbox high-risk capabilities (e.g., web/file/network) using isolation tech (e.g., WASM/gVisor).
- Governed Regeneration: Prefer regenerating from updated requirements to avoid technical debt, using pinned model versions, semantic diff validation, reproducible builds, token/cost budgets, and comprehensive end-to-end tests; allow incremental patches for minor fixes.
- Trigger-Based Distribution: Move to processes/containers or external transports only on explicit, measured triggers (e.g., untrusted code or multi-tenant needs, polyglot/runtime specialization, sustained SLO breaches or resource saturation, or code/context approaching model window limits).
- Security and Operations Simplified: DMZ-only ingress, capability/RBAC for tools, encrypted storage, audit logging, and HA via process supervision/replication; internal calls stay in-process to minimize attack surface and overhead.
- Pluggable Boundaries: Abstract messaging and I/O so teams can switch from in-memory to Redis/NATS and extract modules to processes/containers without logic changes.

Unified Recommendations
- Start with a single modular codebase (e.g., Python), in-memory messaging, one gateway, and sandboxed peripheries; keep rationale and diagrams (Mermaid) alongside code.
- Implement a GenOps toolchain: model pinning, semantic diffing, cost/token budgeting, deterministic builds, and mandatory end-to-end test suites integrated into CI/CD (deploy/test/runbooks as code).
- Instrument for distribution triggers (users, CPU/memory, latency SLOs, context size) and define promotion playbooks that swap transports or extract modules with minimal churn.

When to Apply
- Monolithic: Trusted environments; single-language, I/O-bound/LLM-centric workloads; modest concurrency (roughly up to 100–150 users); code/context within model windows (~0.5–2MB, model-dependent); no strict regulatory/geographic isolation.
- Distributed: Untrusted or multi-tenant execution; polyglot or specialized runtimes; sustained SLO/resource breaches; regulatory/geographic isolation; or code/context beyond available model windows.