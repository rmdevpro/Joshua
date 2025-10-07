Paper 00: The MAD Ecosystem — Master Document v2.0

Version: Draft v2.0 for Council of Elders Review
Date: 2025-10-06
Status: Synthesis for Council Review
Repository: Joshua (MAD ecosystem)
Purpose: Present the corrected trinity, position MAD as the Agent Assembly discipline, and integrate ICCM Paper 00 (Context Engineering) and IDE Paper 00 (Decision Engineering) into a unified architecture for assembling complete agents.

Executive Summary

- MAD is the Agent Assembly discipline. It completes the trinity by integrating components from ICCM (Context Engineering) and IDE (Decision Engineering) into complete agents with clear separation of Thinking and Doing.
- The MAD Thinking Engine comprises four components from three disciplines:
  - CET (ICCM): context transformation
  - Rules Engine (IDE): deterministic decision-making and policy enforcement
  - DER (IDE): synthesis for ambiguous or novel decisions
  - State Manager (MAD): memory and world model
- The Doing Engine is the domain-specific execution layer that enacts decisions and returns outcomes to the State Manager for learning and audit.
- Half-MADs provide shared capabilities through conversations. Full MADs use these capabilities and embody the complete Thinking and Doing architecture.
  - Half-MADs: Fiedler (LLM Orchestra), Dewey (conversation storage), Godot (observability), Marco (MCP proxy), Horace (file catalog), Gates (document generation), Playfair (diagram generation)
  - Full MADs: Hopper (autonomous development), Grace (intelligent system UI)
- LLM Orchestra is a universal capability provided by Fiedler (a Half-MAD). Any component can converse with Fiedler. It is not owned by any single discipline.
- MAD Papers 01–14 specify core architecture, the State Manager, Doing Engines, CET/Rules/DER integration, Half-MADs, multi-MAD collaboration, testing, observability, and case studies (Hopper, Grace).
- All interactions between MADs are conversations. MADs expose capabilities. Terms like service call, API request, or infrastructure are deprecated.
- This document assumes familiarity with ICCM Paper 00 and IDE Paper 00.

1. Introduction: The MAD Ecosystem

1.1 What is the MAD Ecosystem?

MAD (Multipurpose Agentic Duo) is a cognitive agent architecture with a principled separation between Thinking and Doing. MAD is a discipline for Agent Assembly: it composes agents from:
- ICCM’s Context Engineering Transformer (CET)
- IDE’s Rules Engine and Decision Engineering Recommender (DER)
- MAD’s State Manager and Doing Engine, with integration patterns that unify the whole.

Key innovations:
- Separation of concerns: Thinking decides; Doing executes.
- Transparent, auditable, controllable agents through explicit state and decision provenance.
- Ecosystem composition via conversations among Full MADs and Half-MADs, each offering capabilities.

1.2 The Trinity of Disciplines

The trinity provides the conceptual and technical foundation for reliable agents:

- ICCM (Context Engineering)
  - Repository: ICCM
  - Discipline: Transform raw input into decision-ready context
  - Output: CET
  - Contribution: Thinking Engine component #1 (context transformation)
  - Reference: ICCM Paper 00 and follow-on papers

- IDE (Decision Engineering)
  - Repository: Joshua/IDE
  - Discipline: Make transparent, auditable, hybrid decisions
  - Outputs: Rules Engine (deterministic), DER (synthesis)
  - Contribution: Thinking Engine components #2–3 (decision making)
  - Reference: IDE Paper 00 and follow-on papers

- MAD (Agent Assembly)
  - Repository: Joshua/MAD
  - Discipline: Assemble complete agents
  - Outputs: State Manager (Thinking Engine component #4), Doing Engine patterns, integration, complete MADs
  - Reference: this Paper 00 and MAD Papers 01–14

Relationship:
- ICCM Paper 00 and IDE Paper 00 define components that MAD consumes and integrates.
- MAD’s Paper 00 defines how to assemble these components into complete agents, adding the State Manager and Doing Engine.

1.3 Why Dual-Engine Architecture Matters

Separation of Thinking and Doing gives:
- Clarity: Decisions are formed through CET → Rules Engine → DER with State Manager support; execution is handled by the Doing Engine.
- Testability: Decision logic and execution logic can be validated independently and together.
- Auditability: State Manager records context, decisions, and outcomes; reproducibility is enabled via time-travel reads and deterministic rules.
- Safety: Rules Engine enforces policies; DER produces reasoned recommendations; Doing Engine applies safeguards for irreversible actions.
- Composability: The same Thinking Engine can drive different Doing Engines; Half-MADs provide shared capabilities through conversations.

1.4 Half-MADs vs Full MADs

Half-MADs:
- Minimal or incomplete Thinking Engine; provide focused capabilities to other MADs via conversations.
- Examples and capabilities:
  - Fiedler: LLM Orchestra (multi-model consultation and synthesis)
  - Dewey: Conversation storage and retrieval
  - Godot: Logging, tracing, observability
  - Marco: MCP conversation proxy and routing
  - Horace: File catalog, indexing, versioning
  - Gates: Document generation and formatting (e.g., Markdown to ODT)
  - Playfair: Diagram generation (e.g., Mermaid, Graphviz)
- Evolution: Each Half-MAD is a candidate to become a Full MAD by adopting the complete Thinking Engine and a Doing Engine suited to its domain.

Full MADs:
- Complete Thinking Engine (CET + Rules + DER + State Manager) plus a Doing Engine.
- Examples:
  - Hopper: Autonomous development agent (code synthesis, execution, testing)
  - Grace: Intelligent system UI agent (interaction management, orchestration of capabilities)
- They converse with Half-MADs to invoke capabilities such as LLM Orchestra and logging.
- They maintain robust internal state and provide audit-friendly outcomes.

MAD-to-MAD interactions:
- Always conversations, never service calls.
- MADs expose and invoke capabilities.
- All conversations conform to MCP or a MAD-aligned conversation protocol.

1.5 Document Organization

- Section 2: Theoretical foundation and the full Thinking Engine specification.
- Section 3: Complete MAD architecture, State Manager, integration boundaries, and data contracts.
- Section 4: The MAD hierarchical paper structure (14 papers).
- Section 5: Implementation roadmap for Hopper and Grace and the ecosystem.
- Section 6: Success metrics for Thinking, Doing, integration, and ecosystem.
- Section 7: Relationship to ICCM and IDE.
- Section 8: Half-MAD specifications.
- Section 9: Publication strategy.
- Section 10: Research questions.
- Section 11: Case studies (Hopper and Grace).
- Section 12: Governance, versioning, and compliance.
- Section 13: Security, safety, and ethics.
- Conclusion and Appendix with terminology and reference patterns.

2. Theoretical Foundation

2.1 Cognitive Architecture Principles

- Two-System perspective:
  - Fast, pattern-based judgments (augmented by LLM-assisted synthesis where suitable).
  - Deliberative, rule-governed reasoning (explicit Rules Engine) and structured synthesis (DER).
- Explicit state:
  - Decisions and executions reference the same world model and memories through the State Manager.
- Modular integration:
  - Components of the Thinking Engine are independent yet coordinated via well-defined interfaces.
- Transparency:
  - Reasoning traces, rules hits/misses, and synthesis rationales are recorded and inspectable.
- Composable execution:
  - The Doing Engine enacts decisions and provides outcomes; Think-Do feedback continuously improves performance.

2.2 The Thinking Engine: Complete Specification

Composition:
- Component 1: CET (ICCM)
  - Responsibility: Transform raw inputs into structured, decision-ready context.
  - Typical operations: parsing, normalization, classification, routing, summarization, conflict resolution, deduplication.
  - Inputs: raw user utterances, sensor streams, documents, system events.
  - Outputs: context packages; pointers to relevant episodic/semantic memories.
  - References: ICCM Paper 00 (core), ICCM Papers 01–03 (patterns and validation).
- Component 2: Rules Engine (IDE)
  - Responsibility: Deterministic decisions in known scenarios; policy enforcement; safety guardrails.
  - Typical operations: rule matching, constraint checking, escalation triggers, compliance validation.
  - Inputs: context packages, state snapshots, policy sets.
  - Outputs: decisions, policies applied, rationale, required escalations.
  - References: IDE Paper 00, IDE Papers 01–02.
- Component 3: DER (IDE)
  - Responsibility: Synthesis in ambiguous or novel scenarios; hybrid decision-making.
  - Typical operations: hypothesis generation, option ranking, confidence calibration, cost-quality tradeoffs.
  - Inputs: rules outputs (including escalations), enriched context, relevant memories.
  - Optional: conversation with Fiedler for LLM Orchestra consultation.
  - Outputs: decision recommendations, rationale, confidence, alternatives considered.
  - References: IDE Paper 00, IDE Papers 03–05.
- Component 4: State Manager (MAD)
  - Responsibility: Memory and world model management across Thinking and Doing.
  - Memory strata:
    - Episodic: chronological records of conversations, decisions, executions, outcomes.
    - Semantic: structured domain knowledge and learned associations.
    - Working: active context and task-local variables.
    - World model: current representation of the environment, resources, and constraints.
  - Features:
    - Read/write interfaces for CET, Rules, DER, and Doing Engine.
    - Append-only decision logs for audit.
    - Time-travel reads for reproducibility.
    - Integration via conversations with Dewey (storage), Godot (observability), Horace (catalog).
  - References: MAD Papers 02–03.

Operational flow:
- Input arrives. CET transforms it into a structured context package.
- Rules Engine evaluates policies and determines deterministic actions or escalations.
- DER synthesizes decisions where rules defer or augment; may consult Fiedler’s LLM Orchestra via conversation.
- State Manager is read and updated across all steps; contextualizes decisions and records provenance.
- Decision package is emitted to the Doing Engine.

2.3 The Doing Engine: Domain-Specific Execution

Definition:
- Executes decisions produced by the Thinking Engine; interacts with external systems; reports outcomes to State Manager.

Characteristics:
- Receives well-formed decision packages with constraints and plans.
- Applies execution safeguards (preconditions, dry-run modes, human-in-the-loop gates).
- Produces execution reports, including results, errors, timings, and side effects.
- Can converse with Half-MADs for specialized capabilities (e.g., code synthesis from Fiedler).
- Is swappable; different Doing Engines can connect to the same Thinking Engine depending on domain.

Patterns:
- Tool execution:
  - CLI and file operations, compilers, linters, test runners (Hopper).
- API orchestration:
  - Web and backend orchestration, DB operations, messaging, cloud resources (Grace).
- Human interaction:
  - UI rendering, confirmations, feedback loops, preference collection.
- Hybrid execution:
  - Combination of tools, APIs, and interaction patterns.

Feedback:
- Doing Engine sends execution reports to the State Manager.
- State Manager updates episodic memory and, where appropriate, semantic memory and world model.
- DER and Rules Engine can leverage updated state in subsequent cycles.

2.4 LLM Orchestra as Universal Capability

- Fiedler provides the LLM Orchestra capability: multi-model consultation across GPT, Claude, Gemini, Grok, and others.
- Any component can converse with Fiedler:
  - CET can request ambiguity resolutions or taxonomic classification under constraints.
  - DER can request brainstorming or multi-model synthesis with cost-quality tradeoff guidance.
  - Doing Engine can request code generation, refactoring, migration frameworks, or transformation pipelines.
- Ownership and access:
  - LLM Orchestra is not owned by any discipline or component; it is a shared capability.
  - Access is mediated by conversations adhering to MCP-compatible patterns.
- Conversation pattern:
  - Initiator sends a prompt bundle: context snapshot, constraints, expected format, budget/time constraints.
  - Fiedler responds with a synthesized proposal, alternatives, model-specific confidence, and tradeoff notes.
  - Initiator incorporates results and records the rationale in the State Manager.

3. Complete MAD Architecture

3.1 Full MAD Structure

High-level structure:
- Thinking Engine: CET → Rules Engine → DER while reading/writing state via the State Manager.
- Doing Engine: executes decision package; reports outcomes to the State Manager.
- Conversations with Half-MADs: invoked as needed for capabilities (LLM Orchestra, logging, storage, cataloging, formatting, diagramming, MCP proxy).
- All internal and external communications are conversations; no service calls.

Lifecycle:
- Receive input.
- CET produces context package.
- Rules Engine applies policies and constraints.
- DER synthesizes a decision package, optionally after consulting Fiedler.
- State Manager updates across steps; records provenance.
- Doing Engine enacts decisions; outcomes flow back to State Manager.
- Agent learns and adapts via state updates.

3.2 State Manager Specification

Purpose:
- Provide the shared memory fabric and world model necessary for coherent, reproducible, and auditable thinking and doing.

Core elements:
- Episodic memory:
  - Immutable, append-only record of conversations, decisions, execution reports, and external events.
  - Supports queries by time, topic, task, and actor.
- Semantic memory:
  - Domain ontology, policies, schemas, entities, relationships, embeddings or indexes for efficient recall.
  - Supports updates from learning loops and curation from Rules Engine decisions.
- Working memory:
  - Short-lived context and variables; current task frame; scratchpads for current decisions.
  - Managed with size/time limits; checkpointed when tasks become long-lived.
- World model:
  - External state representation: resources, environment, dependency graphs, capabilities catalogue, current constraints.

Interfaces:
- Read APIs for CET, Rules, DER, Doing Engine:
  - Get snapshots, retrieve relevant episodes and facts, fetch active constraints.
- Write APIs:
  - Append decision logs, record execution outcomes, promote learned facts to semantic memory.
- Time-travel and reproducibility:
  - Read consistent snapshots at specific decision points.
  - Re-run decisions on historical state for diagnostics and trust calibration.

Conversations with Half-MADs:
- Dewey (storage/retrieval):
  - Persist episodic records; index and retrieve by multi-key queries.
- Godot (observability):
  - Emit structured logs, traces, metrics; correlate across MADs.
- Horace (file catalog):
  - Maintain file inventories, dependencies, version maps; link artifacts to decision provenance.
- Marco (MCP proxy):
  - Bridge to external MCP domains; route and monitor cross-domain conversations.

Constraints and policies:
- The State Manager enforces data retention, privacy, and access policies defined by Rules Engine policies and MAD governance.
- Utilization quotas and rate limits for external capability conversations (e.g., Fiedler) are tracked here.

3.3 Integration Boundaries

ICCM to MAD:
- Artifact: CET component and integration guidelines.
- Contract:
  - Input: raw input bundle (utterance, actor metadata, environment snapshot).
  - Output: context package (normalized fields, classification, routing hints, references to state).
  - Error handling: ambiguity flags, disambiguation prompts, and fallback strategies.
- MAD responsibilities:
  - Provide State Manager access; ensure CET can read necessary episodic/semantic context and write context indexes.

IDE to MAD:
- Artifacts: Rules Engine and DER specifications and reference implementations.
- Contracts:
  - Rules Engine input: context package, state snapshot, policy set, constraints.
  - Rules Engine output: policy-compliant decision or escalation directive; rule hits/misses; rationale.
  - DER input: rules outputs, enriched context, relevant memories, optional LLM Orchestra responses.
  - DER output: decision package (intent, plan, constraints, confidence, rationale, alternatives).
- MAD responsibilities:
  - Provide State Manager access; enforce trace and audit requirements; manage conversation budgets to Fiedler when DER consults LLM Orchestra.

MAD to Half-MADs:
- Interface: conversations over MCP.
- Capability invocation pattern:
  - Prepare capability request with a context pointer, constraints, and expected output schema.
  - Send conversation turn to the Half-MAD.
  - Receive capability response; validate schema; record in State Manager with provenance.

3.4 Data Contracts and Schemas

Context package (CET output):
- Fields:
  - context_id
  - normalized_input (text, structured, or both)
  - classification (intent candidates, confidence)
  - routing hints (target domains or policies)
  - references to state (episodic keys, semantic entities)
  - ambiguity markers and suggested clarifications
  - timestamps and provenance

Decision package (DER output, possibly augmented by Rules Engine):
- Fields:
  - decision_id
  - intent and scope
  - plan outline and constraints (permissions, resource budgets, safety modes)
  - policy compliance summary (rules applied, exceptions)
  - confidence and rationale
  - alternatives considered and why rejected
  - required confirmations (human or MAD)
  - expected outputs and verification checks
  - timestamps and provenance (including any LLM Orchestra consultations)

Execution report (Doing Engine output):
- Fields:
  - decision_id linkage
  - actions taken and tool/APIs used (described as capabilities invoked)
  - results, artifacts produced, side effects
  - errors and mitigations
  - verification outcomes (tests, validations)
  - resource usage and timing
  - next-step recommendations
  - timestamps and provenance (including Half-MAD conversations)

3.5 Safety and Escalation

- Rules Engine acts as the first line of safety: permissions, policy constraints, environment checks.
- DER performs risk assessment: confidence, uncertainty quantification, mitigation strategies.
- Doing Engine applies execution guardrails: dry-run, staged rollout, human confirmation.
- Escalations:
  - Human-in-the-loop confirmations for sensitive operations.
  - Fallback to safer alternatives or deferral with explanation.
- Recordkeeping:
  - All escalations and confirmations recorded in State Manager.

4. Hierarchical Paper Structure (14 Papers)

Act 1 — Foundations
- Paper 01: MAD Core Architecture and Agent Assembly Discipline
  - MAD as the integrator of ICCM and IDE; Thinking vs Doing; conversations and capabilities.
- Paper 02: State Manager Specification
  - Episodic, semantic, working memory, world model; interfaces; policies; time-travel.
- Paper 03: Doing Engine Patterns and Domain-Specific Execution
  - Tool execution, API orchestration, human interaction, hybrids; safety.

Act 2 — MAD Integration
- Paper 04: Integrating CET (ICCM) into MAD Thinking Engine
  - Contracts, schemas, routing, ambiguity handling.
- Paper 05: Integrating Rules Engine and DER (IDE) into MAD Thinking Engine
  - Decision pipelines, escalations, policy enforcement, synthesis.
- Paper 06: Thinking Engine ↔ Doing Engine Conversations
  - Decision package handoffs; execution reports; verification loops.

Act 3 — MAD Ecosystem
- Paper 07: Half-MADs — Capabilities and Patterns
  - Fiedler, Dewey, Godot, Marco, Horace, Gates, Playfair.
- Paper 08: MAD-to-MAD Conversations and Capability Invocation
  - MCP patterns, provenance, budgets, error handling.
- Paper 09: LLM Orchestra Integration Patterns
  - When and how to consult Fiedler; cost-quality tradeoffs; reproducibility.

Act 4 — Advanced Topics
- Paper 10: Multi-MAD Coordination and Collaboration
  - Joint planning, role assignment, conflict resolution, shared state.
- Paper 11: MAD Testing and Validation Frameworks
  - Unit, integration, scenario, regression; synthetic benchmarks; golden traces.
- Paper 12: MAD Observability and Debugging
  - Telemetry, tracing across MADs, time-travel debugging, incident response.

Act 5 — Production and Case Studies
- Paper 13: Hopper — Autonomous Development MAD Case Study
  - End-to-end trace; decision-to-execution loops; performance metrics.
- Paper 14: Grace — Intelligent System UI MAD Case Study
  - UI patterns; multi-capability orchestration; human-in-the-loop design.

5. Implementation Roadmap

Phase 1: Foundations (Hopper and Grace)
- Deliver complete Thinking Engine:
  - Integrate CET (ICCM), Rules Engine and DER (IDE), State Manager (MAD).
- Implement Doing Engines:
  - Hopper: tools, file ops, build/test harness, code execution sandboxes.
  - Grace: web UI orchestration, backend integration, session management.
- Validate conversations with key Half-MADs:
  - Fiedler (LLM Orchestra), Dewey (storage), Godot (observability).
- Demonstrate full lifecycle:
  - From input to decision to execution to learning; publish reproducible traces.

Phase 2: Ecosystem Maturity
- Expand Half-MAD capabilities and reliability:
  - Marco (MCP proxy), Horace (catalog), Gates (doc generation), Playfair (diagramming).
- Enhance State Manager:
  - Learning feedback loops; policy-aware retention and summarization.
- Multi-MAD coordination:
  - Role assignment, consensus formation, shared task boards.
- Testing and validation tooling:
  - Scenario harnesses, mutation testing for rules, DER stress tests.

Phase 3: Production Scale
- Upgrade select Half-MADs to Full MADs:
  - Add complete Thinking Engines where autonomy is beneficial (e.g., Horace managing catalogs).
- Advanced observability:
  - Cross-MAD trace stitching; anomaly detection; SLOs for decision quality and latency.
- Deployment patterns:
  - High-availability MAD clusters; capability pooling; governance and change management.
- Community templates:
  - Reference blueprints, contracts, and patterns for building Full MADs.

6. Success Metrics

Thinking Engine metrics:
- Context quality (CET): classification accuracy, ambiguity reduction, context completeness.
- Rule coverage and correctness: rules hit rate, false positives/negatives, policy drift detection.
- DER synthesis quality: decision accuracy, confidence calibration, diversity of alternatives.
- State Manager effectiveness: recall precision, latency, memory footprint, reproducibility success rate.

Doing Engine metrics:
- Execution success and reliability: success rate, rollback efficacy, error taxonomy.
- Latency and throughput: decision-to-execution delay, task completion time.
- Verification outcomes: test pass rates, post-execution invariants, defect density reductions.
- Domain-specific KPIs: for Hopper (compile/test success, code quality), for Grace (task success, UX feedback).

Integration metrics:
- Thinking ↔ Doing handoff: latency, correctness of contract adherence.
- Decision-to-execution conversion: rate of executed decisions without escalation failures.
- End-to-end completion: task success per budget/time constraints.
- Audit trail completeness: percentage of decisions with full provenance and re-run capability.

Ecosystem metrics:
- Half-MAD capability availability: uptime, response latency, budget adherence.
- MAD-to-MAD conversation overhead: tail latencies, timeouts, retry rates.
- LLM Orchestra utilization: cost-quality tradeoffs, consult frequency by component.
- Observability coverage: trace completeness across interactions.

7. Relationship to ICCM and IDE

MAD’s role:
- MAD consumes CET (ICCM) and Rules Engine + DER (IDE) and integrates them with the MAD State Manager and Doing Engine to produce complete agents.

From ICCM to MAD:
- MAD implements CET integration as per ICCM guidelines; ensures CET has state access and records context provenance.
- MAD adopts ICCM’s context schemas and error handling patterns.

From IDE to MAD:
- MAD integrates the Rules Engine for policy governance and DER for synthesis; implements audit logs and rationale capture.
- MAD aligns with IDE’s decision package schemas and supports reproducibility and human-in-the-loop escalation.

MAD’s contributions:
- State Manager specification and implementation.
- Doing Engine patterns and safety guardrails.
- Agent assembly blueprints, integration contracts, and reference implementations (Hopper, Grace).
- Ecosystem collaboration patterns (MAD-to-MAD conversations).

Reading order:
- ICCM Paper 00 → IDE Paper 00 → MAD Paper 00.

8. Half-MAD Specifications

General characteristics:
- Provide focused capabilities through conversations.
- Maintain minimal internal state; delegate durable storage and audit to Dewey and Godot.
- Follow capability contracts and schemas; record provenance.

Fiedler (LLM Orchestra):
- Capability: multi-model consultation and synthesis; cost-quality tradeoff analysis; reasoning traces when available.
- Conversation protocol:
  - Request fields: prompt bundle, constraints (budget/time), requested structure, provenance requirements.
  - Response fields: synthesized answer, alternative candidates, model rationales, confidence estimates, cost usage.
- Integration patterns:
  - DER consult for ambiguous decisions; Doing Engine requests code generation or transformation.
- Evolution path:
  - Full MAD potential: add CET for prompt structuring, Rules for guardrails on prompts, DER for meta-synthesis, State Manager for knowledge accumulation.

Dewey (Conversation Storage and Retrieval):
- Capability: durable storage of episodic records; rich retrieval and indexing.
- Protocol:
  - Store: record with keys (context_id, decision_id), categories, redaction tags.
  - Retrieve: parameterized queries; returns record bundles with integrity checks.
- Evolution path:
  - Full MAD potential: add DER for autonomous summarization, retention decisions, and legal compliance suggestions.

Godot (Observability: Logging and Tracing):
- Capability: structured logs, traces, metrics; correlation IDs across MAD conversations.
- Protocol:
  - Ingest: event with severity, context pointers, and span attributes.
  - Query: retrieve traces for debugging and compliance.
- Evolution path:
  - Full MAD potential: anomaly detection, autonomous incident management.

Marco (MCP Proxy):
- Capability: route conversations across domains; normalize schemas; enforce access policies.
- Protocol:
  - Proxy request: source MAD, target capability, constraints, schema mapping.
  - Response: proxied conversation transcript and results.
- Evolution path:
  - Full MAD potential: intelligent routing via Rules and DER; dynamic policy negotiation.

Horace (File Catalog and Versioning):
- Capability: authoritative catalog of artifacts; dependency graphs; version lineage.
- Protocol:
  - Register: artifact metadata; links to decisions and executions.
  - Query: dependency resolution; impact analysis.
- Evolution path:
  - Full MAD potential: proactive refactoring suggestions and storage optimization decisions.

Gates (Document Generation and Formatting):
- Capability: transform structured content into presentation formats; style and tone control.
- Protocol:
  - Input: semantic structure and style constraints.
  - Output: formatted documents; diffs vs previous versions.
- Evolution path:
  - Full MAD potential: autonomous publishing pipelines and style rule learning.

Playfair (Diagram Generation):
- Capability: produce diagrams from structured descriptions; maintain diagram lineage.
- Protocol:
  - Input: diagram spec; layout constraints.
  - Output: renderings and source; links to originating decisions.
- Evolution path:
  - Full MAD potential: layout optimization and design policy enforcement.

9. Publication Strategy

Primary venues:
- ICSE, FSE for software engineering.
- AAMAS, AAAI for agent systems.

Secondary venues:
- NeurIPS, ICLR for ML aspects of LLM Orchestra integration.
- CHI for human-in-the-loop and UX in Grace.
- Middleware and systems venues for MAD-to-MAD conversations and observability.

Dependencies:
- ICCM Papers 00–03 and IDE Papers 00–05 should be publicly available to support MAD foundations.

Release sequencing:
- MAD Papers 01–03 following ICCM/IDE foundation publication.
- MAD Papers 04–06 after stable CET/Rules/DER interfaces.
- MAD Papers 07–09 aligned with Half-MAD capability maturity and multi-agent orchestration.
- MAD Papers 10–12 after Hopper and Grace produce robust traces and metrics.
- MAD Papers 13–14 as capstone case studies.

Cross-discipline collaboration:
- Joint ICCM↔MAD papers on CET integration and context quality metrics.
- Joint IDE↔MAD papers on rules coverage, DER synthesis, and auditability.
- Joint trinity papers on complete agent assembly.

10. Research Questions

- Thinking Engine composition:
  - Optimal sequencing and feedback loops among CET, Rules, DER, and State Manager under varying domains.
- State Manager design:
  - Balancing episodic, semantic, working memory in dynamic tasks; consistency models for distributed MADs.
- Doing Engine patterns:
  - Swappability, verification strategies, and domain specialization without sacrificing safety.
- Half-MAD evolution:
  - Criteria for when focused capabilities warrant full autonomy.
- MAD-to-MAD coordination:
  - Protocols for joint planning, shared state, intent negotiation, and conflict resolution.
- LLM Orchestra integration:
  - Decision policies for when to consult; budget-aware synthesis; provenance-preserving prompts.
- Learning and adaptation:
  - Incorporating execution outcomes into policies and semantic memory; preventing catastrophic forgetting.
- Observability:
  - Techniques to correlate traces across MADs; standards for audit-quality provenance.
- Testing and validation:
  - Scenario generation, rules mutation testing, DER stress testing; system-level accept/reject criteria.
- Production deployment:
  - Operational patterns, SLOs, progressive delivery for decision policies, and resilience under partial outages.

11. Case Studies

11.1 Hopper: Autonomous Development MAD

Goal:
- Accept development tasks, plan, generate and modify code, run builds/tests, validate outcomes, and iterate.

Thinking Engine:
- CET:
  - Parse user task and repo state; classify intent (feature, fix, refactor); identify impacted components using Horace.
- Rules Engine:
  - Enforce policies (branching standards, test coverage thresholds, code owners).
  - Require human confirmation for risky operations (schema migrations, secrets handling).
- DER:
  - Propose implementation plan; request designs or code stubs via Fiedler as needed.
  - Produce alternatives (quick fix vs comprehensive refactor) with cost/benefit and confidence.
- State Manager:
  - Record planned changes; link to past similar tasks; maintain working memory for the active feature branch.

Doing Engine:
- Executes:
  - Create branches; generate code; run build and tests; perform static analysis; produce diffs and artifacts.
- Conversations:
  - Fiedler for code snippets or transformations; Gates for release notes; Playfair for architecture diagrams.
- Reporting:
  - Execution reports with metrics (compile/test times, pass rates, diff size); update State Manager.

Workflow example:
- Input: “Implement search auto-suggestions for product names.”
- CET: Classify as feature; link to search module and UI; retrieve related tickets.
- Rules: Require code owner approval; set coverage increase target; flag UX review.
- DER: Propose plan with stages (backend API extension, UI integration, tests); consult Fiedler for a ranked list of API designs; recommend choice with rationale.
- Doing: Implement feature branch; run tests; generate UI preview; present to human for approval.
- Outcome: Merge after policy checks; record all steps, decisions, and artifacts in State Manager.

Metrics:
- Build/test pass rates; rework frequency; code quality indicators; decision reproducibility for similar tasks.

11.2 Grace: Intelligent System UI MAD

Goal:
- Orchestrate interactions across capabilities; provide adaptive UI; capture user preferences and deliver tasks end-to-end.

Thinking Engine:
- CET:
  - Interpret user intents, UI context, session history; disambiguate multi-step requests.
- Rules Engine:
  - Enforce privacy, consent, rate limits; UI accessibility standards.
- DER:
  - Suggest interaction flows; rank capability combinations; decide when to ask clarifying questions.
  - Optionally consult Fiedler for summarizations or UI text proposals.
- State Manager:
  - Persist session state; user preferences; capability success statistics; world model of available capabilities.

Doing Engine:
- Executes:
  - UI rendering and updates; routing to Half-MAD capabilities; managing confirmations.
- Conversations:
  - Marco to connect to external domains; Godot for telemetry; Dewey for session logs; Fiedler for natural language synthesis.
- Reporting:
  - Outcome summaries, preference updates; error recoveries; user satisfaction signals.

Workflow example:
- Input: “Summarize these three reports and draft a two-page brief with a comparison chart.”
- CET: Classify as summarization + synthesis + document + diagram; retrieve the three documents via Horace/Dewey.
- Rules: Check document access permissions; apply quotas; require user consent for sharing.
- DER: Plan sequence: summarize each, synthesize cross-cutting themes, generate comparison chart spec, draft formatted brief; consult Fiedler for summary drafts under cost cap.
- Doing: Orchestrate through Gates for the brief and Playfair for the chart; present draft; collect user edits; finalize deliverable.
- Outcome: Deliver brief and chart; record full provenance for later reuse.

Metrics:
- Task success, user satisfaction, turnaround time, number of clarifications, adherence to preferences.

12. Governance, Versioning, and Change Management

Governance principles:
- Decisions are explainable and auditable; provenance is compulsory.
- Backward-compatible contracts across ICCM, IDE, and MAD are versioned and documented.
- Policy updates are treated as first-class changes with deployment staging and rollbacks.

Versioning:
- CET, Rules Engine, DER, State Manager contracts use semantic versioning.
- MAD agents record component versions in every decision and execution record.

Change management:
- Policy changes (Rules) go through canary stages with shadow decisioning to evaluate impact.
- DER strategy updates are A/B tested with guardrails; confidence calibration monitored.
- Doing Engine updates include rollback plans and progressive activation.

13. Security, Safety, and Ethics

Security:
- Conversation authentication and authorization; signed provenance and integrity checks.
- Data minimization and redaction policies enforced via Rules Engine and State Manager.
- Least privilege for capability invocations; secrets handled through secure enclaves managed as capabilities.

Safety:
- Multi-layer safety with Rules, DER risk assessment, Doing Engine guardrails, and human-in-the-loop.
- Adversarial prompt and model exploitation mitigations when consulting Fiedler (prompt hygiene, response validation).

Ethics:
- Bias mitigation via monitoring decision outcomes across demographics where applicable.
- Transparency to users on automated vs human-assisted decisions; consent management.
- Right-to-explanation provided through State Manager’s rationale records.

Conclusion

MAD is the Agent Assembly discipline that completes the trinity with ICCM and IDE:
- ICCM supplies CET for context transformation.
- IDE supplies Rules Engine and DER for decision-making.
- MAD integrates these with the State Manager and a Doing Engine to produce complete agents.

This separation of concerns enables agents that are:
- Transparent: each decision and action is explainable with full provenance.
- Auditable: rules and rationale are recorded, reproducible, and testable.
- Controllable: policies and safety are enforced with deterministic rules and verified execution.
- Composable: MADs converse and exchange capabilities through a shared ecosystem.

LLM Orchestra, provided by the Fiedler Half-MAD, is a universal capability accessible to both Thinking and Doing. MAD’s reference Full MADs, Hopper and Grace, operationalize these principles, validating the architecture across development and interactive system domains. The hierarchical MAD paper series codifies the patterns and practices for building, integrating, and deploying MADs at scale.

Appendix A: Terminology Reference

Correct terminology:
- Conversation: any communication between MADs or components; never described as service calls.
- Capability: what a MAD provides to others; never described as services or functions.
- Half-MAD: a MAD with minimal or incomplete Thinking Engine that provides focused capabilities.
- Full MAD: a MAD with a complete Thinking Engine (CET + Rules Engine + DER + State Manager) and a Doing Engine.
- Thinking Engine: the composition of CET (ICCM), Rules Engine (IDE), DER (IDE), and State Manager (MAD).
- Doing Engine: the domain-specific executor that carries out decisions and produces execution reports.
- CET: Context Engineering Transformer (from ICCM).
- Rules Engine: deterministic policy and decision executor (from IDE).
- DER: Decision Engineering Recommender for synthesis (from IDE).
- State Manager: memory and world model manager (from MAD).
- LLM Orchestra: multi-model consultation capability provided by Fiedler (a Half-MAD).

Deprecated terminology:
- Infrastructure or Infrastructure Classical.
- Service calls or API requests.
- Services or functions in this context.
- Infrastructure Half-MADs.

Appendix B: Conversation Patterns and Field Guides

General conversation envelope:
- Headers:
  - conversation_id
  - sender MAD id and role
  - receiver MAD id and capability
  - timestamps, correlation_id
- Body:
  - intent or purpose
  - context references (state pointers)
  - constraints (budget, time, policies)
  - expected schema of response
- Response:
  - result payload adhering to expected schema
  - rationale, confidence, alternatives (when relevant)
  - provenance, including any sub-conversations

LLM Orchestra consultation pattern (Fiedler):
- Request fields:
  - task description; context snippet or pointers; explicit constraints (cost cap, time cap)
  - desired structure; required rationales and confidence
- Response fields:
  - synthesized answer; candidate set; confidence per candidate; usage report; rationale summary

Observability conversation (Godot):
- Ingest event fields:
  - severity; message; context pointers; span attributes (start, end, children)
- Retrieval fields:
  - filter criteria; correlation_id; timeframe; severity thresholds

Appendix C: State Manager Interaction Cheatsheet

Read operations:
- get_state_snapshot(checkpoint_id or now)
- get_episodic_records(filters)
- get_semantic_entities(query)
- get_working_context(task_id)
- get_world_model(scope)

Write operations:
- append_decision_log(decision_package, rationale)
- record_execution_report(report)
- promote_semantic_fact(fact, source, confidence)
- update_working_context(task_id, delta)
- checkpoint_state(reason)

Consistency:
- Snapshot isolation for decision steps.
- Eventual consistency for semantic promotion and world model updates.
- Strong audit invariants: append-only logs, signed records.

Appendix D: Safety and Escalation Quick Rules

- Sensitive actions require:
  - Rules Engine approval, DER risk assessment, Doing Engine dry-run when possible, and human confirmation if configured.
- High uncertainty:
  - Request clarification from the user or consult LLM Orchestra; never proceed silently with low-confidence destructive actions.
- Budget violations:
  - Abort or degrade gracefully; present alternatives with lower cost; record reasons.

Appendix E: Example End-to-End Trace (Condensed)

- Input: “Migrate config system to support per-tenant overrides.”
- CET:
  - Classifies as refactor + feature; extracts affected modules; routes to Hopper’s domain.
  - References prior migrations; attaches semantic policies.
- Rules:
  - Requires migration plan, backward compatibility, rollout strategy.
- DER:
  - Proposes two alternatives: a) layered config with override resolution; b) schema extension with tenant-prefix tables.
  - Consults Fiedler for pattern comparison under performance and maintainability constraints.
  - Selects option a) with confidence 0.78; notes risks and mitigations.
- State Manager:
  - Records decision; checkpoints affected artifacts via Horace.
- Doing Engine:
  - Implements layered config; runs integration tests; deploys to staging.
- Feedback:
  - Test results: stable; performance within bounds.
  - State updates: semantic memory records new config ontology; episodic logs link artifacts to decision.
- Completion:
  - Human review and approval; production rollout staged; final audit log includes every conversation and artifact link.

Appendix F: Reading Map

- Start with ICCM Paper 00 for CET principles and context schemas.
- Proceed to IDE Paper 00 for Rules and DER mechanics, including decision packaging.
- Use this MAD Paper 00 for assembly guidance; follow MAD Papers 01–14 for implementation details and case studies.

End of Paper 00 v2.0.