Council of Elders Integrated Review
Suite: 00_IAE, 00_IDE, 00_IEE (v1.0, 2025-10-06)

Summary verdict
- Strengths: Strong conceptual backbone, clear separation of concerns, principled hybrid decision architecture, solid articulation of Half-MAD capabilities, and a credible roadmap anchored by Hopper and Grace.
- Key inconsistencies to resolve: Discipline naming (MAD vs IAE), quaternary vs “trinity” framing, Thinking Engine composition (is LLM Orchestra inside or external?), and interface/contract nomenclature.
- Key gaps to close: Canonical data contracts (Decision/Directive and Execution Outcome), conversation and capability discovery protocols, State Manager specification, risk-tier and confidence policies, and safety invariants spanning IDE↔IEE.
- Readiness: Not yet ready for v2.0 implementation across the entire stack. One more synthesis pass focused on normalization and contracts is required. IDE and IAE can proceed to limited v2.0 pilots if the contract set is finalized first.

1) Consistency analysis

1.1 Discipline boundaries and naming
- Intended quaternary structure: ICCM (context) + IDE (decisions) + IEE (execution) + IAE (agent assembly/overarching discipline).
- Inconsistency:
  - IDE Paper 00 repeatedly frames a “trinity (ICCM + IDE + MAD)” and uses “MAD” as if it were the assembly discipline. This conflicts with IAE Paper 00, which defines “IAE as discipline” and “MAD as an architecture pattern within IAE.”
  - IEE Paper 00’s “Quaternary Structure (ICCM + IDE + IEE + MAD)” likewise substitutes MAD for IAE.
- Required normalization:
  - Use IAE as the discipline and MAD as the architecture pattern consistently. The quaternary is ICCM + IDE + IEE + IAE. MAD is the core architecture pattern produced within the IAE discipline.

1.2 Component responsibilities and composition
- State Manager ownership:
  - IAE Paper 00 places State Manager under IAE (Agent Assembly).
  - IDE Paper 00 uses it within the Thinking Engine equation; that’s fine if it explicitly cites ownership by IAE.
  - Action: Explicitly state in all papers that State Manager is provided/owned by IAE and participates in the Thinking Engine assembly.
- Thinking Engine composition:
  - IAE lists five components and includes the LLM Orchestra as “component 3,” yet elsewhere it states Fiedler (LLM Orchestra) is a Half-MAD capability available to all MADs (external).
  - Action: Choose one stance and apply consistently. Recommended: The Thinking Engine consists of four core components (CET, Rules Engine, DER, State Manager). LLM Orchestra is an external consultative capability (Half-MAD) accessed via conversations.

1.3 Interfaces and contracts
- Naming inconsistency:
  - IDE uses “FinalDecision,” “Decision Package,” and “Decision” interchangeably; IEE uses “Decision Package.”
  - IEE references “Execution Outcome Package,” while IAE mentions “telemetry/outcome reporting” without a named contract.
  - Action: Adopt canonical names across the suite:
    - StructuredContext (from CET)
    - RuleEngineOutput (from Rules Engine)
    - Decision Package (from DER to Doing Engine)
    - Execution Outcome Package (from Doing Engine to State Manager/DER)
    - Reasoning Trace (auditable artifact)
- Boundary clarity:
  - IDE → IEE: Decision Package schema must be standardized (action, parameters, preconditions, safety assertions, expected effects, confidence, trace_ref).
  - IEE → State Manager/IDE: Execution Outcome Package schema must be standardized (status, observed effects, deviations from expected, error diagnostics, telemetry, cost/latency, trace_ref).
  - IAE: Must publish both schemas and the State Manager’s API for persistence, linking, and replay.

1.4 Terminology
- Conversations and capabilities:
  - IAE and IDE consistently prefer “conversations” and “capabilities.” IDE explicitly says “Conversations over calls.” Good.
  - IEE uses “API calls” appropriately for external world interactions. Ensure any inter-MAD communication is described as conversations.
- Half-MADs and Full MADs:
  - Consistent across IAE and IDE. IEE is silent, which is acceptable; consider a brief cross-link to the capability model for completeness.

2) Completeness check

2.1 IAE’s integration strength
- IAE Paper 00 does a good job situating IDE and Half-MADs and articulating the dual-engine pattern. It also frames the State Manager and Thinking-Doing boundary conceptually.
- It falls short of publishing the concrete contracts required to implement the boundary and the feedback loop.

2.2 Gaps to close before v2.0 build-out
- Canonical contracts:
  - Decision Package and Execution Outcome Package schemas are referenced but not specified in a formal, versioned contract with field names, types, optionality, and constraints.
- Conversation protocol:
  - No canonical conversation schema for MAD-to-MAD messaging (message types, correlation IDs, versioning, capability discovery/registration, addressing, error handling).
- Capability discovery and registration:
  - IAE mentions discovery/registration but no registry spec, announcement protocol, or health/latency/cost metadata contract.
- State Manager specification:
  - Tripartite state is defined conceptually (World/Task/Execution), but no API contract (create/read/update links, trace links, retention policies, immutability, provenance, replay).
- Risk tiers and confidence policy:
  - IDE defines the concepts but lacks a canonical, cross-discipline policy (tier definitions, thresholds for accept/abstain/escalate, default values, governance).
- Safety invariants across IDE↔IEE:
  - Rules Engine guardrails and Doing Engine safety validation need a shared invariant model so constraints checked during decision are revalidated during execution (and vice versa) with explicit mismatch handling.
- DER re-engagement on execution failure:
  - IDE mentions re-engagement conceptually; the trigger, payload, and loopback message schema are not defined.
- LLM Orchestra usage governance:
  - Budgets, selection strategy, privacy constraints, and transcript retention policies are discussed but not codified as a policy contract.
- IEE detail is placeholder:
  - This is acceptable strategy-wise, but the minimal Doing Engine interface (validator/orchestrator/monitor/outcome synthesizer contracts) should be finalized now to unblock Hopper/Grace.

3) Terminology validation

Confirmations
- Conversations used correctly in IAE and IDE for MAD-to-MAD interactions.
- Capabilities used correctly for what MADs provide to each other (and Half-MADs).
- Half-MADs and Full MADs used appropriately in IAE and IDE.
- Quaternary structure intended: ICCM + IDE + IEE + IAE.

Corrections required
- Replace all instances of “trinity (ICCM + IDE + MAD)” and “Quaternary (ICCM + IDE + IEE + MAD)” with “Quaternary (ICCM + IDE + IEE + IAE)”. Clarify that MAD is the architecture pattern under IAE, not a separate discipline.
- Replace “MAD → boundary” references in IDE/IEE that imply MAD as a discipline with “IAE (MAD assembly)”.
- Replace any residual “service call/API” phrasing for inter-MAD interactions with “conversations.” Keep “API calls” only for Doing Engine’s external-world actions.
- Standardize object names: use “Decision Package” consistently (alias “FinalDecision” acceptable in prose, but not as a schema name). Use “Execution Outcome Package” consistently.

4) Enhancement recommendations

4.1 Publish canonical contracts (add to IAE Paper 00 or as IAE Paper 02: Contracts)
- StructuredContext v1:
  - IDs, provenance, trust, health, task framing, features (typed and versioned), safety profile, risk tier, TTL.
- RuleEngineOutput v1:
  - Matches (IDs, versions, actions), status enum, conflicts, guardrails_triggered, coverage, confidence_rule, residuals, trace.
- Decision Package v1 (DER → Doing Engine):
  - decision_id, task_id, timestamp, decision_type
  - selected_action (name, parameters, preconditions, expected effects)
  - safety_assertions
  - confidence_score with interpretation
  - reasoning trace reference (trace_ref)
  - alternatives with expected utility and trade-offs
  - versions (DER_version, Rules_version_set, CET_version, models_used)
  - governance fields (risk_tier, abstain_threshold, escalation_route)
- Execution Outcome Package v1 (Doing Engine → State Manager/DER):
  - decision_id, action_name, start/end timestamps
  - status (success, failure, partial, aborted)
  - observed_effects vs expected_effects
  - deviations and drift signals
  - error diagnostics (type, message, stack/log refs)
  - telemetry (cost, latency, resource usage)
  - safety_assertions revalidation results
  - outcome_trace_ref and artifacts
- Reasoning Trace v1:
  - Content-addressed, signed graph; includes rule IDs/versions, context_id chain, consultations with redactions/hashes, confidence calculation summary.

4.2 Conversations and capability discovery (add to IAE Paper 03: Conversation Protocols)
- Message types: ConsultationRequest/Response, CapabilityQuery/Advertise, Health/Heartbeat, BudgetUpdate, Error/NACK.
- Transport-neutral spec (headers, correlation IDs, versioning, schema refs).
- Capability registry: schema (capability name, versions, SLAs, cost, latency, risk profile, required inputs/outputs), discovery flow, health checks.
- Privacy and redaction rules (PII minimization, transcript retention policies).

4.3 State Manager (add to IAE Paper 04: State Manager Specification)
- Data model and API for World/Task/Execution state.
- Versioning, provenance, and immutability rules.
- Trace linkage (context_id, decision_id, outcome ids).
- Replay and audit APIs.
- Retention and security model.

4.4 Safety, risk, and confidence policy (add to IDE Paper 05 and cross-reference in IAE/IEE)
- Risk tier definitions and default thresholds (accept/abstain/escalate).
- Confidence interpretation contract and calibration method.
- Safety invariants catalog and cross-check flow (IDE prechecks, IEE revalidation).
- Human-in-the-loop triggers and operator UI data contract.

4.5 Consistency edits (surgical redlines)
- Replace “trinity (ICCM + IDE + MAD)” with “quaternary (ICCM + IDE + IEE + IAE)” in IDE sections 0, 1.3, 7.2, and anywhere “MAD” is used as a discipline.
- In IEE, change “Quaternary Structure (ICCM + IDE + IEE + MAD)” to “… + IAE”, and fix the “Complete MAD Architecture” block to:
  - Thinking Engine (ICCM + IDE + IAE/State Manager)
  - Decision → Doing Engine (IEE)
  - Execution → State Manager (feedback; IAE)
- In IAE 2.2 and 2.4, adjust Thinking Engine composition to exclude LLM Orchestra as a core component. Recast it as an external consultative capability accessed via conversations (Half-MAD Fiedler). Retain its centrality without conflating ownership.
- Standardize on “Decision Package” and “Execution Outcome Package” across all three papers.
- Replace “service calls” or “API requests” in inter-MAD contexts with “conversations.” Keep “API calls” only in IEE for external systems.

4.6 Minimal Doing Engine interface (advance IEE beyond placeholder without over-specifying)
- Publish validator/orchestrator/monitor/outcome synthesizer interface signatures aligned to Decision Package and Execution Outcome Package.
- Define precondition/safety assertion vocabulary and mapping to validator checks.
- Define expected-effects → observed-effects comparison contract.

4.7 Governance and change management
- Cross-discipline versioning rules: CET schema versioning, Ruleset version sets, DER versions, model snapshots, capability versions.
- Change review workflow and rollback policies shared across ICCM/IDE/IEE/IAE.
- Safety case templates and incident playbooks referenced by all disciplines.

4.8 Test harness and validation
- Contract conformance tests for all four contracts (context, rule output, decision, outcome).
- Replay harness that reconstructs decisions from traces.
- Adversarial and red-team scenarios for both IDE and IEE.
- Shadow-mode DER and A/B rule evaluation pipelines.

5) Ready for v2.0?

Verdict
- Not yet for a full v2.0 push. The suite needs one synthesis round focused on:
  - Discipline naming normalization (use IAE, not MAD, as the discipline).
  - Thinking Engine composition correction (LLM Orchestra as external capability).
  - Publication of canonical, versioned contracts (Decision Package and Execution Outcome Package).
  - Conversation/capability discovery protocols.
  - Minimal State Manager spec.

Conditional go for targeted implementation
- If the above contracts and naming normalization are completed, IDE and IAE can proceed to:
  - Implement Rules Engine v1 and DER v1 against the StructuredContext/Decision Package contracts.
  - Integrate with a minimal Doing Engine that honors the Execution Outcome Package.
  - Pilot in Hopper/Grace with clearly scoped decision domains and risk tiers.

Pre–v2.0 checklist (must be green)
- Quaternary structure standardized in all three papers: ICCM + IDE + IEE + IAE.
- Thinking Engine defined as CET + Rules Engine + DER + State Manager (IAE-owned); LLM Orchestra identified as Half-MAD capability.
- Contracts published and versioned: StructuredContext v1, RuleEngineOutput v1, Decision Package v1, Execution Outcome Package v1, Reasoning Trace v1.
- Conversation and capability discovery protocols published v1.
- Risk/Confidence policy and safety invariant cross-check flow documented and adopted by IDE and IEE.
- Minimal State Manager API v1 published.

Closing note
The architectural vision is coherent and compelling. A short, contract-centric synthesis pass will remove residual ambiguities, align terminology with the quaternary structure (ICCM + IDE + IEE + IAE), and de-risk implementation. Once those redlines and contracts are in place, the papers will be a strong foundation for the MAD architecture’s v2.0 implementation.