--- 00_IAE_Intelligent_Agentic_Engineering_v1.1.txt ---
Paper 00: Intelligent Agentic Engineering (IAE) - Master Document
Version: 1.1
Date: 2025-10-06
Status: DRAFT - Council of Elders Synthesis (v1.1)
Repository: Joshua (IAE)
Note: IAE is the overarching discipline; MAD is the architecture pattern within IAE
Synthesized by: Council of Elders (Gemini 2.5 Pro, GPT-5, Claude Opus 4)

Changelog
- v1.1 (2025-10-06): Quaternary structure normalized (ICCM + IDE + IEE + IAE). LLM Orchestra naming corrected: LLM Conductor is the Half-MAD; “Fiedler” removed. Thinking Engine defined as four components (CET + Rules Engine + DER + State Manager). Added full State Manager specification (tripartite model, APIs, versioning). Published canonical contracts v1 (Structured Context, Rule Engine Output, Decision Package, Execution Outcome Package, Reasoning Trace). Added conversation protocols (MAD-to-MAD messaging, capability discovery/registration, error handling, versioning). Elevated operational feedback loop.
- v1.0 (2025-10-06): Initial master document framing IAE as overarching discipline, positioning MAD pattern, and defining component boundaries.

Executive Summary
Intelligent Agentic Engineering (IAE) is the overarching discipline for designing, assembling, and operating intelligent agents built on the MAD (Multipurpose Agentic Duo) architecture pattern. MAD agents separate cognition from action:

- Thinking Engine: CET (ICCM), Rules Engine (IDE), DER (IDE), State Manager (IAE)
- Doing Engine: Domain-specific execution (IEE)

IAE integrates four disciplines (quaternary): ICCM (context), IDE (decisions), IEE (execution), IAE (assembly and state). LLM Conductor is an external Half-MAD that provides the LLM Orchestra capability via conversations to any MAD; it is not part of the Thinking Engine.

Core tenets
- Separation of concerns: model-agnostic thinking, domain-specific doing
- Contracts first: canonical schemas enable independent evolution
- Conversations over calls: MAD-to-MAD interactions are dialogic and versioned
- State as the spine: IAE-owned State Manager provides world model, task context, and execution state to all disciplines
- Feedback loop: decisions → execution → outcomes → state update → improved context → improved decisions

1. Introduction: What IAE Is and Does
- IAE is the discipline of agent assembly. It produces Full MADs by integrating CET (ICCM), Rules Engine and DER (IDE), State Manager (IAE), and Doing Engines (IEE).
- MAD is the architecture pattern produced within IAE. It is not a separate discipline.
- Half-MADs provide reusable capabilities to all MADs via conversations. Examples:
  - LLM Conductor: LLM Orchestra capability (multi-model consultative reasoning)
  - Dewey: Conversation retrieval (immutable archives)
  - Godot: Conversation management (active sessions)
  - Marco: Session orchestration and budgeting
  - Horace: File and artifact catalog with provenance
  - Gates: Document generation with style/compliance
  - Playfair: Diagram and visualization generation

2. Theoretical Foundation
2.1 Two-system framing
- Thinking Engine (deliberative, auditable, model-agnostic)
- Doing Engine (fast, sandboxed, tool- and API-centric)

2.2 Thinking Engine composition (four components)
- CET (ICCM): transformation-only context engineering
- Rules Engine (IDE): deterministic policy, safety, and known regimes
- DER (IDE): synthesis under uncertainty, multi-objective arbitration
- State Manager (IAE): authoritative memory and world model
Note: LLM Orchestra is provided externally by the LLM Conductor Half-MAD and consulted via conversations initiated by DER (or other MAD components when appropriate).

2.3 Doing Engine philosophy (IEE)
- Domain-specific execution through tools and APIs
- Safety validation, monitoring, and outcome synthesis
- Reporting outcomes to State Manager and signaling re-engagement when needed

2.4 Operational feedback loop
- Decision → Execution → Outcome → State Update → Context Refresh → Better Decision
- All links are standardized through canonical contracts and State Manager APIs

2.5 Relationship to existing architectures
- Symbolic AI: production rules (Rules Engine)
- Cognitive architectures: explicit memory and deliberation (State Manager + DER)
- Modern LLM agents: consultative multi-model reasoning (LLM Conductor) bounded by deterministic guardrails
- Software architecture: micro-interfaces and versioned contracts

3. Architecture Components and Specifications
3.1 Thinking Engine interfaces and boundary
- IDE consumes Structured Context and produces:
  - Rule Engine Output (Rules Engine)
  - Decision Package (DER) for IEE
- IAE State Manager is read and written by CET, IDE, and IEE via versioned APIs
- IEE consumes Decision Package and produces Execution Outcome Package, persisted via State Manager

3.2 State Manager specification (IAE-owned)
3.2.1 Purpose and scope
- Authoritative memory for all MADs
- Tripartite data model:
  - World Model: long-lived facts, ontologies, environment snapshots
  - Task Context: scoped, evolving task-level state and conversation context
  - Execution State: decision execution lifecycles and telemetry

3.2.2 Global properties
- Versioned and immutable-by-default records; updates create new versions with provenance
- Content-addressable artifacts; signed traces
- Optimistic concurrency with entity tags; idempotent writes by natural keys
- Access control and tenancy: per-agent, per-capability, and per-tenant isolation
- Time-travel reads for audit and replay
- Event emission (state-changed topics) with backpressure-aware delivery

3.2.3 Core APIs (abstract signatures)
- World Model
  - get_world_snapshot(filters, at_version?)
  - get_world_fact(fact_id, at_version?)
  - put_world_fact(fact) → fact_id, world_version_id
  - update_world_fact(fact_id, patch, if_match_etag) → new_world_version_id
  - list_world_versions(range)
  - get_ontology(schema_version)
- Task Context
  - create_task_context(task_id, parent_task_id?, seed_context) → context_id
  - read_task_context(task_id, at_context_version?)
  - update_task_context(task_id, patch, if_match_etag) → new_context_version
  - append_context_event(task_id, event) → event_id
  - link_context_to_world(task_id, world_version_id)
- Execution State
  - start_execution(decision_id, action_name, expected_effects) → execution_id
  - update_execution(execution_id, progress, partial_effects?, logs_ref?)
  - complete_execution(execution_id, status, observed_effects, outcome_ref) → outcome_id
  - read_execution(decision_id or execution_id)
- Cross-cutting
  - persist_decision_package(decision_package) → decision_id
  - persist_execution_outcome(outcome_package) → outcome_id
  - link_reasoning_trace(decision_id, trace_id)
  - get_reasoning_trace(decision_id or trace_id)
  - retention_policy(entity_type) get/set
  - register_schema(schema_uri, schema_version, checksum)

3.2.4 Versioning and provenance
- Every write yields a new version with:
  - version_id (ULID), parent_version_id, timestamp, writer_id, discipline, toolchain versions
- Provenance captured for all derived items with references back to inputs and transformations
- Replay support:
  - construct_decision_context(decision_id) reconstructs the exact inputs used

3.2.5 Security and privacy
- Mutual authentication (mTLS or equivalent) and fine-grained authorization
- At-rest encryption; field-level redaction and tokenization as policy
- Conversation transcript handling rules: redaction policy, retention classes
- Audit logging with tamper-evident hashes

3.3 Canonical Contracts (v1)
All schemas are minimum viable and extensible. Field names are normative; types are indicative.

3.3.1 Structured Context (CET → IDE)
- context_id: string (ULID)
- schema_version: string
- task_id: string
- created_at: timestamp
- ttl: duration or timestamp
- provenance: list of {source, method, timestamp}
- trust_level: enum {low, medium, high}
- health: {completeness: 0–1, freshness: duration, anomalies: list}
- actor_profile: {agent_id, role, tenant}
- entitlements: list of capability scopes
- risk_tier: enum {T0, T1, T2, T3}
- jurisdiction: list of strings
- problem_frame: {objectives, constraints, preferences, utility_proxies}
- features: list of {name, type, value, unit?, tags?, source?, last_updated?}
- environment: {resources, budgets, cost_windows, SLAs}
- safety_profile: {red_lines, rate_limits, exposure_budgets}
- world_refs: {world_version_id}
- prior_decisions: list of decision_id
- context_links: list of prior context_ids

3.3.2 Rule Engine Output (Rules → DER)
- rule_output_id: string
- schema_version: string
- ruleset_version: string
- status: enum {HIGH_CONFIDENCE_MATCH, LOW_CONFIDENCE_MATCH, NO_MATCH}
- matches: list of {
  rule_id, rule_version, action_proposal, certainty: 0–1, priority, mandatory: bool, justification
}
- guardrails_triggered: list of {invariant_id, severity, detail}
- conflicts: list of {rule_ids, rationale, resolution_hint}
- residuals: list of undecided aspects
- coverage: 0–1
- confidence_rule: 0–1
- trace_ref: string
- requested_retransformations: optional list of {feature_gap, suggested_scope}

3.3.3 Decision Package (DER → Doing Engine)
- decision_id: string
- schema_version: string
- task_id: string
- timestamp: timestamp
- decision_type: enum {choose, plan, route, approve, deny}
- selected_action: {
  name, parameters: map, preconditions: list, expected_effects: list,
  dependencies?: list, required_capabilities?: list
}
- safety_assertions: list of invariant_ids with parameterization
- confidence_score: 0–1
- confidence_interpretation: {calibration_method, band, notes}
- risk_tier: enum
- abstain_threshold: 0–1
- human_review_required: bool
- escalation_route: {contact, SLA}
- alternatives: list of {action, expected_utility, confidence, trade_offs}
- reasoning_trace_ref: string
- references: {
  context_id, rule_output_id, world_version_id,
  CET_version, Ruleset_version, DER_version
}
- consultations: list of {provider: “LLM Conductor”, consultation_id, consensus_metrics}
- budgets: {time, cost}
- policy_requirements: list of approvals/checks to enforce

3.3.4 Execution Outcome Package (Doing Engine → State Manager)
- outcome_id: string
- schema_version: string
- decision_id: string
- action_name: string
- start_time: timestamp
- end_time: timestamp
- status: enum {success, failure, partial, aborted}
- execution_state_transitions: list of {time, state, note}
- observed_effects: list
- deviations: list of {expected, observed, severity, remediation}
- safety_validation_results: list of {invariant_id, pass_fail, detail}
- error_diagnostics: {code, message, category, logs_ref?}
- telemetry: {latency_ms, cost, resource_usage, api_quota_used}
- artifacts: list of {artifact_id, kind, uri, checksum}
- outcome_trace_ref: string
- world_version_id_before: string
- world_version_id_after: string
- next_actions_suggested?: list
- reengagement_advice?: {trigger, payload_ref}

3.3.5 Reasoning Trace (audit and replay)
- trace_id: string
- decision_id: string
- schema_version: string
- structure: directed acyclic graph of nodes:
  - context_nodes (with context_id and version)
  - rule_nodes (rule_id/version, fire/skip reasons)
  - consultation_nodes (provider “LLM Conductor”, prompts, redactions, consensus)
  - synthesis_nodes (weights, constraints, utilities)
  - confidence_nodes (calibration details)
- signatures: list of {signer, signature, timestamp}
- redaction_info: policies applied and fields affected
- content_address: checksum for integrity

3.4 Conversation Protocols (MAD-to-MAD)
3.4.1 Transport-agnostic envelope
- headers:
  - message_id (ULID), conversation_id, correlation_id?
  - from_agent_id, to_agent_id
  - sent_at, ttl
  - protocol_version (min_supported, max_supported)
  - message_type
  - payload_schema_uri, payload_schema_version
  - auth: {scheme, credentials or token ref}
  - privacy: {classification, redactions_applied}
  - budgets: {time_ms, cost_units, max_tokens?}
  - signatures (optional)
- payload: typed per message_type
- semantics: at-least-once delivery; receivers must be idempotent

3.4.2 Message types (non-exhaustive)
- CapabilityAdvertise
  - capability_name, versions, SLA, cost_model, auth_requirements, privacy_level, health
- CapabilityQuery
  - capability_name, constraints (latency, cost ceiling, jurisdiction), required_schema
- CapabilityResolution
  - list of providers with descriptors and endpoints
- ConsultationRequest (e.g., to LLM Conductor)
  - question, constraints, context_refs, expected_output_schema
- ConsultationResponse
  - answer, consensus metrics, dissent summaries, citations, cost, latency
- Health/Heartbeat
  - status, uptime, load, planned downtime
- BudgetUpdate
  - new limits, rationale, validity window
- Error/NACK
  - code, message, retriable: bool, backoff_hint, schema_mismatch_info
- VersionNegotiation
  - proposed versions, accepted versions, deprecation dates
- Cancel
  - cancellation reason, effective_at

3.4.3 Capability registry
- Registration record fields
  - provider_agent_id, capability_name, version_range, schema_refs, SLA (p50/p95), cost model, auth and privacy requirements, tags, jurisdiction constraints, health endpoint
- Discovery flows
  - push (advertise) and pull (query) models
- Health and de-listing policies
  - failure thresholds, quarantine windows, operator overrides

3.4.4 Error handling and versioning
- Standard error codes
  - CAPABILITY_NOT_FOUND, UNAUTHORIZED, BUDGET_EXCEEDED, INVALID_SCHEMA, VERSION_UNSUPPORTED, RATE_LIMITED, TEMPORARILY_UNAVAILABLE, INTERNAL_ERROR
- Version negotiation
  - header-driven; both sides agree to a concrete protocol_version and schema_version for the conversation
- Backward compatibility
  - additive fields allowed; removals require major version bump; deprecation windows communicated via VersionNegotiation

3.4.5 Security and privacy
- Mutual auth (mTLS, OIDC tokens with audience binding)
- Least-privilege scopes for capability access
- PII minimization, transcript redaction, retention classes and expirations
- Encryption in transit and at rest for transcripts and artifacts

3.5 LLM Conductor usage model
- Role: A Half-MAD that offers the LLM Orchestra capability to any MAD
- Invocation: DER issues ConsultationRequest conversations when ambiguity or novelty requires multi-model insight
- Governance: budgets, privacy redactions, transcript retention per policy; consultation summaries referenced in Reasoning Trace

4. Integration Boundaries
- ICCM → IDE: Structured Context contract
- IDE internal: Rules Engine → DER via Rule Engine Output
- IDE → IEE: Decision Package
- IEE → State Manager (IAE): Execution Outcome Package
- All components read/write State Manager via versioned APIs
- LLM Conductor: conversations conforming to protocol above

5. Governance and Change Management
- Schema versioning and deprecation policy across contracts
- Cross-discipline change review and rollback plans
- Safety case templates and incident playbooks
- Calibration and validation policies for confidence signals

6. Metrics and Validation (high level)
- Contract conformance rates, replay determinism, calibration error
- Decision-to-action success, safety invariant revalidation pass rate
- Conversation cost/latency budgets adherence
- Feedback loop latency (execution → state → context availability)

Appendix A: Master Glossary (selected)
- MAD: Multipurpose Agentic Duo, the architecture pattern assembled by IAE
- Half-MAD: Minimal MAD providing a capability to others via conversations
- LLM Conductor: Half-MAD providing the LLM Orchestra capability
- Thinking Engine: CET + Rules Engine + DER + State Manager
- Doing Engine: Domain-specific execution component (IEE)
- State Manager: IAE-owned memory system (World Model, Task Context, Execution State)
- Conversation: MAD-to-MAD messaging per protocol
- Capability: A function provided by a MAD to others via conversations
- Canonical Contracts: Structured Context, Rule Engine Output, Decision Package, Execution Outcome Package, Reasoning Trace


--- 00_IDE_Intelligent_Decision_Engineering_v1.1.txt ---
Paper 00: Intelligent Decision Engineering (IDE) - Master Document
Version: 1.1
Date: 2025-10-06
Status: DRAFT - Council of Elders Synthesis (v1.1)
Repository: Joshua (IDE discipline within IAE ecosystem)
Synthesized by: Council of Elders

Changelog
- v1.1 (2025-10-06): Normalized to quaternary structure (ICCM + IDE + IEE + IAE). Clarified MAD as an architecture pattern within IAE. Corrected Thinking Engine composition to four components (CET + Rules Engine + DER + State Manager). LLM Orchestra naming aligned: LLM Conductor is the Half-MAD; references to implementation names removed. Adopted canonical contract names and fields consistent with IAE Paper 00 v1.1. Updated consultation and integration sections to use the conversation protocol and Decision Package v1.
- v1.0 (2025-10-06): Initial version defining IDE discipline, Rules Engine, and DER.

Executive Summary
IDE is the discipline that engineers transparent, auditable, controllable, and adaptive decisions within MAD agents. IDE produces the Rules Engine and the Decision Engineering Recommender (DER), which together form the decision core of the Thinking Engine. IDE consumes Structured Context (from ICCM/CET) and reads/writes via the IAE-owned State Manager.

Key normalizations in v1.1:
- Quaternary structure enforced: ICCM (context) + IDE (decisions) + IEE (execution) + IAE (assembly/state)
- Thinking Engine has four components; LLM Orchestra is an external capability provided by the LLM Conductor Half-MAD
- Canonical contracts adopted: Structured Context, Rule Engine Output, Decision Package, Execution Outcome Package, Reasoning Trace
- Conversations over calls: all cross-MAD interactions follow the IAE conversation protocol

1. Introduction: Why Decision Engineering
- Safety-critical domains require deterministic guardrails and auditable synthesis
- IDE defines a hybrid decision process: Rules Engine for the known, DER for the unknown or ambiguous, bounded by policy
- Confidence is first-class and calibrated; low confidence triggers alternatives or human escalation

2. IDE Principles (unchanged in spirit, normalized in terms)
- Transparency, auditability, controllability, adaptability, confidence-awareness
- Separation of concerns: CET shapes context; IDE decides; IEE executes; IAE provides state and assembly
- Human-in-the-loop readiness: explicit abstain and escalation policies by risk tier

3. Architecture
3.1 Components
- Rules Engine (deterministic)
- DER (synthesis, arbitration, confidence estimation)
- External consultative capability: LLM Conductor (LLM Orchestra) accessed via conversations initiated by DER when needed
- State Manager (IAE) used for world, task, and execution state

3.2 Decision flow (normalized)
- Input: Structured Context (CET)
- Rules pass: Rule Engine Output (status, matches, guardrails)
- Gatekeeping: DER either adopts deterministic matches (when allowed by policy), synthesizes options, or consults LLM Conductor
- Synthesis: evidence fusion under constraints and utilities
- Output: Decision Package to Doing Engine (IEE), with Reasoning Trace reference
- Feedback: Execution Outcome Package stored; DER can be re-engaged on deviations

3.3 Rules Engine specification (summary)
- Input: Structured Context, relevant State Manager reads
- Output: Rule Engine Output (canonical contract)
- Requirements:
  - Deterministic execution; support multiple formalisms (tables, production, logic, policy engines)
  - Guardrails and safety invariants prechecked
  - Conflict resolution strategies and coverage reporting
  - Request for CET re-transformation when features are missing or stale
- Non-functional:
  - Low latency, high throughput, reproducibility, observability, verification alignment

3.4 DER specification (summary)
- Inputs: Structured Context, Rule Engine Output, World/Task state, optional LLM Conductor consultations
- Functions:
  - Gatekeeper (deterministic adopt/refine/consult/abstain)
  - Arbitration and synthesis (multi-objective under policy)
  - Consultation Manager (conversation protocol)
  - Confidence Estimator (calibrated scores or sets)
  - Trace Builder (content-addressed, signed)
  - Escalation and alternatives
- Output: Decision Package (canonical), with Reasoning Trace
- Policies:
  - Risk tier thresholds for accept/abstain/escalate
  - Budgets and privacy for consultations
  - Post-synthesis constraint recheck against safety invariants

4. Canonical contracts (IDE view; authoritative definitions in IAE Paper 00 v1.1)
4.1 Structured Context v1 (consumed)
- As defined by IAE; IDE relies on fields: context_id, task_id, risk_tier, problem_frame, features, safety_profile, world_refs, health, provenance, trust_level

4.2 Rule Engine Output v1 (produced by Rules, consumed by DER)
- Fields: rule_output_id, ruleset_version, status, matches (with action_proposal, certainty, mandatory), guardrails_triggered, conflicts, residuals, coverage, confidence_rule, trace_ref

4.3 Decision Package v1 (produced by DER, consumed by IEE)
- Fields: decision_id, decision_type, selected_action (name, parameters, preconditions, expected_effects), safety_assertions, confidence_score, risk_tier, abstain_threshold, human_review_required, escalation_route, alternatives, reasoning_trace_ref, references (context_id, rule_output_id, world_version_id, versions), consultations (provider “LLM Conductor”, consultation_id, consensus_metrics), budgets, policy_requirements

4.4 Reasoning Trace v1 (produced by DER)
- Trace graph of inputs, rule firings, consultations, synthesis, confidence calculation, with signatures and redactions

5. Conversations: LLM Conductor and beyond
- DER initiates ConsultationRequest to LLM Conductor when ambiguity/novelty warrants
- Requests include: question, constraints, context_refs, expected schema; responses include consensus metrics, dissent handling, citations
- All conversations adhere to the IAE conversation envelope, error codes, and version negotiation
- Privacy: PII minimization and redaction policies applied; summaries and hashes retained per policy

6. Policies: Risk, safety, and confidence
- Risk tiers (T0–T3) map to thresholds:
  - Example defaults: T0 accept if confidence ≥ 0.6; T1 ≥ 0.7; T2 ≥ 0.8; T3 ≥ 0.9 with human review unless explicitly waived
- Safety invariants catalog referenced by Rules and revalidated by IEE at execution time
- Confidence calibration: monitor ECE/Brier; adjust bands; optionally provide conformal prediction sets for decision classes that support them

7. Integration boundaries
- ICCM → IDE: Structured Context is contract; DER may request re-transformation or feature augmentation via IAE State Manager events or direct feedback to CET processes
- IDE → IEE: Decision Package is the sole directive interface; no ad hoc calls
- IDE ↔ State Manager: read world/task state; persist Decision Package, Reasoning Trace links; subscribe to Execution Outcome events for learning
- IDE ↔ Half-MADs: conversations-only, registry-based discovery

8. Roadmap (phased)
- Phase 1: Rules Engine v1, DER v1, LLM Conductor consults, Trace v1, calibration baseline
- Phase 2: Conflict analytics, conformal sets where applicable, improved aggregation, red-team harness, re-transformation loops
- Phase 3: Multi-agent decision coordination, negotiation protocols, advanced governance

9. Metrics
- Decision accuracy and latency; rule coverage; consultation invocation rate; calibration error; trace completeness; reproducibility; selective prediction performance

10. Conclusion
IDE delivers a principled hybrid decision core for MAD agents within the quaternary structure. By adopting canonical contracts, conversation protocols, and the LLM Conductor capability as an external consultative resource, IDE ensures decisions are transparent, auditable, controllable, and adaptive.

Appendix: Terminology (delta)
- LLM Conductor: Half-MAD providing LLM Orchestra
- Thinking Engine: CET + Rules Engine + DER + State Manager
- Decision Package: directive from DER to Doing Engine
- Execution Outcome Package: Doing Engine’s report to State Manager
- Reasoning Trace: audit and replay artifact


--- 00_IEE_Intelligent_Execution_Engineering_v1.1.txt ---
Paper 00: Intelligent Execution Engineering (IEE) - Master Document
Version: 1.1
Date: 2025-10-06
Status: DRAFT - Strengthened placeholder with contracts and feedback loops
Repository: Joshua (IEE discipline within IAE ecosystem)
Purpose: Define the Doing Engine discipline, completing the quaternary structure of IAE

Changelog
- v1.1 (2025-10-06): Normalized to quaternary structure (ICCM + IDE + IEE + IAE). Adopted canonical contracts (consumes Decision Package; produces Execution Outcome Package). Clarified boundary with State Manager and DER re-engagement triggers. Added execution feedback loops, safety revalidation, and observability requirements. Aligned terminology (conversations, capabilities). LLM Conductor referenced only as an external capability where execution-time consultative checks are explicitly allowed by policy.
- v1.0 (2025-10-06): Initial placeholder framing IEE’s scope.

Executive Summary
IEE is the discipline of execution. It produces Doing Engines that translate decisions into safe, effective actions. Doing Engines validate directives, orchestrate tools/APIs, monitor progress, handle errors, and synthesize outcomes. They consume Decision Packages (from IDE/DER) and produce Execution Outcome Packages persisted by the IAE State Manager. They also revalidate safety invariants and participate in the architecture’s core feedback loop.

1. Foundations
1.1 Role in the quaternary
- ICCM: context engineering (CET)
- IDE: decision engineering (Rules Engine + DER)
- IEE: execution engineering (Doing Engines)
- IAE: assembly and State Manager

1.2 Execution engineering principles
- Safety-first execution with invariant revalidation
- Domain specialization through patterns (tool execution, API orchestration, human interaction)
- Observability and reproducibility
- Feedback loops as first-class: outcomes inform future context and decisions
- Conversations for any cross-MAD capability consumption (rare for IEE; policy-gated)

2. Doing Engine architecture
2.1 Components
- Decision Validator
  - Validate preconditions, safety_assertions, entitlements, resource availability, and jurisdiction/policy gates
- Tool Orchestrator
  - Select tools/APIs, bind parameters, manage execution plans and dependencies
- Execution Monitor
  - Track progress, enforce timeouts and budgets, collect telemetry, detect drift against expected_effects
- Outcome Synthesizer
  - Compare observed vs. expected effects, assess status, compile diagnostics and artifacts, and produce Execution Outcome Package

2.2 Interface contracts (canonical)
- Input: Decision Package v1 (DER → Doing Engine)
  - Required fields used by IEE: decision_id, selected_action (name, parameters, preconditions, expected_effects), safety_assertions, risk_tier, confidence_score, budgeting, reasoning_trace_ref, references (context_id, world_version_id), policy_requirements
- Output: Execution Outcome Package v1 (Doing Engine → State Manager)
  - Fields: outcome_id, decision_id, status, observed_effects, deviations, safety_validation_results, telemetry, error_diagnostics, artifacts, world_version_id_before/after, outcome_trace_ref

2.3 Safety invariant revalidation
- All safety_assertions in Decision Package are rechecked before and optionally during execution
- On pre-execution failure:
  - Abort; emit outcome with failure status and diagnostics; offer reengagement_advice
- On mid-execution violation or drift:
  - Pause or abort based on policy; emit partial outcome and remediation suggestions; request DER re-engagement when appropriate

2.4 DER re-engagement and clarifications
- Triggers:
  - Precondition unsatisfied; safety invariant violations; unresolvable tool errors; deviations with severity above thresholds; budget exhaustion
- Mechanism:
  - Emit Execution Outcome Package with reengagement_advice and notify DER via State Manager event or a direct ClarificationRequest conversation when permitted by policy
- ClarificationRequest (conversation payload)
  - decision_id, failure_reason, current_state summary, proposed options (if any), time/budget remaining, desired schema for updated directive
- DER replies with a new Decision Package or advises abort/escalation

2.5 Optional consultative checks
- Policy may allow IEE to request domain checks from external capabilities (e.g., LLM Conductor for interpretation of ambiguous tool output)
- Any such use must:
  - Be explicitly allowed for the decision type and risk tier
  - Use the conversation protocol and respect budgets and privacy
  - Record consultation summaries and costs in telemetry
  - Never override DER authority for action selection

3. Execution patterns (concise)
- Tool Execution (e.g., Hopper)
  - Shell, git, filesystem actions; sandboxed; command whitelists; file diffs as artifacts
- API Orchestration (e.g., Grace)
  - REST/gRPC/DB calls; rate limiting, schema validation; compensating transactions
- Human Interaction
  - UI prompts and confirmations; output sanitization; stateful interactions
- Hybrid
  - Composition of the above with explicit handoffs and safety checks

4. Observability, telemetry, and artifacts
- Telemetry minimum set
  - Latency, cost, resource usage, API quotas, retries, tool versions
- Outcome trace
  - Ordered event log linked to decision_id; content-addressed and signed
- Artifacts
  - Files, logs, diffs, build outputs; checksums and URIs
- Monitoring
  - Health endpoints, budgets adherence, error taxonomies, SLOs

5. Integration boundaries
- IDE → IEE: Decision Package v1 is the sole directive interface
- IEE → State Manager (IAE): persist Execution Outcome Package; update Execution State; link artifacts and outcome traces
- IEE → ICCM: no direct interface; effects observed by State Manager can drive CET re-transformations on subsequent tasks
- IEE ↔ Half-MADs: rare, policy-gated conversations only (e.g., LLM Conductor for non-decisional consults); default path is DER re-engagement

6. Governance and safety
- Shared safety invariants catalog and identifiers across IDE and IEE
- Risk-tiered execution policies (timeouts, tool restrictions, human approvals)
- Change management for tool adapters (version pinning, canary, rollback)
- Incident response and postmortems linked to Reasoning and Outcome traces

7. Roadmap
- Phase 1 (now): Implement minimal Doing Engines for Hopper and Grace aligned to canonical contracts; validate safety revalidation and outcome synthesis
- Phase 2: Expand error recovery patterns, compensating actions, richer telemetry, and drift detectors
- Phase 3: Multi-tool coordination DAGs, real-time constraints, human-in-the-loop execution patterns

8. Metrics
- Execution success rate and time-to-completion
- Safety validation pass rate; zero critical violations target
- DER re-engagement trigger accuracy and resolution time
- Telemetry completeness and diagnostic quality
- Budget adherence and cost predictability

9. Conclusion
IEE formalizes execution as a first-class discipline in the quaternary IAE structure. By standardizing the interfaces with IDE and the State Manager, enforcing safety revalidation, and closing the loop with detailed outcomes, Doing Engines make MAD agents not just smart, but reliably effective and governable.

Appendix: Key terms
- Decision Package: directive from DER to Doing Engine
- Execution Outcome Package: Doing Engine’s report to State Manager
- Re-engagement: policy-driven request for DER assistance when execution cannot proceed safely or successfully
- LLM Conductor: Half-MAD offering LLM Orchestra capability via conversations (not part of the Thinking Engine)


End of v1.1 synthesis for IAE Paper 00, IDE Paper 00, and IEE Paper 00.