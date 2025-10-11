REFINE

Core Conclusion
LLM-native development replaces human-centric abstractions with code as the single source of truth. The consensus architecture is Monolithic-First Cellular: a modular, in-process core with embedded rationale and executable operations, plus sandboxed peripheries for high-risk tasks. Evolution favors governed regeneration, and distribution is a deliberate, trigger-based choice rather than the default.

Key Consensus Points
- Everything as Code: Design rationale, diagrams (as code), tests, deployment, and runbooks live in a literate codebase with executable artifacts; prose plans are unnecessary.
- Monolithic-First Cellular Architecture: Start with a single-process system using modular classes and an in-memory bus; isolate high-risk capabilities (e.g., web/file/network access) via sandboxes while keeping the core simple.
- Governed Regeneration: Prefer regenerating from updated requirements to avoid technical debt; use pinned model versions, semantic diff validation, reproducible builds, cost/token budgets, and end-to-end tests. Allow incremental patches for minor fixes.
- Trigger-Based Distribution: Distribute only on explicit thresholds, such as untrusted or multi-tenant code, polyglot/runtime specialization, sustained resource saturation (e.g., CPU >75% under load), concurrent users beyond small-team needs (e.g., >150), regulatory/geographic isolation, or code/context approaching model limits (e.g., >2MB).
- Security by Design: Enforce a single hardened DMZ gateway as the sole ingress; apply capability/RBAC controls, encrypted storage, audit logging, and keep internal calls in-process to minimize attack surface and overhead.

Unified Recommendations
- Adopt the Cellular Monolith blueprint: one modular codebase, in-memory messaging, a single gateway, and sandboxed high-risk peripheries; keep rationale and diagrams co-located with code.
- Implement a “GenOps” toolchain: model pinning, semantic diffing, deterministic builds, token/cost budgeting, and mandatory end-to-end tests integrated into CI/CD; deployment/testing/ops as code.
- Design pluggable boundaries: abstract messaging and I/O so you can swap in-memory for Redis/NATS and extract modules to processes/containers without logic changes.
- Instrument triggers and define promotion playbooks: monitor users, SLOs, CPU/memory, and context size; migrate components or transports only when thresholds are met.

When to Apply
- Monolithic: Trusted environments; single-language, I/O-bound/LLM-centric workloads; modest concurrency (roughly up to 100–150 users); code/context within current model windows (typically ≤500KB–2MB); no strict regulatory/geographic isolation.
- Distributed: Untrusted or multi-tenant execution; polyglot or specialized runtimes; sustained SLO/resource breaches; regulatory/geographic isolation; or code/context exceeding available model windows.