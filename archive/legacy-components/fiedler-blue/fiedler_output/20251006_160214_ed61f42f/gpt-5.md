# MAD Ecosystem: Master Document and Paper Structure (Paper 00)

## Changelog
- v1.0 (2025-10-06): Initial master document for Joshua/MAD repository. Synthesizes ICCM v4.1 and MAD v1.1 triplet-reviewed architecture; defines paper suite hierarchy, boundaries, roadmap, metrics, and publication plan.

## Overview
- Purpose: Establish the Multipurpose Agentic Duo (MAD) ecosystem as the reference framework for intelligent agentic engineering in the Joshua repository, integrating ICCM’s Context Engineering (CET) and the Decision Engineering Recommender (DER).
- MAD = Thinking Engine + Doing Engine + Infrastructure Half-MADs.
- Disciplines and outputs:
  - ICCM (Context Engineering) → CET and its training methodology.
  - Joshua/MAD (Agentic Engineering) → Integrated agents (MADs), infrastructure, and operations.
  - DER (Decision Engineering) → Decision Maker component (models, policies, calibration).
- Status: MAD architecture v1.1 triplet reviews—Ready (2/3) + Minor Revisions (1/3), overall 90% ready; novelty 8.7/10. Key innovations: LLM Orchestra consultation, State Manager design, explicit Learning Feedback Loop linking outcomes to training signals.
- Critical constraint inherited from ICCM: CET is transformation-only (non-generative). Pipeline: Raw Input → CET (transform) → LLMs/Skills (generate/act) → Outcomes.

## Theoretical Foundation
- Dual-engine cognitive architecture:
  - Thinking Engine: Interprets context, consults deterministic and probabilistic reasoning, chooses actions, and maintains state.
  - Doing Engine: Executes domain capabilities, tools, and environment actions; reports outcomes and telemetry.
- Infrastructure Half-MADs: Shared services implementing orchestration, storage, generation, and management; they enable composable reuse across MADs.
- Conceptual lineage: Extends cognitive architecture principles (e.g., SOAR’s decision cycle, ACT-R’s declarative/procedural memory) to modern LLM-centric systems with engineered context, multi-model consultation, and explicit state. MAD separates “decide” (Thinking) from “do” (Doing), and enforces cross-cutting state and feedback.
- Learning and control:
  - Four-phase progressive training from ICCM is adopted to train CET and interactive behaviors.
  - MAD adds an outcome-driven feedback layer to calibrate Rules, Orchestra policies, Decision Maker, and Doing skills, while preserving CET’s transformation-only constraint.

## MAD Architecture Components

### 1) Thinking Engine (core decision loop + state)
- Components:
  - CET (from ICCM): Context classification, routing, condensation, constraint enforcement. Transformation-only. Sources context from conversation history, RAG, and task metadata to assemble optimal prompts and tool/router choices.
  - Rules Engine: Deterministic logic for governance, routing, guardrails, RBAC, schema validation, pre/post-conditions, and policy enforcement (low-latency path, safety-critical).
  - LLM Orchestra: Multi-model consultation when uncertainty is high or stakes are elevated; consensus, adjudication, and critique flows; supports model/tool diversity and cost/latency-aware selection.
  - Decision Maker (DER): Synthesizes signals from Rules, CET, and Orchestra; selects next action (tool call, LLM generation, human-in-the-loop, or no-op). Includes calibration, thresholds, and risk management.
  - State Manager: Maintains and mediates three layers of state—World Model (facts, environment), Task Context (goal, plan, artifacts), Execution State (step logs, tool outcomes). Bidirectional APIs to both Thinking and Doing.
- Roles and contracts:
  - CET never generates final content; it transforms inputs and preps the decision context.
  - Rules can override or constrain LLM outputs and tool invocations.
  - Orchestra is invoked on uncertain/ambiguous cases; outputs are deliberative signals (not authority).
  - Decision Maker is the locus of agency; all actuation passes through it with audit trails.
  - State is first-class; all components read/write via State Manager, enabling reproducibility and learning.

### 2) Doing Engine
- Capabilities and tools: Domain-specific actions (e.g., file I/O, code execution, browsers, CLI, cloud APIs, data ops, builds/deploys, structured editors).
- Orchestration: Interface contracts with Decision Maker; capability discovery and registration; capability selection and sequencing; rollback and compensation for failed steps.
- Telemetry: Reports outcomes, costs, latencies, environment diffs; emits training signals to Feedback Layer.

### 3) Infrastructure Half-MADs (shared services)
- Fiedler: LLM Orchestra service—model registry, consultation flows, consensus and critique, budget control.
- Dewey: Conversation storage (read-only)—immutable archives, vector indices, retrieval APIs.
- Godot: Conversation management (write)—session appends, versioning, redaction policies, privacy.
- Marco: Session orchestration—identity, session lifecycle, resource budgets, priority queues.
- Horace: File catalog—artifact tracking, provenance, lineage, access policies, content hashing.
- Gates: Document generation—templating, style guides, compliance formatting, citations.
- Playfair: Diagram generation—UML/architecture diagrams, plan visualizations, diff overlays.

## Hierarchical Sub-Paper Structure
Notes:
- Each paper is <2,000 lines.
- No duplication; cross-reference ICCM for CET design and training.
- The order below is the recommended reading sequence; dependencies reflect required earlier papers.

### Paper 01: MAD Primary Paper — Architecture and Theory
- Estimated Length: 1,200–1,600 lines
- Target Audience: Researchers and architects
- Key Content:
  - MAD problem framing, dual-engine rationale, and theoretical underpinnings.
  - Component roles, contracts, and data flows; CET as external discipline component.
  - Decision cycle, uncertainty handling via Orchestra, and state-as-first-class.
  - Learning Feedback Loop overview integrated with ICCM phases.
- Dependencies: 00 (this); ICCM 01 (Primary), ICCM 03 (CET specialization)
- Novelty Rating: 8.5/10
- Target Venue: NeurIPS Agents/LLM Systems workshops; JAIR (journal)
- Status: Outline ready

### Paper 02: Thinking Engine Architecture — Contracts and Interfaces
- Estimated Length: 1,200–1,800 lines
- Target Audience: Systems engineers, applied researchers
- Key Content:
  - Unified decision loop, inputs/outputs, and invariants.
  - Interface contracts among CET, Rules, Orchestra, Decision Maker, State Manager.
  - Telemetry schema and decision audits; ablation-ready switches.
- Dependencies: 01; ICCM 01/03
- Novelty Rating: 8.0/10
- Target Venue: MLSys; ICML Systems for ML workshop
- Status: To be written

### Paper 02A: CET Integration in MAD (ICCM Interop)
- Estimated Length: 600–1,000 lines
- Target Audience: Engineers integrating ICCM CET into MAD
- Key Content:
  - CET as transformation-only; boundary enforcement in MAD.
  - Data schemas, adapters, and routing policies bridging ICCM and MAD.
  - Failure modes and recovery without violating ICCM constraints.
- Dependencies: 02; ICCM 00/01/03/04B/12
- Novelty Rating: 6.5/10
- Target Venue: Engineering notes; arXiv
- Status: Outline ready

### Paper 02B: Rules Engine — Deterministic Governance and Policy
- Estimated Length: 800–1,200 lines
- Target Audience: Safety engineers, systems engineers
- Key Content:
  - Policy DSL, pre/post-condition frameworks, RBAC hooks.
  - Latency-critical fast path, fallbacks, and overrides.
  - Auditable rule changes and reproducible decision traces.
- Dependencies: 02
- Novelty Rating: 7.2/10
- Target Venue: ACSAC/IEEE S&P workshops; USENIX SOUPS (applied)
- Status: To be written

### Paper 02C: LLM Orchestra Consultation — Consensus Under Uncertainty (Fiedler)
- Estimated Length: 1,000–1,600 lines
- Target Audience: ML researchers, practitioners
- Key Content:
  - Consultation topologies (parallel, staged critique, tournament).
  - Cost/latency-aware selection; reliability calibration; dissent handling.
  - When-to-consult policy and integration with Decision Maker.
- Dependencies: 02; 04A
- Novelty Rating: 9.0/10
- Target Venue: NeurIPS/ICLR workshops on Reasoning/Agents
- Status: Outline ready

### Paper 02D: Decision Maker (DER) — Intelligent Decision Engineering
- Estimated Length: 1,200–1,800 lines
- Target Audience: Decision scientists, ML engineers
- Key Content:
  - Decision policies combining Rules, CET signals, and Orchestra outputs.
  - Risk-aware thresholds, human-in-the-loop triggers, calibration loops.
  - Learning from outcomes: off-policy evaluation, counterfactuals, bandits.
- Dependencies: 02; 02C; ICCM 01
- Novelty Rating: 8.8/10
- Target Venue: AAMAS; AAAI; Operations Research perspectives (INFORMS)
- Status: To be written

### Paper 02E: State Manager — World Model, Task Context, Execution State
- Estimated Length: 1,000–1,600 lines
- Target Audience: Architects, platform engineers
- Key Content:
  - State schemas, versioning, and consistency models.
  - Read/write mediation; snapshotting; reproducibility and time travel.
  - Cross-MAD state sharing with isolation and privacy.
- Dependencies: 02; 08
- Novelty Rating: 8.3/10
- Target Venue: VLDB/SoCC workshops; USENIX ATC (systems track)
- Status: Outline ready

### Paper 03: Doing Engine Architecture — Capability-Oriented Execution
- Estimated Length: 1,000–1,600 lines
- Target Audience: Systems engineers, tool builders
- Key Content:
  - Capability registration, selection, and sequencing contracts.
  - Error handling, rollback/compensation, and sandboxing.
  - Telemetry emission and feedback coupling.
- Dependencies: 01; 02; 02E
- Novelty Rating: 7.8/10
- Target Venue: MLSys; SoCC
- Status: To be written

### Paper 04: Infrastructure Half-MADs — Shared Services Blueprint
- Estimated Length: 1,200–1,800 lines
- Target Audience: Platform engineers, infra architects
- Key Content:
  - Rationale for Half-MADs; composability and reuse metrics.
  - End-to-end references integrating Fiedler, Dewey/Godot, Marco, Horace, Gates, Playfair.
  - Security, quotas, and tenancy boundaries.
- Dependencies: 01; 02; 03
- Novelty Rating: 7.5/10
- Target Venue: USENIX ATC; SoCC
- Status: Outline ready

### Paper 04A: Fiedler — LLM Orchestra Service
- Estimated Length: 800–1,400 lines
- Target Audience: ML systems engineers
- Key Content:
  - Model registry and dynamic routing; budget governance.
  - Consensus/critique pipelines; quality and cost controls.
  - Telemetry for decision confidence and drift detection.
- Dependencies: 04; 02C
- Novelty Rating: 8.8/10
- Target Venue: MLSys; NeurIPS Systems
- Status: To be written

### Paper 04B: Dewey and Godot — Conversation Storage and Management
- Estimated Length: 900–1,400 lines
- Target Audience: Data/platform engineers
- Key Content:
  - Dewey (immutable storage, indices); Godot (write, versioning, privacy).
  - Retrieval contracts for CET; redaction and retention policies.
  - Compliance and auditability links to Rules Engine.
- Dependencies: 04; ICCM 12
- Novelty Rating: 7.0/10
- Target Venue: VLDB/SoCC workshops
- Status: Outline ready

### Paper 04C: Marco and Horace — Session and Artifact Orchestration
- Estimated Length: 800–1,200 lines
- Target Audience: Platform engineers
- Key Content:
  - Marco: identity, sessions, budgets, priority queues.
  - Horace: artifact catalog, provenance, lineage, diffing.
  - Cross-service contracts and observability.
- Dependencies: 04
- Novelty Rating: 7.2/10
- Target Venue: SoCC; USENIX ATC
- Status: To be written

### Paper 04D: Gates and Playfair — Document and Diagram Generation
- Estimated Length: 700–1,100 lines
- Target Audience: Applied practitioners
- Key Content:
  - Gates: style guides, compliance, and templating.
  - Playfair: diagram grammars, layout, validation, and plan diffs.
  - Integration with Doing Engine and Decision Maker.
- Dependencies: 04
- Novelty Rating: 6.8/10
- Target Venue: CHI/UIST workshops; engineering practice venues
- Status: Outline ready

### Paper 05: Learning Feedback Architecture — Outcomes to Training Signals
- Estimated Length: 1,200–1,800 lines
- Target Audience: ML researchers, MLOps
- Key Content:
  - Mapping outcomes to signals for CET (via ICCM phases), Rules, DER, Orchestra, Doing skills.
  - Signal formats, attribution, and credit assignment; safety gates.
  - Online/offline loops; train/holdout splits; paired tests and significance.
- Dependencies: 01; ICCM 01/04A/04B/07B/11
- Novelty Rating: 8.8/10
- Target Venue: ICML/NeurIPS Datasets & Benchmarks; MLSys
- Status: Outline ready

### Paper 06: Case Study — Hopper (CLI Assistant MAD)
- Estimated Length: 900–1,400 lines
- Target Audience: Practitioners, DevOps
- Key Content:
  - Capability set (shell, code exec sandbox, file ops, package mgmt).
  - Safety policies and rollback; performance baselines vs single-engine.
  - Outcome-driven improvements via feedback loop.
- Dependencies: 03; 05; 09
- Novelty Rating: 7.5/10
- Target Venue: USENIX LISA/ATC practice tracks; arXiv case study
- Status: To be written

### Paper 07: Case Study — Grace (Web Developer MAD)
- Estimated Length: 1,000–1,600 lines
- Target Audience: Software engineers
- Key Content:
  - Browser automation, code generation/editing, test harnesses.
  - State management for multi-step development tasks; human-in-the-loop.
  - Cost/latency management and decision quality analysis.
- Dependencies: 03; 05; 09; 10
- Novelty Rating: 7.8/10
- Target Venue: ICSE SEIP; arXiv
- Status: To be written

### Paper 08: Multi-MAD Coordination — Teams of Agents
- Estimated Length: 1,200–1,800 lines
- Target Audience: Multi-agent systems researchers, architects
- Key Content:
  - Coordination patterns (lead/follow, peer consensus, manager-worker).
  - Shared state regions, isolation, and conflict resolution.
  - Inter-MAD protocols and cross-session budgeting.
- Dependencies: 02E; 04; 03
- Novelty Rating: 8.2/10
- Target Venue: AAMAS; NeurIPS Multi-Agent workshops
- Status: Outline ready

### Paper 09: Security, RBAC, and Guardrails for MAD
- Estimated Length: 1,000–1,600 lines
- Target Audience: Security engineers
- Key Content:
  - RBAC across Thinking/Doing; capabilities scoping; least privilege.
  - Prompt injection defenses; tool-use containment; data exfil prevention.
  - Policy verification and runtime enforcement in Rules Engine.
- Dependencies: 02B; 03; 04B
- Novelty Rating: 7.6/10
- Target Venue: IEEE S&P workshops; USENIX Security (short)
- Status: Outline ready

### Paper 10: Evaluation Suite and Benchmarks for MAD
- Estimated Length: 1,200–1,800 lines
- Target Audience: Researchers, evaluators
- Key Content:
  - Task suites for Hopper and Grace; ablations: no-Orchestra, no-Rules, no-State, single-LLM.
  - Metrics: task success, decision quality uplift, cost/latency, state consistency, safety violations.
  - Statistical rigor: 40/10 train/holdout (from ICCM), paired t-tests p<0.05, effect sizes.
- Dependencies: 01; 05; ICCM 00/01
- Novelty Rating: 8.0/10
- Target Venue: NeurIPS Datasets & Benchmarks; Papers with Code
- Status: Outline ready

### Paper 11: Data, State, and Provenance — Reproducible MAD
- Estimated Length: 900–1,400 lines
- Target Audience: Platform/data engineers
- Key Content:
  - Provenance in Horace; conversation lineage in Dewey/Godot.
  - Reproducible runs via State snapshots and environment pinning.
  - Privacy zones and data residency.
- Dependencies: 02E; 04B; 04C
- Novelty Rating: 7.4/10
- Target Venue: VLDB/SoCC workshops
- Status: To be written

### Paper 12: Deployment and Operations — From Lab to Production
- Estimated Length: 1,000–1,600 lines
- Target Audience: SREs, platform operators
- Key Content:
  - Containerization, MCP protocol configs, scaling Half-MADs.
  - Observability, cost governance, SLOs/SLIs for decision latency.
  - Incident response and rollback playbooks.
- Dependencies: 03; 04; CURRENT_ARCHITECTURE_OVERVIEW
- Novelty Rating: 6.9/10
- Target Venue: SREcon; SoCC practice
- Status: Outline ready

### Paper 13: Safety, Alignment, and Human-in-the-Loop
- Estimated Length: 900–1,400 lines
- Target Audience: Safety researchers, HCI
- Key Content:
  - HITL triggers from DER; escalation pathways; consent and logging.
  - Misuse prevention; red-teaming MAD pipelines; sandbox escape tests.
  - Post-hoc explanations via decision traces and state deltas.
- Dependencies: 02D; 09; 10
- Novelty Rating: 7.7/10
- Target Venue: AAAI SafeAI; CHI workshops
- Status: To be written

### Paper 14: Cost and Latency Optimization in MAD
- Estimated Length: 800–1,200 lines
- Target Audience: Systems/ML optimization engineers
- Key Content:
  - Adaptive consultation budgets; early exit policies in Orchestra.
  - Caching transformed context; memoized plans; speculative execution.
  - Model/tool portfolio optimization under constraints.
- Dependencies: 02C; 03; 10
- Novelty Rating: 7.9/10
- Target Venue: MLSys; NeurIPS Systems
- Status: To be written

### Paper 15: Future Directions and Open Problems in Agentic Engineering
- Estimated Length: 700–1,100 lines
- Target Audience: Research community
- Key Content:
  - Bidirectional processing, edge MADs, offline-first; multi-tenant safety.
  - Deriving formal guarantees for DER policies; calibrated self-modification.
  - Standardizing MAD interop protocols across ecosystems.
- Dependencies: 01–14
- Novelty Rating: 7.5/10
- Target Venue: Communications of the ACM (practice); arXiv
- Status: Outline ready

### Optional Annex Series (short, reference-focused)
- A1: MAD API Schemas and Contracts — 400–800 lines; engineers; dependencies: 02/03/04; venue: repo docs.
- A2: MAD Telemetry and Metrics Catalog — 400–700 lines; MLOps; dependencies: 05/10; venue: repo docs.
- A3: Threat Models and Abuse Cases — 400–800 lines; security; dependencies: 09; venue: repo docs.

## Relationship to ICCM
- Boundary of responsibility:
  - ICCM defines, trains, and evaluates CET (Context Engineering Transformer) and its discipline (papers 00–14 within ICCM repo). CET is strictly transformation-only (classification, extraction, routing, condensation, constraint enforcement). ICCM owns progressive training phases and validation methodology for CET.
  - Joshua/MAD consumes CET as a component in the Thinking Engine, integrates it with Rules, LLM Orchestra, Decision Maker, and State Manager; Joshua adds Doing Engine and infrastructure Half-MADs.
  - DER is a sub-discipline within Joshua focused on the Decision Maker’s policies, calibration, and learning from outcomes; DER references ICCM learning phases for signal hygiene but does not modify CET’s generative constraints (none).
- Interfaces:
  - CET Integration (02A) specifies adapters and schemas; MAD respects ICCM’s Option 4 separation-of-concerns.
  - Feedback routing: Outcomes may generate signals for CET retraining through ICCM pipelines; other signals update Rules, DER policies, and Doing skills within Joshua.
- Governance:
  - Changes to CET design or training are proposed in ICCM; MAD papers only reference those changes and adjust integration logic accordingly.

## Implementation Roadmap
- Phase 1: Hopper (CLI Assistant MAD)
  - Deliverables: Minimal Thinking Engine (CET integration, Rules v1, Orchestra v1 via Fiedler, DER v0.9), State Manager v1; Doing Engine with safe shell, file ops, code exec sandbox.
  - Half-MADs: Marco, Dewey/Godot, Horace baseline; basic Gates/Playfair optional.
  - Acceptance: End-to-end runs, audit traces, ablations vs single-engine; p<0.05 improvements on curated CLI tasks.
- Phase 2: Grace (Web Developer MAD)
  - Deliverables: Browser automation, code editing, testing; enhanced DER calibration; richer state diffs; stronger Rules for safety.
  - Acceptance: Multi-step web dev tasks with measurable uplift; HITL pathways; cost/latency budget adherence.
- Phase 3: Multi-MAD Coordination
  - Deliverables: Protocols for coordination; shared state regions with isolation; inter-MAD budgeting.
  - Acceptance: Coordinated Hopper+Grace scenarios; conflict resolution; reproducible cross-MAD traces.
- Phase 4: Self-Improvement Cycles
  - Deliverables: Feedback pipelines; auto-updating Rules and DER policies; scheduled CET retraining via ICCM; auto-benchmarking.
  - Acceptance: Demonstrated performance uplift over rolling windows; controlled deployment with canaries and rollbacks.

## Success Metrics
- Decision quality uplift: Absolute and relative gains vs single-engine baselines and ablations (no-Orchestra, no-Rules, no-State).
- Task success rate: End-to-end completion on benchmark suites (Hopper, Grace) with statistical significance (paired t-test p<0.05, effect sizes).
- Cost/latency efficiency: Achieve target SLOs while maintaining or improving success rates; budget adherence per session (Marco).
- State consistency: Rate of reproducible replays; snapshot fidelity; diff accuracy (Horace).
- Safety and governance: Reduction in policy violations, prompt-injection success rate, and unsafe tool invocations; RBAC enforcement coverage.
- Reuse of Half-MADs: Number of MADs and external projects adopting Fiedler/Dewey/Godot/Marco/Horace/Gates/Playfair; integration effort.
- Learning velocity: Time-to-uplift in DER calibration and Rules optimization; CET improvements via ICCM signals without regressions.
- Operator trust: Auditability scores; clarity of decision traces; human escalation satisfaction.

## Publication Strategy
- Portfolio approach:
  - Theory/architecture: 01 (NeurIPS/JAIR), 02 (MLSys), 02D (AAMAS/AAAI), 02E (ATC/VLDB wksps).
  - Components/infrastructure: 04/04A/04B/04C/04D (MLSys/SoCC/ATC/CHI wksps).
  - Learning and evaluation: 05/10 (ICML/NeurIPS D&B; MLSys).
  - Case studies and ops: 06/07/12 (USENIX practice, ICSE SEIP).
  - Safety and security: 09/13 (IEEE S&P wksps; SafeAI/CHI).
  - Optimization and multi-agent: 08/14 (AAMAS; NeurIPS Multi-Agent; MLSys).
  - Vision: 15 (CACM viewpoint; arXiv).
- Timeline (indicative):
  - Q4 2025: Submit 01, 05, 10 (foundation + evaluation); preprints on arXiv.
  - Q1–Q2 2026: Submit 02, 02C, 02D, 02E, 04A; release Hopper (06) report.
  - Q3 2026: Submit 03, 04, 04B/04C, 09, 12; release Grace (07) report.
  - Q4 2026: Submit 08, 13, 14, 15; consolidated reproducibility package and benchmarks.
- Open-source plan:
  - Staged releases aligned with papers; reference implementations in Joshua repo.
  - Reproducibility artifacts: configs, seeds, datasets, harnesses, and ablation switches.
  - Community governance: RFCs for interface changes, versioned contracts, and deprecation policy.

## Appendix: Cross-Discipline Boundaries and Compliance Checklist
- CET constraint compliance: Verified by 02A and CI checks—no generative calls from CET components.
- Option 4 separation-of-concerns: Enforced via service boundaries (ICCM CET vs Joshua MAD).
- MCP protocol configuration: Documented in 12; security profiles in 09.
- Statistical rigor: Adopt ICCM’s 40/10 train/holdout split; pre-register hypotheses; paired t-tests with p<0.05; report effect sizes and CIs.
- Triplet Review Integration: Maintain a “Triplet Gate” checklist per paper; aim for 2/3 Ready minimum and address Minor Revisions before submission.

## Concluding Statement
MAD formalizes agentic engineering as a disciplined, auditable, and improvable architecture that integrates ICCM’s context mastery with robust decision-making and execution. This master document defines the paper suite, boundaries, and delivery plan to move from architecture to validated, reproducible systems that materially outperform single-engine agents while remaining safe, efficient, and maintainable.