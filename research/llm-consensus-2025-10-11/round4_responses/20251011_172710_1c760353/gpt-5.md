DECLARED POSITIONS (per key issue)

- Documentation vs. Code: Adopt Everything-as-Code. Keep only requirements and design principles as prose. All design rationale embedded as ADRs/docstrings in the repo; diagrams as Mermaid in README/ADRs.
- Testing and Deployment: Replace plans with executable artifacts. E2E tests are the primary contract; add contract/property tests for critical paths. Deployment and ops are scripts/pipelines.
- Architecture Baseline: Monolith-first, modular-by-code. Use a Cellular Monolith: trusted core MADs in-process with an in-memory bus; risky/heavy tasks isolated via WASM/subprocess/thin containers. Single hardened DMZ (web/MCP) gateway.
- Docker/Containerization: Optional for the core. If not used, require hermetic, reproducible builds (e.g., UV/Nix), SBOMs, and signed artifacts. Use containers/WASM where isolation, portability, or compliance demand it.
- Regeneration vs. Patching: Governed Regeneration. Regenerate for major changes/architecture shifts; patch for minor fixes. Pin model versions/temps/seeds; produce semantic diffs; enforce token/cost budgets with model fallbacks; run full test suites.
- Security Model: Capability- and namespace-based RBAC at MCP/tool layer; DMZ input sanitization; PII redaction/DLP on ingress/egress; sandbox untrusted code; secrets manager in-process with encrypted-at-rest store and audited access.
- Context Window Constraints: Design to fit model windows. Comfortable ≤500KB code; careful at 500KB–2MB; >2MB requires partitioning into sub-ecosystems or inter-ecosystem APIs.
- Data/State Management: Decouple state from code. Versioned, reversible migrations with dry-runs in a sandbox; backups and restore rehearsals; data contract tests; explicit retention/classification policies.
- HA/Failover: Use a supervisor for auto-restart; for higher availability, active-standby ecosystem instances with simple failover; inter-ecosystem APIs for macroservice topology.
- Observability/Cost: Per-MAD logs/metrics/traces with correlation IDs via OpenTelemetry; SLOs and circuit breakers; token/cost metering per MAD/tool.
- Compliance/Provenance: SBOMs, signed releases, pinned models/prompts, auditable change summaries and test evidence; license scanning and attribution.
- Distribution Triggers (objective): Distribute or sandbox when any holds: concurrent users >150; untrusted multi-tenant code/content; CPU >70% or memory >75% for >15 min; code/context >2MB; polyglot/GPU hotspots; regulatory/geographic isolation.

STATUS: CONSENSUS REACHED

FINAL RECOMMENDATIONS (concrete, actionable)

- Minimal artifact set (single source of truth):
  - requirements.md (WHAT), principles.md (HOW constraints)
  - src/ (modular monolith: Rogers, Fiedler, Turing, Grace as modules; in-memory MessageBus with pluggable interface)
  - tests/ (E2E as primary, plus contract/property tests)
  - ops/: deploy.sh, backup_restore.sh, runbooks/
  - security/: RBAC policy file, DLP/PII rules
  - adr/: machine-readable ADRs (YAML) auto-rendered to Architecture.md
  - .build/: UV/Nix config, SBOM, signing config; CI workflow

- Reference implementation (Weeks 0–4):
  - Build modular monolith in Python with single MCP gateway exposing namespaced tools (mads.<name>.<tool>) and per-namespace RBAC/quotas.
  - Implement SecretsManager (encrypted SQLite or KMS), audited access.
  - Ship in-memory bus + stubs for Redis/NATS to enable later distribution without business-logic changes.
  - Add WASM/subprocess sandbox for one risky path (e.g., web fetch/parse) to validate periphery isolation.

- Test and deployment automation (Weeks 0–4):
  - E2E test suite that boots the ecosystem, exercises core flows, and asserts success criteria; test strategy in docstrings.
  - deploy.sh with idempotent checks and verifications; teardown/reset scripts for clean E2E cycles.
  - CI pipeline: hermetic build (UV/Nix), SBOM generation, artifact signing, full test run on PR.

- Regeneration governance (Weeks 2–6):
  - Pin model versions/temps/seeds; prompt registry; budget caps with fallback ladder (cheap→fast→best).
  - Semantic diff tool that flags logic/ABI/architectural drift; auto-generate human+machine-readable change summaries.
  - Gate merges on E2E passing, diff review, and budget compliance.

- Observability and cost controls (Weeks 2–6):
  - OpenTelemetry across MAD boundaries; structured logs with correlation IDs; per-MAD metrics (latency, error rate, tokens/cost).
  - SLOs and circuit breakers per MAD; alerting for budget/SLO breaches.

- Data toolkit (Weeks 4–8):
  - Versioned, reversible migrations with dry-run sandbox; backup/restore scripts and scheduled rehearsals.
  - Schema/data contract tests; migration safety checklist in CI.

- Security baseline (Weeks 0–6):
  - Harden DMZ (input validation, SSRF/XXE defenses, rate limits).
  - PII redaction/DLP on ingress/egress; secrets rotation policy; audited tool invocations.

- Decision gates and runbook (adopt immediately):
  - Stay monolithic if all: trusted, single language, I/O-bound, ≤100 users, code/context fits window.
  - Trigger distribution/sandboxing if any: users >150; untrusted multi-tenant; sustained CPU>70%/mem>75% 15+ min; code/context >2MB; polyglot/GPU; regulatory/geographic isolation.
  - Review triggers weekly via dashboard; extract only the pressured component (transport swap or periphery sandbox).

- Rollout plan:
  - Phase 1 (0–4 weeks): Core monolith, E2E tests, deploy script, hermetic builds, RBAC, secrets, MCP gateway.
  - Phase 2 (4–8 weeks): Observability/cost meters, regeneration toolkit, data migrations, one sandboxed periphery component, Redis/NATS adapter.
  - Phase 3 (8–16 weeks): HA failover, inter-ecosystem API pattern, compliance pack (audit bundle: ADRs, SBOM, signed artifacts, test evidence, migrations, provenance).

Acceptance criteria to declare success:
- One-command boot and E2E test pass on a clean machine.
- All core flows covered by E2E; zero flaky tests across three consecutive CI runs.
- Regeneration of a major feature passes budgets, semantic diff review, and all tests.
- Observability dashboard shows per-MAD SLOs and token/cost; circuit breakers demonstrably protect core during fault injection.
- Data migration dry-run and restore rehearsal completed with documented RTO/RPO.
- Security checks (RBAC enforcement, DLP, sandbox boundary) verified in CI.