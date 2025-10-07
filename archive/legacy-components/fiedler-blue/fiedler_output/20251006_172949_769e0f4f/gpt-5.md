Paper 00: IDE (Intelligent Decision Engineering) — Master Document

Version: Council Synthesis v1.0
Date: 2025-10-06
Status: Foundation Paper (Paper 00)
Repository: Joshua (IDE discipline within the MAD ecosystem)
Purpose: Define the Intelligent Decision Engineering discipline and deliver the Rules Engine and DER components that, together with CET (from ICCM) and State Manager (MAD), comprise the MAD Thinking Engine.

Executive Summary

- Intelligent Decision Engineering (IDE) formalizes decision-making for Machine-Agency Devices (MADs) by bridging symbolic decision logic (deterministic, auditable rules) with probabilistic synthesis (DER) under rich context (CET from ICCM).
- IDE produces two Thinking Engine components:
  - Rules Engine: A deterministic, transparent, and verifiable engine for known scenarios, policies, and safety invariants.
  - DER (Decision Engineering Recommender): A synthesis layer that integrates Rules output, CET-structured context, State Manager world state, and optional consultation with the LLM Orchestra (via Fiedler MAD), producing an actionable decision with calibrated confidence and an auditable reasoning trace.
- IDE completes the trinity with ICCM (context) and MAD (agentic assembly), ensuring agents decide with transparency, auditability, controllability, adaptivity, and quantified confidence.
- This Paper 00 defines the discipline, enumerates principles, specifies the architecture and interfaces, proposes a hierarchical paper series, sets the roadmap and metrics, and frames research questions for the Council.

1. Introduction: The Decision Problem in AI Agents

1.1 Why Decision Engineering Matters

- In practice, most AI agents make decisions that are opaque, weakly grounded in explicit policy, and difficult to audit or reproduce. This undermines safety, compliance, trust, and lifecycle governance.
- Decision spaces vary by familiarity and risk. Known, high-regret spaces require strict policy adherence; novel or ambiguous spaces benefit from probabilistic synthesis and external consultation.
- Without a formal discipline, ad hoc decisions accumulate technical, compliance, and ethical debt. IDE defines a principled, inspectable, and maintainable path.

1.2 The IDE Discipline

- Input to IDE: Structured context from CET; current world state from State Manager; task specification; policy, safety, and compliance constraints; decision risk tier and cost-of-error profiles; operator preferences; capability availability across MADs.
- Output from IDE: Actionable decision (or set of options), calibrated confidence, reasoning trace with provenance, rule matches and overrides, optional alternative recommendations or deferral with escalation path.
- Core innovations:
  - Hybrid architecture: deterministic Rules Engine for known and safety-critical cases; DER for synthesis under uncertainty, ambiguity, or novelty.
  - Deep integration with CET: context-as-contract, feature stability, context health checks, and re-transformation requests from DER.
  - Conversational consultation: when needed, DER engages the LLM Orchestra (Fiedler MAD) to incorporate multi-model insights into a traceable synthesis.
  - Confidence as a first-class signal: predictive calibration, monotonic alignment with realized accuracy, and conformal bounds where applicable.
  - Auditable epistemology: every decision yields an inspectable, replayable reasoning trace linked to versions of rules, models, and context.

1.3 The Trinity of Disciplines

- ICCM produces CET (context engineering), which converts messy inputs into structured, scoped, and optimized decision contexts.
- IDE produces Rules Engine + DER, which transform context into decisions.
- MAD assembles full agents by combining CET, Rules Engine, DER, and State Manager into the Thinking Engine; plus Doing Engine(s) that enact decisions safely.
- In the MAD Thinking Engine:
  - CET (ICCM) → Rules Engine (IDE) → DER (IDE) → State Manager interactions throughout → Decision delivered to Doing Engine.
- MADs communicate via conversations (not service calls) and advertise capabilities (not services). This vocabulary enforces agentic patterns and discourages brittle RPC mental models.

1.4 Document Organization

- Section 2: Theoretical foundations for IDE.
- Section 3–8: Architecture, specifications, and integration details for Rules Engine and DER with CET, State Manager, Doing Engines, and the LLM Orchestra.
- Section 9: Proposed hierarchical paper series for the IDE discipline.
- Section 10–13: Implementation roadmap, metrics, governance/safety, and reference implementation plan.
- Section 14–15: Use cases and multi-agent decision coordination.
- Section 16–18: Research questions, publication strategy, glossary, and appendices.

2. Theoretical Foundations

2.1 Decision Engineering Principles

- Transparency: Each decision must be explainable in terms of applied rules, synthesized judgments, data provenance, and model consultations. Rationales should be concise and verifiable against stored artifacts.
- Auditability: The full reasoning trace is persisted and replayable, with versioned references to rulesets, policies, model snapshots, and context transforms. Tamper-evident storage is preferred.
- Controllability: Deterministic rules govern known regimes, especially high-regret or regulated ones. Safety invariants and red-lines are enforced at all times via policy engines and runtime guards.
- Adaptability: When contexts are novel or ambiguous, DER uses probabilistic synthesis and consultative conversations to propose decisions with confidence and alternatives.
- Confidence: All outputs include quantitative confidence signals with explicit interpretation (e.g., calibrated probability of correctness or bounded prediction set). Coverage/selectivity trade-offs are tunable by risk tier.
- Separation of Concerns: Context shaping (ICCM/CET) is distinct from decision synthesis (IDE). Decision-making (IDE) is distinct from behaving (Doing Engines). State Manager mediates memory and world state across them.
- Minimality and Composability: IDE defines a minimal set of decision components and interfaces that compose across MADs and across capabilities. Nothing more than necessary to decide; nothing less than sufficient for safety.
- Human-in-the-Loop Readiness: Escalation paths, review workflows, and accountability hooks are first-class features, not afterthoughts.

2.2 Hybrid Decision Architecture

- Rules Engine: Executes deterministic logic expressed as policies, decision tables, production rules, or formal specifications. Strengths: speed, predictability, formal verification. Uses: safety gates, compliance enforcement, known playbooks, default routing, cost ceilings, rate limits, identity/entitlement checks.
- DER (Decision Engineering Recommender): Integrates rule outputs, CET context, and optional consultation with external MAD capabilities (notably Fiedler’s LLM Orchestra) to synthesize a decision with calibrated confidence and rationalized trade-offs. Strengths: handling ambiguity, novelty, multi-objective optimization, stakeholder alignment, and value-sensitive trade-offs.
- The hybrid is not a fallback hack. It is a principled approach: rules codify accepted knowledge; DER explores plausible extensions and integrates expert advice, under constraints and with explainable adjudication.

2.3 Decision Flow in the MAD Thinking Engine

- In-flow:
  - Task or trigger arrives.
  - CET transforms inputs into a structured, scoped context; validates and tags context for freshness, provenance, and trust level.
  - Rules Engine checks for deterministic matches; annotates matches with rule IDs, versions, and mandatory actions or guardrails.
  - DER receives the context and rule annotations; chooses one of: accept rule decision, refine/augment via synthesis, escalate for consultation, or defer.
- Out-flow:
  - DER returns an actionable decision with a confidence score, an explanation trace, alternatives if confidence is low, and any preconditions to be enforced by Doing Engines.
  - State Manager updates are proposed or requested (e.g., record a commitment, reserve a resource).
  - Doing Engine enacts the decision or requests clarification; if doing fails, DER can be re-engaged with a failure context.

2.4 Relationship to Existing Decision Systems

- Expert systems (CLIPS, Drools) emphasize production rules but lack modern probabilistic synthesis and lack contextual optimization across multi-agent settings.
- RL and neural decision networks excel in pattern-rich domains but often lack auditability and governance in regulated applications.
- Cognitive architectures (SOAR, ACT-R) integrate memory and rules but predate modern LLM orchestration and comprehensive context pipelines.
- IDE’s novelty:
  - Explicit, modular integration with CET for context health and re-transformation loops.
  - DER’s consultative synthesis layer with calibrated confidence, under policy constraints.
  - Conversations over calls: multi-agent decision coordination handled via dialogic protocols and capability discovery rather than hardwired APIs.
  - Auditable epistemology: decisions are reconstructible artifacts with formal references to rules, contexts, models, and consultation transcripts.

3. Architecture Overview and Interfaces

3.1 Components and Boundaries

- CET (ICCM):
  - Responsibility: Transform, scope, and validate input context; produce decision-ready features; encode task framing; assert context quality and provenance.
  - Interface to IDE: Context Package (schema defined below), re-transformation requests, context health signals.
- Rules Engine (IDE):
  - Responsibility: Evaluate deterministic rules, policy constraints, and safety invariants against the Context Package. Produce rule matches, actions, hard blocks, and policy annotations.
  - Interface to DER: Rule Decision Package with matches, priorities, required actions, and residual uncertainties.
- DER (IDE):
  - Responsibility: Synthesize final decision from context, rules, state, and consultations, with confidence and trace.
  - Interfaces:
    - Input: Context Package, Rule Decision Package, State Read Snapshot, Task Specification.
    - Output: Decision Package with action, confidence, rationale, trace, and alternatives.
    - Optional: Conversations with Fiedler MAD (LLM Orchestra) and other capability-bearing MADs.
- State Manager (MAD):
  - Responsibility: Store and serve world state, memory, commitments, event logs; support transactional updates and time-travel reads for audit.
  - Interfaces: Read/Write with IDE components; append-only decision logs; provenance and versioning.
- Doing Engine (MAD):
  - Responsibility: Execute decisions with safeguards; report outcome, side-effects, and exceptions; form feedback loop for learning and audit.
  - Interface: Accepts Decision Package and returns Execution Outcome Package.

3.2 Context and Decision Data Contracts

- Context Package (from CET):
  - Fields (illustrative, extensible):
    - context_id, task_id, created_at, ttl, provenance, trust_level
    - actor_profile, entitlements, risk_tier, jurisdiction
    - problem_frame: objective(s), constraints, preferences, utility proxies
    - features: typed, versioned, with units and ontological tags
    - environment: resources, load, cost windows, SLAs
    - safety_profile: red-lines, rate limits, exposure budgets
    - health: completeness, freshness, inferred anomalies, warnings
- Rule Decision Package (from Rules Engine):
  - Fields:
    - rule_matches: list of {rule_id, version, priority, action, mandatory: bool, params}
    - conflicts: list of conflicting rules and conflict rationale
    - guardrails_triggered: list of {policy_id, severity, required_block: bool}
    - coverage: proportion of context features utilized by matched rules
    - confidence_rule: heuristic confidence for matched decision(s) (0–1)
    - residuals: aspects of the decision left undecided (e.g., parameter ranges, selection among safe options)
- Decision Package (from DER to Doing Engine and logs):
  - Fields:
    - decision_id, task_id, timestamp, decision_type (choose/plan/route/approve/deny/etc.)
    - selected_action: name, parameters, preconditions, expected effects
    - confidence: calibrated probability of correctness or conformal coverage
    - rationale: structured natural language with references to trace nodes
    - trace_ref: pointer to Decision Trace artifact (hash, storage URI)
    - alternatives: list with expected utility, confidence, and trade-off notes
    - safety_assertions: invariant checks to revalidate at execution time
    - consultation_digest: topics consulted, consensus measure, dissent handling
    - DER_version, Rules_version_set, CET_version, models_used
- Execution Outcome Package (from Doing Engine back to IDE and logs):
  - Fields:
    - decision_id, outcome (success/failure/partial), telemetry, exceptions
    - realized_costs, realized_latencies, realized_risks
    - postconditions_met, drift_signals, operator_feedback

3.3 Decision Types

- Classification and routing (e.g., route a ticket, select a plan).
- Parameter selection (e.g., price, dosage, rate limit).
- Approval and gating (e.g., policy-compliant approval of changes).
- Scheduling and prioritization (e.g., allocate compute or human attention).
- Plan synthesis and option ranking (e.g., multi-step plan under constraints).
- Risk-informed abstention or escalation (e.g., defer decision, request human input).

3.4 Lifecycle

- Authoring: Rules authored from policy, domain knowledge, or distilled from outcomes; DER templates configured per decision type.
- Testing and Verification: Simulated inputs; property-based tests; formal property checks on rules; calibration checks on DER.
- Deployment: Canary and shadow modes; progressive coverage; recorded conversations for high-risk decisions.
- Operations: Monitoring metrics; red-teaming; rollbacks; version freeze during incidents.
- Learning: Feedback from outcomes; propose rule updates; update DER calibration; operator governance review.

4. Rules Engine Specification (IDE Component 1)

4.1 Functional Requirements

- Deterministic output for identical inputs and ruleset versions.
- Support for multiple rule representations:
  - Decision tables and trees for clarity and speed.
  - Production rules (if-then) with a Rete-like matcher for scale.
  - Declarative policy languages (OPA/Rego, Cedar).
  - Formal specifications (temporal logic) for critical invariants.
- Conflict resolution strategies:
  - Priority and specificity: more specific rules override general ones.
  - Policy dominance: safety and legal policies outrank business preferences.
  - Multi-policy merge: evaluate partial overlaps; produce residuals where deterministic resolution is not defined.
- Mandatory guardrails:
  - Safety invariants: unbreakable constraints, e.g., “never exceed dose limit.”
  - Resource and rate limits: budget controls, concurrency caps.
  - Identity, entitlement, and jurisdiction checks.
- Coverage reporting:
  - Which features were used; which policy sections touched; coverage score.
- Explanations:
  - For each match/conflict, a machine-renderable explanation with references to rule text, policy doc anchors, and test cases.
- Runtime hooks:
  - Request for CET re-transformation if required features are missing or stale.
  - Request for DER escalation if ambiguity persists.

4.2 Non-Functional Requirements

- Low latency (typical < 10 ms per evaluation for moderate rulesets).
- High throughput capability (optimized indexing, Rete network).
- Memory safety and predictable performance.
- Reproducibility: fully versioned rulesets; deterministic execution.
- Observability: tracing, metrics, debug logs, explainability on demand.
- Formal verification compatibility: static checking against invariants.

4.3 Rule Representation Options

- Decision Tables:
  - Human-friendly matrix; ideal for business operations.
  - Tools: CSV/JSON table formats; compile to efficient predicates.
- Decision Trees:
  - Visual and introspectable; can be learned from data then pruned and reviewed.
  - Ensure monotonic constraints where required.
- Production Rules:
  - Expressiveness for complex conditions; Rete/RETE-UL for matching.
  - Use salience/priorities and agenda control.
- Policy Engines (OPA/Rego, Cedar):
  - Externalized policy-as-code; strong for access control, tenancy, jurisdictional checks.
  - Composable with other rule forms via adapters.
- Formal Logic:
  - LTL/CTL for temporal properties; Answer Set Programming or Prolog for complex constraints or search.
  - Used for safety-critical properties and verification.

4.4 Authoring and Governance

- Authoring sources:
  - Policy documents, regulations, standard operating procedures.
  - Subject-matter expert input captured as tables/rules with tests.
  - Distillation from DER outcomes (semi-automated rule synthesis).
- Governance:
  - Rule proposals via merge requests with linters, coverage and conflict reports.
  - Regulatory annotations: jurisdiction, effective dates, deprecation schedule.
  - Change control: sign-offs by policy owners; automated impact analysis.
- Versioning and Rollouts:
  - Semantic versioning of rulesets; tags per decision domain.
  - Canary and shadow evaluation on live traffic with holdout logging.
  - Automatic rollback on incident triggers.

4.5 Evaluation Engine

- Matching:
  - Build an index over discrete and range features; compile guards for numeric, categorical, and temporal conditions.
  - Rete-like network for production rules; vectorized evaluation for tables/trees.
- Conflict Resolution:
  - Deterministic agenda ordering: policy precedence > safety > business > preference layers.
  - Tie-breaking by specificity, recency, and operator-configured lex order.
  - If unresolved, return residuals and ambiguity signals to DER.
- Guardrails and Hard Blocks:
  - Immediate block if any invariant violation matches.
  - Provide minimal sufficient explanation for the block and paths to compliance.
- Escalation signals:
  - Unknown feature combos, low coverage, or conflicting applicable rules.

4.6 Formal Verification and Testing

- Safety properties expressed in temporal/deontic logic:
  - Example: “Always: if action=Deploy and environment=Prod, then change_approved=true and rollback_plan_exists=true.”
- Model Checking:
  - Translate rules into finite-state models under bounded horizons; check properties via tools (nuXmv, TLA+, alloy).
- Property-Based Testing:
  - Generate synthetic contexts satisfying edge conditions; assert invariants hold.
- Regression Suites and Golden Sets:
  - Known decision inputs with expected outputs; used in CI.

4.7 Observability and Audit

- Rule match logs: rule_id, version, condition hash, feature snapshot hash.
- Coverage and conflict metrics: moving windows and heatmaps.
- Explainability:
  - Plain-language rendering with pointers to policy paragraphs.
  - Developer-friendly structured explanation.

5. DER (Decision Engineering Recommender) Specification (IDE Component 2)

5.1 Role and Placement

- DER is the synthesizer that:
  - Accepts context, rule outputs, and state.
  - Decides among applicable options or requests clarification.
  - Consults external capabilities via conversations when needed.
  - Returns a decision with calibrated confidence and a trace that binds the entire reasoning chain.

5.2 Inputs and Outputs

- Inputs:
  - Context Package (CET).
  - Rule Decision Package.
  - State Read Snapshot (from State Manager).
  - Task specification including objective(s), constraints, risk tier, utility proxies.
  - Operator governance parameters (e.g., abstain thresholds, escalation rules).
- Outputs:
  - Decision Package (as above).
  - Signals for:
    - CET re-transformation requests.
    - Human-in-the-loop escalation.
    - Capability requests to other MADs.

5.3 Internal Modules

- Gatekeeper:
  - Decides initial path: adopt deterministic decision; refine; consult; or defer.
  - Uses thresholds: rule_confidence, risk tier, novelty signals.
- Arbitration and Synthesis:
  - Multi-objective optimizer that reconciles policy, utility proxies, and stakeholder preferences.
  - Handles residuals from Rules Engine by assembling feasible sets and scoring them.
- Consultation Manager:
  - Conducts conversations with Fiedler (LLM Orchestra) or other MADs providing relevant capabilities.
  - Structures prompts with context and explicit questions; receives multi-model outputs and rationales.
- Aggregation and Consensus:
  - Aggregates rule recommendations, model votes, and constraints using weighted methods (e.g., Bayesian model averaging, weighted Borda count) subject to hard constraints.
- Confidence Estimator:
  - Produces calibrated probabilities or conformal sets, adjusted by decision type and risk tier.
- Trace Builder:
  - Maintains a graph of reasoning nodes: rules, models, consultations, and synthesis operations; emits a compact, verifiable trace artifact.
- Escalation and Alternatives:
  - Produces “safe to act” alternatives and a human-readable summary for operator review when confidence is low.

5.4 Orchestration Logic

- Primary decision loop:
  - If Rules Engine returns a mandatory action with no guardrail conflicts and confidence_rule ≥ θ_rule and risk tier ≤ T1 → accept; produce decision with rationale referencing rules.
  - Else if guardrails block → return denial with remedial steps; optionally offer compliant alternatives.
  - Else if residuals exist and feasible options can be enumerated from State Manager and rules constraints → synthesize options and score via utility; choose best if confidence ≥ θ_der else consider consultation.
  - Else if novelty/ambiguity signals or risk tier ≥ T2 → consult Fiedler (LLM Orchestra) with structured questions. Aggregate responses, re-check constraints, compute confidence.
  - If still low confidence → escalate to human; present top-k alternatives and trade-offs. Optionally defer.
- Risk-aware thresholds:
  - θ_rule and θ_der are per-domain and per-risk-tier; conservative defaults for higher tiers.
- Resource-aware controls:
  - Rate-limit consultations; cache reusable synthesis results; incorporate cost caps from Rules Engine.

5.5 Consultation with the LLM Orchestra (Fiedler MAD)

- Conversation Protocol:
  - DER introduces the decision context, constraints, and what is already known from rules.
  - DER asks targeted questions (e.g., “Given constraints C, which of options O1..Ok maximizes U and why?”).
  - Fiedler responds with model ensemble outputs, rationales, and dispersion signals (agreement/disagreement).
- Aggregation within DER:
  - Combine votes and rationales using:
    - Weighted majority with weights by historical model accuracy on similar contexts.
    - Dempster–Shafer combination to handle uncertainty and conflict.
    - Utility-adjusted scores with penalties for constraint proximity.
- Safety and Compliance:
  - All external suggestions are filtered through Rules Engine constraints and safety invariants a second time (post-synthesis constraint recheck).
  - Consultation transcript is included in the decision trace.

5.6 Confidence Scoring and Calibration

- Predictive features:
  - Rule coverage, conflict count, novelty signals, consultation dispersion, option margin (score gap), historical success in similar contexts, distance to safety thresholds.
- Calibration methods:
  - Platt scaling or isotonic regression per decision type and risk tier, retrained periodically.
  - Conformal prediction for set-valued recommendations when abstention is acceptable; control empirical coverage (e.g., 90%).
- Monitoring:
  - Reliability diagrams; expected calibration error (ECE); Brier score.
  - Selective prediction: decision coverage vs. risk-aware abstention trade-offs.

5.7 Reasoning Trace

- Graph structure with node types: RuleMatch, Constraint, Option, ModelOpinion, Aggregation, Decision, Escalation.
- Each node references:
  - Inputs (feature hashes, state versions), operations, outputs, and confidence.
  - Provenance of any external consultation (MAD id, conversation hash).
- Stored as a signed, content-addressed artifact with minimal personally identifiable information; compatible with privacy policies and retention rules.

5.8 Fallbacks and Escalation

- Fallback types:
  - Safe default action (defined by policy).
  - Minimal-risk alternative (e.g., lower dosage, slower rollout).
  - Abstain and request human review with summarized options.
- Escalation triggers:
  - Confidence below threshold; high novelty; disagreement above limit; rule-policy conflicts not resolvable; missing critical context; time pressure violation.
- Human-in-the-Loop:
  - Present decisions with succinct rationales and trace excerpts.
  - Capture operator choices to feed learning and governance.

6. Integration with CET (from ICCM)

6.1 Context as a Contract

- CET guarantees:
  - Feature definitions and ontological tags.
  - Freshness bounds and provenance chain.
  - Quality metrics and health flags for context.
  - Task framing aligned with operator intent and constraints.
- IDE relies on CET’s contract to ensure stable inputs; CET relies on IDE feedback to improve context.

6.2 Re-Transformation Loop

- DER and Rules Engine may request:
  - Feature augmentation (e.g., add derived features or alternative encodings).
  - Scope adjustment (e.g., narrower time window).
  - Trust upgrades (e.g., request verified data sources).
- CET responds with updated context_id; IDE links both contexts in trace.

6.3 Ontology and Schema Alignment

- CET defines vocabularies for domains; IDE references them in rules and synthesis.
- Schema versioning:
  - Backward-compatible feature additions; deprecations coordinated via governance.
- Feature parity checks:
  - IDE can refuse to decide if mandatory features are missing or invalid.

6.4 Context Health Influence on Decisions

- Confidence adjustments based on:
  - Missingness patterns, stale data, conflicting sources.
  - CET health flags reduce maximum reachable confidence or raise thresholds for consultation/escalation.

7. Integration with the LLM Orchestra (Fiedler MAD)

7.1 Conversations, Not Service Calls

- DER converses with Fiedler, stating:
  - The decision context.
  - Hard constraints and safety invariants.
  - The question to answer and acceptable output schema.
- The conversation captures:
  - Multiple model perspectives; citations or reference knowledge; disagreements.

7.2 Consultation Types

- Expert Advice:
  - Ask for explanations and trade-offs in natural language, grounded in constraints.
- Option Ranking:
  - Request scored ranking among enumerated options.
- Hypothesis Testing:
  - Probe edge cases; request adversarial critiques against candidate decisions.
- Knowledge Gaps:
  - Ask for missing context items or unknown unknowns to inform re-transformation.

7.3 Aggregation Strategies in DER

- Weighted Borda or Condorcet-like methods for ranked options.
- Bayesian model averaging with priors from historical accuracy on related tasks.
- Dempster–Shafer theory for belief combination under uncertainty.
- Arbitration under constraints:
  - Discard any suggestion that violates invariants; penalize those close to boundaries.

7.4 Cost and Latency Controls

- Budget per decision type and risk tier.
- Use cached consultations for recurring contexts; timebox conversations.
- Fail-fast mode for low-risk, high-throughput decisions.

7.5 Safety and Privacy

- PII minimization in conversations.
- Mask sensitive attributes; use synthetic identifiers with access checks.
- Retain only hashes or redacted transcripts in traces when required by policy.

8. State Manager and Doing Engine Interactions

8.1 State Reads and Writes

- IDE reads:
  - Current commitments, resource availability, historical outcomes, operator preferences, and relevant external facts with timestamps.
- IDE writes:
  - Decision logs, proposed commitments (e.g., pre-allocation), and learning signals.
- Doing Engine enacts decisions and writes execution outcomes and side effects; IDE consumes them for learning and calibration.

8.2 Reproducibility

- Use time-travel reads with versioned state snapshots.
- Record state versions in trace; ensure replays reconstruct identical decision paths.

8.3 Transactionality

- For decisions that alter state before execution (e.g., reservations), use two-phase commits or sagas:
  - DER includes preconditions and compensations in the Decision Package.
  - Doing Engine ensures atomic application or compensating actions.

9. Hierarchical Paper Structure for the IDE Discipline

Act 1 — Foundations
- Paper 01: IDE Core Principles and Architecture
  - Formal definition, decision types, hybrid design rationale, safety profile.
- Paper 02: Rules Engine Design and Authoring
  - Representations, agenda control, conflict resolution, verification.

Act 2 — Decision Engineering Mechanics
- Paper 03: DER Internal Architecture
  - Gatekeeping, arbitration, synthesis, confidence, trace.
- Paper 04: Consultative Synthesis with LLM Orchestra
  - Conversation designs, aggregation, dissent management, safety filters.
- Paper 05: Confidence, Calibration, and Abstention
  - Methods, metrics, and operational policies across risk tiers.

Act 3 — Integration
- Paper 06: CET↔IDE Integration Patterns
  - Context contracts, re-transformation loops, ontology alignment.
- Paper 07: IDE↔State Manager and Doing Engine Contracts
  - Transactionality, reproducibility, and execution preconditions.
- Paper 08: Multi-Agent Decision Coordination
  - Protocols, consensus, negotiation, and capability discovery.

Act 4 — Advanced Topics
- Paper 09: Learning from Outcomes
  - Offline/online updates, rule distillation, counterfactual evaluation.
- Paper 10: Safety and Compliance
  - Formal verification, hazard analysis, safety cases, audit controls.
- Paper 11: Performance and Real-Time Optimization
  - Latency budgets, caching, prioritization under load.

Act 5 — Productionization
- Paper 12: Observability and Decision Monitoring
  - Tracing, dashboards, SLOs, incident response.
- Paper 13: Governance and Change Management
  - Approvals, rollbacks, versioning strategies, regulatory alignment.
- Paper 14: Reference Implementations and Case Studies
  - Hopper/Grace deployments; lessons learned; domain templates.

10. Implementation Roadmap

Phase 1 — Foundation (0–3 months)
- Minimal viable Rules Engine:
  - Decision tables and production rules; agenda; guardrails; explanations.
  - Integrate with OPA or Cedar for policy layers.
- DER v1:
  - Gatekeeper logic; synthesis over enumerated options; confidence via heuristics.
  - Fiedler conversation prototype; simple aggregation; trace v1.
- Integrate with CET v1 and State Manager v1.
- Deploy in Hopper and Grace:
  - Use low-risk decision domains first (e.g., routing, prioritization).
- Metrics: establish baselines (accuracy, latency, rule coverage, invocation rate).

Phase 2 — Refinement (3–6 months)
- Rules Engine:
  - Add decision trees; conflict analytics; property-based tests.
  - Formal safety properties; model checking for critical invariants.
- DER:
  - Calibration (isotonic/Platt); conformal sets where applicable.
  - Enhanced aggregation; dispersion-aware consensus; abstention policies.
  - Trace v2: graph form, signed and content-addressed.
- CET↔IDE loops: context health integration; re-transformation requests.
- Learning from outcomes v1:
  - Counterfactual evaluation; simple rule distillation proposals.
- Governance tools:
  - Rule authoring portal; change review workflows; incident playbooks.

Phase 3 — Advanced Capabilities (6–12 months)
- Multi-agent decision coordination:
  - Capability discovery; negotiation protocols; decision commitments.
- Real-time optimization under load:
  - Adaptive rate limits; cost-aware consultation; caching strategies.
- Safety and compliance:
  - Safety case templates; red-team harness; runtime monitors.
- Broaden to higher-risk domains with human-in-the-loop gating.

11. Metrics and Evaluation

11.1 Technical Metrics

- Decision accuracy: fraction of decisions judged correct by ground truth or post-hoc validation.
- Latency: end-to-end time from Context Package receipt to Decision Package emission; p50/p95 budgets by tier.
- Rule coverage: percentage of decisions fully handled deterministically.
- Consultation invocation rate: fraction of decisions that required LLM Orchestra.
- Confidence calibration:
  - ECE, Brier score, reliability curves.
- Selective prediction:
  - Coverage vs. risk curves; abstention rate and outcomes.

11.2 Auditability Metrics

- Trace completeness: proportion of decisions with fully reconstructible traces; missing artifacts rate.
- Explainability: human-rated clarity scores; time-to-understanding.
- Reproducibility: deterministic replays success rate; variance explainers.

11.3 System Metrics

- CET↔IDE correctness: schema mismatches; context health influence on decisions; re-transformation efficacy.
- Doing Engine success: decision-to-action success rate; postconditions met rate.
- Multi-MAD overhead: conversation counts, durations, and cost budgets adherence.

11.4 Calibration and Validation Methodology

- Offline backtesting with logged contexts and outcomes.
- Prospective A/B tests with shadow DER and alternative rulesets.
- Conformal validation for set-based decisions; measured coverage vs. target.

12. Governance, Safety, and Compliance

12.1 Policy Layering

- Layer order: Legal/jurisdictional → Safety invariants → Security/identity → Business policy → Preferences/heuristics.
- Strong dominance semantics: lower layers cannot override upper layers.

12.2 Safety Engineering

- Hazard analysis (STPA-style): identify unacceptable losses and control structures.
- Safety cases: structured arguments linking evidence (rules tests, verification, simulation) to safety claims.
- Runtime enforcement: invariant monitors, kill switches, and safe defaults.

12.3 Compliance and Audit

- Decision logs: append-only, content-addressed; retention aligned with regulation.
- Redaction/minimization: privacy by design for traces and conversations.
- External audits: export sanitized traces and verification reports.

12.4 Change Management

- Approved change windows; feature flags for new rules.
- Automatic impact analysis: simulate top decision cohorts.
- Rollback plans baked into deployment manifest.

13. Reference Implementation Plan

13.1 Language and Stack

- Core IDE library in a memory-safe, performant language (Rust or Go) with Python bindings for experimentation.
- Rules Engine:
  - Decision tables/trees compiled to Rust/Go; production rules with efficient matcher.
  - OPA/Cedar integration via adapters; formal specs integrated via external tools.
- DER:
  - Modular orchestration with plugin interfaces for aggregation and calibration.
  - Conversation client for Fiedler; content-addressable trace store (e.g., CAR/IPLD).
- CET and State Manager integration via conversations mediated by MAD runtime.

13.2 Repository Structure (Joshua)

- /ide-core: core libraries for Rules Engine and DER.
- /ide-adapters: OPA/Cedar, Drools/CLIPS, Prolog/ASP connectors.
- /ide-calibration: calibration and conformal modules.
- /ide-trace: trace graph schema and storage drivers.
- /ide-examples: Hopper/Grace deployments; decision templates.
- /ide-tools: authoring portal, rule linters, coverage/conflict analyzers.

13.3 CI/CD and Quality

- Unit and property-based testing; golden fixtures; snapshot tests for traces.
- Verification step optional but encouraged for critical domains.
- Benchmarks for latency and throughput; load testing profiles.
- Security review of conversations and data handling.

13.4 Example Decision Templates

- Approval Gate: enforce policy constraints and escalate on novelty.
- Routing and Prioritization: multi-objective scoring with abstention.
- Parameter Selection: bounded optimization with conformal sets.
- Rollout Plan Selection: staged deployment with safety monitors.

14. Domains and Case Studies

14.1 MLOps and Software Delivery

- Decisions: approve deploy, choose rollout strategy, trigger rollback.
- Rules: require approvals, test coverage thresholds, rollback plans.
- DER: synthesize rollout blast radius given traffic and risk; consult for anomaly risk predictions.

14.2 Customer Support and Ticket Routing

- Decisions: route to team; prioritize SLA-risk tickets.
- Rules: entitlement checks, SLA clocks, jurisdiction routing.
- DER: weigh agent load, skill match, historical resolution rates.

14.3 Healthcare Triage (with strict oversight)

- Decisions: prioritize patient reviews; suggest safe diagnostic next steps.
- Rules: safety limits, contraindications, jurisdictional compliance.
- DER: consult for differential diagnoses; abstain liberally; escalate to clinicians.

14.4 Finance and Risk Controls

- Decisions: approve transactions; set credit limits; flag anomalies.
- Rules: KYC/AML policies; thresholds; regional laws.
- DER: combine anomaly scores with policy context; conformal flag sets.

14.5 Operations and Resource Allocation

- Decisions: schedule jobs; allocate compute; set rate limits under cost caps.
- Rules: budget ceilings, fairness constraints.
- DER: cost-performance trade-offs; consult for predicted demand spikes.

14.6 Education and Personalized Learning (low-risk)

- Decisions: recommend next learning activity.
- Rules: learning objectives, prerequisites.
- DER: synthesize engagement and mastery predictions; set-based recommendations.

15. Multi-Agent Decision Coordination

15.1 Capability Discovery and Invitations

- MADs advertise capabilities via registries and conversations (e.g., “Can provide demand forecast under constraints C.”).
- DER can invite other MADs to contribute opinions or sub-decisions.

15.2 Coordination Patterns

- Contract Net:
  - DER broadcasts a call for proposals; interested MADs return bids with confidence, cost, and SLAs.
  - DER adjudicates under constraints and chooses a winning proposal or ensemble.
- Consensus for Shared State:
  - For joint decisions affecting shared resources, use conversation-driven consensus similar to Paxos/Raft semantics but human-readable:
    - Propose → Promise → Accept → Commit dialogues with timeouts and fallbacks.
- Argumentation Frameworks:
  - Encourage structured pro/con arguments; DER scores argument strength subject to constraints.

15.3 Consistency, Safety, and Accountability

- Commitments:
  - Decision commitments recorded in State Manager with clear owners and compensations.
- Safety:
  - Hard invariants applied locally and globally; monitor for cross-agent conflicts.
- Accountability:
  - Each MAD’s contribution is traceable; decisions carry authorship and capability IDs.

16. Research Questions and Open Problems

1) Rules Engine Design
- What hybrid of decision tables, production rules, and policy engines yields the best clarity, performance, and verifiability in MAD contexts?
- How to represent and merge layered policies with strong dominance semantics while preserving manageability?

2) DER Architecture
- Optimal gating criteria between deterministic adoption, synthesis, and consultation by risk tier and decision type?
- Which aggregation methods best combine multi-model advice under constraints with interpretable trade-offs?

3) Confidence Scoring
- How to achieve practically calibrated confidence across heterogeneous decision types?
- When do conformal methods provide superior guarantees, and how to integrate abstention policies operationally?

4) Learning Mechanisms
- What pipeline best distills stable rules from DER traces and outcomes? How to prevent overfitting and maintain policy compliance?
- How to perform counterfactual evaluation of alternative rulesets safely?

5) Multi-Agent Decisions
- Which conversation protocols ensure efficiency and fairness when MADs jointly decide?
- How to encode and enforce cross-agent safety invariants and resolve conflicts?

6) Formal Verification
- Which formal methods scale to real-world rulesets with temporal and deontic constraints?
- How to integrate model checking into CI without undue burden?

7) Paper Structure
- Is the 14-paper arc optimal, or should advanced topics be merged/split after initial feedback from Hopper/Grace deployments?

8) Novel Contributions
- How to empirically demonstrate IDE’s unique impact on auditability, calibration, and governance vs. expert systems and black-box ML?

9) Validation Strategy
- Beyond Hopper/Grace: establish benchmarks and open datasets for decision engineering (e.g., policy-rich MLOps approvals, multi-objective routing, compliance-heavy triage).

10) Real-World Applicability
- Which domains with regulatory constraints benefit first? What operator training and governance patterns are needed for adoption?

17. Publication Strategy

17.1 Venues

- Core AI and decision venues: AAAI, IJCAI, ICAPS.
- Safety and interpretability: SafeAI, XAI workshops, NeurIPS D&B tracks.
- Multi-agent systems: AAMAS.
- Software engineering and ops: ICSE, SREcon, MLSys (for MLOps case studies).

17.2 Timeline

- Paper 00 (this): Council synthesis as foundation.
- Papers 01–03 (6 months): core architecture, Rules Engine, DER internals.
- Papers 04–08 (12 months): consultations, calibration, CET/State integration, multi-agent coordination.
- Papers 09–14 (18 months): learning, safety/compliance, performance, production case studies.

17.3 Open Source Strategy

- Reference implementation in Joshua repository with permissive license.
- Integration examples with ICCM CET and MAD runtime.
- Hopper and Grace deployments as living case studies with redacted traces and metrics.
- Community contributions: rule libraries, calibration recipes, trace inspectors.

18. Glossary and Appendices

18.1 Glossary

- MAD: Machine-Agency Device; a conversational agent assembling capabilities.
- Capability: A MAD’s advertised function accessible via conversations.
- Conversation: Dialogic exchange between MADs; replaces service calls.
- Thinking Engine: CET (ICCM) + Rules Engine (IDE) + DER (IDE) + State Manager (MAD).
- Doing Engine: Domain-specific execution component acting on decisions.
- CET: Context Engineering Transformer; structures and validates decision context.
- Rules Engine: Deterministic evaluator of rules, policies, and safety invariants.
- DER: Decision Engineering Recommender; synthesizes decisions with confidence and trace.
- LLM Orchestra: Fiedler MAD’s capability for multi-model consultation.
- State Manager: Memory and world state component supporting reproducibility and audit.

18.2 Minimal Schemas (Illustrative JSON-like)

- Context Package:
  - {
      "context_id": "...",
      "task_id": "...",
      "timestamp": "...",
      "provenance": {"sources": [...], "signatures": [...]},
      "trust_level": "verified|unverified|mixed",
      "actor_profile": {...},
      "risk_tier": "T0|T1|T2|T3",
      "objectives": [{"name": "...", "weight": 0.3}, ...],
      "constraints": [{"name": "max_cost", "value": 1000, "unit": "USD"}, ...],
      "features": [{"name": "latency_p95", "value": 120, "unit": "ms", "ontology": "perf.latency"}, ...],
      "environment": {...},
      "safety_profile": {...},
      "health": {"freshness_ok": true, "missing": [], "warnings": []}
    }

- Rule Decision Package:
  - {
      "rule_matches": [
        {"rule_id": "POL-SAFE-001", "version": "1.2.3", "priority": 100,
         "action": {"name": "deny", "params": {"reason": "dose_limit_exceeded"}},
         "mandatory": true}
      ],
      "conflicts": [],
      "guardrails_triggered": [],
      "coverage": 0.82,
      "confidence_rule": 0.95,
      "residuals": [{"name": "rate_limit", "range": [50, 100], "unit": "rps"}]
    }

- Decision Package:
  - {
      "decision_id": "...",
      "task_id": "...",
      "decision_type": "approve|deny|choose|plan",
      "selected_action": {"name": "rollout_canary", "params": {"percentage": 10}},
      "confidence": 0.91,
      "rationale": "Policy POL-DEP-010 satisfied. Safety margin 2x. Similar contexts succeeded.",
      "trace_ref": "bafy...hash",
      "alternatives": [
        {"action": {"name": "rollout_shadow"}, "confidence": 0.88, "tradeoffs": "lower blast radius; slower feedback"}
      ],
      "safety_assertions": ["rollback_ready", "monitoring_active"],
      "consultation_digest": {"invoked": true, "consensus": 0.7, "models": ["gpt-x", "opus-y"]},
      "versions": {"DER": "0.3.0", "Rules": ["1.2.3","0.9.1"], "CET": "0.4.2"}
    }

- Execution Outcome Package:
  - {
      "decision_id": "...",
      "outcome": "success|failure|partial",
      "telemetry": {"latency_p95": 110, "error_rate": 0.2},
      "exceptions": [],
      "realized_costs": {"usd": 35.2},
      "postconditions_met": true,
      "drift_signals": [],
      "operator_feedback": {"useful": true, "notes": "Good canary choice"}
    }

18.3 Example Rule Layers

- Legal/Safety:
  - Never disclose PII without consent; never exceed pharmacological bounds; require approvals for prod changes.
- Security/Identity:
  - Restrict actions by entitlements; enforce multi-factor approvals.
- Business:
  - Budget ceilings; target latency; customer tier prioritization.
- Preferences/Heuristics:
  - Preferred vendors; default strategies; tie-breakers.

18.4 Example DER Aggregation

- Weighted Borda:
  - Assign weights w_i to model i based on rolling accuracy; sum rank scores; choose top score under constraints.
- Dempster–Shafer:
  - Combine belief masses for options; discount conflicting evidence; abstain if conflict mass exceeds threshold.

18.5 Safety Case Skeleton

- Claim: Approvals for prod deployments maintain risk below R with probability ≥ p.
- Evidence:
  - Verified rules: POL-DEP-001..010.
  - DER calibration ECE < 0.05 on similar contexts.
  - Red-team simulations; rollback success rate > 99%.
- Argument:
  - Policy dominance ensures invariants; DER abstains under uncertainty; Doing Engine enforces preconditions.

Closing

IDE formalizes decision-making as a discipline that is transparent, auditable, controllable, adaptive, and confident. It delivers the Rules Engine and DER components that complete the MAD Thinking Engine when combined with CET (from ICCM) and State Manager. The hybrid architecture—deterministic where it must be, probabilistic where it should be—anchors safety and agility within the same system. By privileging conversations and capabilities, IDE also enables multi-agent decision coordination that is inspectable and governable. This Paper 00 establishes the foundations, architecture, and path to production, and invites the Council to refine the proposed paper arc, implementation roadmap, and validation program across Hopper, Grace, and beyond.