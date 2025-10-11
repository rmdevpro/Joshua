Round 3 – Collective Synthesis and Convergence Report

1) What we all agree on now (strong consensus)
- Everything-as-code: Replace prose design/testing/deploy docs with executable artifacts. Keep “why” as lightweight, in-repo ADRs embedded in code/comments.
- Monolith-first for labs: For small, trusted, I/O-bound systems (single language, ≤100 concurrent users), a modular monolith is the right default. Logical boundaries via modules/classes; no premature distribution.
- Hybrid inevitability: Maintain escape hatches. Use a transport-agnostic message bus (in-memory now; Redis/NATS later) and optional microprocess/WASM isolation for risky tasks. Extract components only when triggers are met.
- Tests as the contract: End-to-end tests are primary evidence of correctness, augmented with contract/property tests for critical paths. Test strategy lives with test code (docstrings).
- DMZ boundary: Expose a single hardened entry (web/MCP gateway), keep the ecosystem internal. Simpler attack surface and encryption story.
- Reproducibility and provenance matter: If not using containers, adopt hermetic builds (UV/Nix), strict pinning, SBOMs, signed artifacts, model/prompt version pinning, and change provenance.
- Observability inside the monolith: Per-MAD logs/metrics/traces/costs (namespacing, correlation IDs, OpenTelemetry) are required despite single-process deployment.
- Distribution triggers exist: Untrusted code/content, high/variable concurrency, CPU/GPU hotspots, polyglot needs, regulatory isolation, geographic distribution, or codebase/context exceeding LLM limits.

2) Where we disagreed and our Round 3 decisions
- Containers vs no containers:
  Decision: Do not require Docker for lab monoliths. Require hermetic, reproducible builds (UV/Nix), SBOM, and signed releases. Offer a thin container variant for parity/supply-chain hygiene or when isolation is mandated.
- Regeneration vs incremental patching:
  Decision: Use a hybrid policy. Regenerate for major feature/risky refactors/interface shifts; patch for small fixes. Always pin model versions/temps/seeds, archive prompts/inputs/outputs, and run semantic diffs and full test suites. Enforce cost budgets with model fallback ladders; fall back to patching when a regeneration exceeds budget or fails validation.
- Security isolation inside a monolith:
  Decision: Enforce capability-based, per-MAD in-process RBAC/quotas at the MCP gateway and tool layer. Sandbox high-risk activities (web scraping, file parsing, untrusted plugins) in microprocesses or WASM. Keep DMZ hardened and apply PII redaction/DLP controls on inputs/outputs.
- Human-in-the-loop:
  Decision: Keep humans in the loop for governance checkpoints (architecture diffs, migrations, compliance), with LLMs generating machine- and human-readable change summaries to minimize review burden.
- V5 definition:
  Decision: Redefine V5 as Distribution- and Governance-ready: isolation primitives, transport-pluggable bus, per-MAD SLOs, audit/compliance artifacts, provenance, cost governance, and inter-ecosystem API/versioning.

3) Unified recommendations the collective stands behind
A) Reference architecture blueprint (lab default)
- Modular monolith in Python.
- MessageBus interface with InMemoryBus; ship stubs for Redis/NATS to swap without business-logic changes.
- Single MCP gateway exposing namespaced tools (mads.<name>.<tool>) with per-namespace RBAC, quotas, and rate limits.
- In-process SecretsManager with encrypted-at-rest store, audited access, JIT decryption.
- Core/periphery isolation: keep persistent MADs (e.g., Rogers, Fiedler, Turing, Grace) in-process; run risky/heavy tasks (e.g., Marco browsing) as sandboxes (WASM/subprocess/container) via a narrow, hardened RPC.
- Observability: OpenTelemetry traces across MAD boundaries, per-MAD metrics (latency, error rate, token/cost), structured logs with correlation IDs, error budgets and circuit breakers per MAD.
- Security and policy: DMZ input sanitization, PII redaction, outbound DLP, SSRF/XXE defenses, secrets rotation, and audited tool invocations.

B) Decision gates: monolith vs distribute
Remain monolithic if ALL are true:
- Trusted environment, no untrusted code execution.
- Single language (Python) and I/O-bound workloads.
- ≤100 concurrent users and codebase fits comfortably in a primary model’s context + RAG index (≤~1M tokens effective).
- No strict regulatory isolation or data residency constraints.
Distribute (or adopt hybrid) if ANY sustained condition holds:
- Untrusted code/content or multi-tenant isolation requirements.
- Persistent SLO violations: p95 latency misses, sustained queue backlogs, CPU >70% or memory >75% for >15 minutes per MAD, or need independent scaling.
- Polyglot/hardware hotspots (GPU/CPU), heavy native deps best run out-of-proc.
- Regulatory/geographic isolation or data residency mandates.
- Codebase/context window breach; or divergent deployment cadences per MAD.

C) Regeneration governance
- Determinism: Pin model versions, temperature, seeds; archive prompts/inputs/outputs; sign releases; track SBOMs.
- Verification: Run full test suites; generate semantic diffs for logic/ABI/architectural drift; cross-LLM or ensemble validation for high-risk changes.
- Economics: Set per-cycle token/cost budgets; use model fallback ladders (cheap→fast→best); cache reusable subsystems; regenerate selectively.
- ADR registry: Store rationale/constraints as machine-readable ADRs (YAML/JSON). Auto-render Architecture.md and change summaries on each regeneration.

D) Data/state management policy
- Decouple state from code. Any schema change requires versioned, reversible migrations with dry runs in an ephemeral sandbox and contract tests over data schemas.
- Backups and restore rehearsals are mandatory. Track data retention/classification policies.
- For inter-ecosystem interfaces, enforce versioned API contracts and backward compatibility with contract tests.

E) Compliance, safety, and provenance
- Produce audit packs per release: ADRs, SBOM, signed artifacts, test evidence, migration plans, model/prompt provenance.
- Enforce centralized PII and policy controls at DMZ and tool invocation boundaries.
- License scanning and attribution for generated/ingested code and assets.

F) Immediate next steps (2–4 weeks)
- Build the modular monolith reference (Rogers, Fiedler, Turing, Grace) with asyncio bus, MCP gateway, secrets, and E2E + contract/property tests.
- Implement hermetic builds (UV or Nix), SBOM, signing; optionally ship a thin container profile.
- Add observability and cost meters; inject faults for resilience testing; benchmark vs the current containerized baseline.
- Stand up regeneration toolchain: model pinning, semantic diffing, ADR registry, change summaries, and budget checks.
- Ship Redis/NATS bus adapters and 1–2 sandboxed “periphery” tasks to validate hybrid extraction.

4) Convergence status
CONVERGING – 4 issues remain
- Regeneration economy: Standardizing cost/benefit thresholds and cadence (when to regenerate vs patch), with quantitative guidance and caching strategies.
- Data evolution toolkit: A reference framework for reversible migrations, data contract tests, and sandboxed dry runs across common datastores.
- Monolith observability pack: A ready-to-use per-MAD telemetry/cost toolkit and “flight recorder” for postmortems, standardized across projects.
- Compliance profiles: Canonical mappings (e.g., GDPR/HIPAA/PCI) to the governance artifacts and controls recommended here.

Final position before limits
We adopt a monolith-first, hybrid-ready, everything-as-code paradigm with strong governance, observability, and isolation-by-design. Containers become optional rather than default; hermetic builds and policy controls are mandatory. Regeneration is a powerful tool, used judiciously under pinned, auditable conditions, with tests-as-spec and semantic diffs as the final arbiter. Clear decision gates dictate when to scale out. This is the unified path the collective can stand behind for LLM-native software in labs and beyond.