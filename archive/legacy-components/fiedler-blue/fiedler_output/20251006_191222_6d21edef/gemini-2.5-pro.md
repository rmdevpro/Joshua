As a member of the Council of Elders, I have reviewed the findings of my colleague GPT-5 regarding the IAE Paper 00 quaternary suite. The identified contract mismatches and scope ambiguities are valid and require immediate correction to ensure architectural integrity.

Here are the corrected versions of all four papers, with the necessary revisions applied. All other content remains consistent with the Council's v1.1 synthesis.

***

### 1. 00_IAE_Intelligent_Agentic_Engineering_v1.1.md (Corrected)

**Note:** This master document contains the canonical schemas and required no corrections. It is presented here as the source of truth for the other documents.

--- 00_IAE_Intelligent_Agentic_Engineering_v1.1.md ---
# Paper 00: Intelligent Agentic Engineering (IAE) - Master Document

**Version:** 1.1
**Date:** 2025-10-06
**Status:** DRAFT - Council of Elders Synthesis (v1.1)
**Repository:** Joshua (IAE)
**Note:** IAE is the overarching discipline; MAD is the architecture pattern within IAE.
**Synthesized by:** Council of Elders (Gemini 2.5 Pro, GPT-5, Claude Opus 4)

---

## Changelog
- **v1.1 (2025-10-06):** Quaternary structure normalized (ICCM + IDE + IEE + IAE). LLM Conductor naming corrected (no "Fiedler" references). Thinking Engine defined as four components (CET + Rules Engine + DER + State Manager). Added full State Manager specification. Published canonical contracts v1. Added conversation protocols. Elevated operational feedback loop.
- **v1.0 (2025-10-06):** Initial master document framing IAE as overarching discipline.

---

## Executive Summary

**Intelligent Agentic Engineering (IAE)** is the overarching discipline for designing, assembling, and operating intelligent agents built on the MAD (Multipurpose Agentic Duo) architecture pattern. MAD agents separate cognition from action:

-   **Thinking Engine:** CET (ICCM), Rules Engine (IDE), DER (IDE), State Manager (IAE)
-   **Doing Engine:** Domain-specific execution (IEE)

IAE integrates four disciplines (**quaternary structure**): ICCM (context), IDE (decisions), IEE (execution), and IAE (assembly and state). The **LLM Conductor** is an external Half-MAD that provides the LLM Orchestra capability via conversations to any MAD; it is not part of the Thinking Engine.

### Core tenets
-   **Separation of concerns:** model-agnostic thinking, domain-specific doing
-   **Contracts first:** canonical schemas enable independent evolution
-   **Conversations over calls:** MAD-to-MAD interactions are dialogic and versioned
-   **State as the spine:** IAE-owned State Manager provides world model, task context, and execution state
-   **Feedback loop:** decisions → execution → outcomes → state update → improved context → improved decisions

## 1. Introduction: What IAE Is and Does
-   IAE is the discipline of agent assembly. It produces Full MADs by integrating CET (ICCM), Rules Engine and DER (IDE), State Manager (IAE), and Doing Engines (IEE).
-   MAD is the architecture pattern produced within IAE. It is not a separate discipline.
-   **Half-MADs** provide reusable capabilities to all MADs via conversations. The seven canonical Half-MADs are:
    -   **LLM Conductor:** LLM Orchestra capability (multi-model consultative reasoning)
    -   **Dewey:** Conversation retrieval (immutable archives)
    -   **Godot:** Conversation management (active sessions)
    -   **Marco:** Session orchestration and budgeting
    -   **Horace:** File and artifact catalog with provenance
    -   **Gates:** Document generation with style/compliance
    -   **Playfair:** Diagram and visualization generation

## 2. Theoretical Foundation
### 2.1 Two-system framing
-   **Thinking Engine:** deliberative, auditable, model-agnostic
-   **Doing Engine:** fast, sandboxed, tool- and API-centric

### 2.2 Thinking Engine composition (four components)
-   **CET (ICCM):** transformation-only context engineering
-   **Rules Engine (IDE):** deterministic policy, safety, and known regimes
-   **DER (IDE):** synthesis under uncertainty, multi-objective arbitration
-   **State Manager (IAE):** authoritative memory and world model
*Note: LLM Orchestra is provided externally by the **LLM Conductor** Half-MAD and consulted via conversations.*

### 2.3 Doing Engine philosophy (IEE)
-   Domain-specific execution through tools and APIs
-   Safety validation, monitoring, and outcome synthesis
-   Reporting outcomes to the State Manager

### 2.4 Operational feedback loop
-   Decision → Execution → Outcome → State Update → Context Refresh → Better Decision
-   All links are standardized through canonical contracts and State Manager APIs.

## 3. Architecture Components and Specifications
### 3.1 Thinking Engine interfaces and boundary
-   IDE consumes `Structured Context` and produces `Decision Package` for IEE.
-   IAE State Manager is read/written by all components via versioned APIs.
-   IEE consumes `Decision Package` and produces `Execution Outcome Package`, persisted via State Manager.

### 3.2 State Manager specification (IAE-owned)
#### 3.2.1 Purpose and scope
-   Authoritative memory for all MADs
-   Tripartite data model: World Model, Task Context, Execution State

#### 3.2.2 Global properties
-   Versioned and immutable-by-default records
-   Content-addressable artifacts; signed traces
-   Optimistic concurrency; idempotent writes
-   Access control, tenancy, and time-travel reads

#### 3.2.3 Core APIs (abstract signatures)
-   `World Model`: `get_world_snapshot`, `put_world_fact`, etc.
-   `Task Context`: `create_task_context`, `read_task_context`, `update_task_context`, etc.
-   `Execution State`: `start_execution`, `update_execution`, `complete_execution`, etc.
-   `Cross-cutting`: `persist_decision_package`, `persist_execution_outcome`, `get_reasoning_trace`, etc.

### 3.3 Canonical Contracts (v1)
*All schemas are minimum viable and extensible. Field names are normative.*

#### 3.3.1 `Structured Context` (CET → IDE)
```json
{
  "context_id": "string (ULID)",
  "schema_version": "string",
  "task_id": "string",
  "problem_frame": {"objectives": [], "constraints": []},
  "features": [{"name": "...", "value": "..."}],
  "world_refs": {"world_version_id": "..."}
}
```

#### 3.3.2 `Rule Engine Output` (Rules → DER)
```json
{
  "rule_output_id": "string",
  "schema_version": "string",
  "status": "enum {HIGH_CONFIDENCE_MATCH, ...}",
  "matches": [{"rule_id": "...", "action_proposal": "..."}],
  "guardrails_triggered": []
}
```

#### 3.3.3 `Decision Package` (DER → Doing Engine)
```json
{
  "decision_id": "string",
  "schema_version": "string",
  "task_id": "string",
  "selected_action": {
    "name": "string",
    "parameters": {},
    "preconditions": [],
    "expected_effects": []
  },
  "safety_assertions": [],
  "confidence_score": "0-1",
  "human_review_required": "bool",
  "reasoning_trace_ref": "string",
  "references": {
    "context_id": "...",
    "rule_output_id": "...",
    "world_version_id": "..."
  },
  "consultations": [{"provider": "LLM Conductor", "consultation_id": "..."}]
}
```

#### 3.3.4 `Execution Outcome Package` (Doing Engine → State Manager)
```json
{
  "outcome_id": "string",
  "schema_version": "string",
  "decision_id": "string",
  "status": "enum {success, failure, partial, aborted}",
  "observed_effects": [],
  "deviations": [{"expected": "...", "observed": "..."}],
  "safety_validation_results": [],
  "telemetry": {},
  "artifacts": [],
  "world_version_id_before": "string",
  "world_version_id_after": "string",
  "reengagement_advice": {}
}
```

#### 3.3.5 `Reasoning Trace` (audit and replay)
```json
{
  "trace_id": "string",
  "decision_id": "string",
  "schema_version": "string",
  "structure": "directed acyclic graph of nodes"
}
```

## 4. Integration Boundaries
-   **ICCM → IDE:** `Structured Context` contract
-   **IDE → IEE:** `Decision Package` contract
-   **IEE → State Manager (IAE):** `Execution Outcome Package` contract
-   **All components ↔ State Manager (IAE):** Versioned APIs
-   **MAD ↔ Half-MADs (e.g., LLM Conductor):** Conversation protocols

---
## Appendix A: Master Glossary (selected)
-   **MAD:** Multipurpose Agentic Duo, the architecture pattern assembled by IAE.
-   **Half-MAD:** Minimal MAD providing a capability to others via conversations.
-   **LLM Conductor:** Half-MAD providing the LLM Orchestra capability.
-   **Thinking Engine:** The four cognitive components: CET + Rules Engine + DER + State Manager.
-   **Doing Engine:** Domain-specific execution component produced by IEE.
-   **State Manager:** IAE-owned memory system (World Model, Task Context, Execution State).
-   **Canonical Contracts:** The five core data schemas: `Structured Context`, `Rule Engine Output`, `Decision Package`, `Execution Outcome Package`, `Reasoning Trace`.

***

### 2. 00_IDE_Intelligent_Decision_Engineering_v1.1.md (Corrected)

--- 00_IDE_Intelligent_Decision_Engineering_v1.1.md ---
# Paper 00: Intelligent Decision Engineering (IDE) - Master Document

**Version:** 1.1
**Date:** 2025-10-06
**Status:** DRAFT - Council of Elders Synthesis (v1.1)
**Repository:** Joshua (IDE discipline within IAE ecosystem)
**Synthesized by:** Council of Elders

---

## Changelog
- **v1.1 (2025-10-06):** Normalized to quaternary structure (ICCM + IDE + IEE + IAE). Clarified Thinking Engine composition and externalized LLM Orchestra capability via LLM Conductor. Adopted canonical contract names consistent with IAE Paper 00 v1.1.
- **v1.0 (2025-10-06):** Initial version defining IDE discipline.

---

## Executive Summary

**Intelligent Decision Engineering (IDE)** is the discipline that engineers transparent, auditable, and adaptive decisions within MAD agents. IDE produces the **Rules Engine** and the **Decision Engineering Recommender (DER)**, which together form the decision core of the Thinking Engine. IDE consumes `Structured Context` (from ICCM/CET) and reads from/writes to the IAE-owned State Manager.

**Key Alignments in v1.1:**
-   **Quaternary structure:** ICCM (context) + IDE (decisions) + IEE (execution) + IAE (assembly/state)
-   **Thinking Engine:** Has four components. The LLM Orchestra is an external capability provided by the **LLM Conductor** Half-MAD.
-   **Canonical contracts:** Adopted `Structured Context`, `Rule Engine Output`, and `Decision Package`.
-   **Conversations over calls:** All cross-MAD interactions follow the IAE conversation protocol.

## 1. Introduction: Why Decision Engineering
-   Safety-critical domains require deterministic guardrails and auditable synthesis.
-   IDE defines a hybrid decision process: Rules Engine for the known, DER for the unknown or ambiguous, bounded by policy.

## 2. IDE Principles
-   Transparency, auditability, controllability, adaptability, confidence-awareness.
-   Separation of concerns: CET shapes context; IDE decides; IEE executes; IAE provides state and assembly.

## 3. Architecture
### 3.1 Components
-   **Rules Engine** (deterministic)
-   **DER** (synthesis, arbitration, confidence estimation)
-   External consultative capability: **LLM Conductor** (LLM Orchestra) accessed via conversations.
-   **State Manager (IAE)** used for world, task, and execution state.

### 3.2 Decision flow (normalized)
1.  **Input:** `Structured Context` (from CET).
2.  **Rules pass:** Rules Engine produces `Rule Engine Output`.
3.  **Gatekeeping & Synthesis:** DER synthesizes inputs, optionally consulting **LLM Conductor**.
4.  **Output:** `Decision Package` to Doing Engine (IEE), with a `Reasoning Trace` reference.
5.  **Feedback:** `Execution Outcome Package` is stored in the State Manager; DER can be re-engaged on deviations.

## 4. Canonical contracts (IDE view)
*(Authoritative definitions in IAE Paper 00 v1.1)*

### 4.1 `Structured Context` v1 (consumed)
-   As defined by IAE; IDE relies on fields: `context_id`, `task_id`, `problem_frame`, `features`, `world_refs`, `schema_version`.

### 4.2 `Rule Engine Output` v1 (produced by Rules, consumed by DER)
-   Fields: `rule_output_id`, `schema_version`, `status`, `matches` (with `action_proposal`), `guardrails_triggered`.

### 4.3 `Decision Package` v1 (produced by DER, consumed by IEE)
-   Fields: `decision_id`, `schema_version`, `task_id`, `selected_action` (name, parameters, preconditions, expected_effects), `safety_assertions`, `confidence_score`, `human_review_required`, `reasoning_trace_ref`, `references`, `consultations` (provider “LLM Conductor”).

### 4.4 `Reasoning Trace` v1 (produced by DER)
-   A trace graph of inputs, rule firings, consultations, and synthesis steps.

## 5. Conversations: LLM Conductor and beyond
-   DER initiates `ConsultationRequest` conversations with **LLM Conductor** when ambiguity or novelty warrants.
-   All conversations adhere to the IAE conversation envelope, error codes, and version negotiation.

## 6. Integration boundaries
-   **ICCM → IDE:** `Structured Context` is the contract.
-   **IDE → IEE:** `Decision Package` is the sole directive interface.
-   **IDE ↔ State Manager (IAE):** Read world/task state; persist `Decision Package` and `Reasoning Trace` links; subscribe to `Execution Outcome Package` events for learning.
-   **IDE ↔ Half-MADs:** Conversations-only, registry-based discovery.

## 7. Conclusion
IDE delivers a principled hybrid decision core for MAD agents within the quaternary structure. By adopting canonical contracts and conversation protocols, IDE ensures decisions are transparent, auditable, and controllable.

---
## Appendix: Terminology
-   **LLM Conductor:** Half-MAD providing LLM Orchestra capability.
-   **Thinking Engine:** CET + Rules Engine + DER + State Manager.
-   **Decision Package:** The directive from DER to the Doing Engine.
-   **Execution Outcome Package:** The Doing Engine’s report to the State Manager.

***

### 3. 00_IEE_Intelligent_Execution_Engineering_v1.1.md (Corrected)

--- 00_IEE_Intelligent_Execution_Engineering_v1.1.md ---
# Paper 00: Intelligent Execution Engineering (IEE) - Master Document

**Version:** 1.1
**Date:** 2025-10-06
**Status:** DRAFT - Strengthened placeholder with contracts and feedback loops
**Repository:** Joshua (IEE discipline within IAE ecosystem)
**Synthesized by:** Council of Elders

---

## Changelog
- **v1.1 (2025-10-06):** Normalized to quaternary structure (ICCM + IDE + IEE + IAE). Adopted canonical contracts (consumes `Decision Package`; produces `Execution Outcome Package`). Clarified boundary with State Manager and DER re-engagement triggers. Aligned all terminology.
- **v1.0 (2025-10-06):** Initial placeholder framing IEE’s scope.

---

## Executive Summary

**Intelligent Execution Engineering (IEE)** is the discipline of execution. It produces **Doing Engines** that translate decisions into safe, effective actions. Doing Engines validate directives, orchestrate tools/APIs, monitor progress, and synthesize outcomes. They consume `Decision Packages` (from IDE/DER) and produce `Execution Outcome Packages` which are persisted by the IAE State Manager, closing the architecture's core feedback loop.

## 1. Foundations
### 1.1 Role in the quaternary structure
-   **ICCM:** context engineering (CET)
-   **IDE:** decision engineering (Rules Engine + DER)
-   **IEE:** execution engineering (Doing Engines)
-   **IAE:** assembly and State Manager

### 1.2 Execution engineering principles
-   Safety-first execution with invariant revalidation.
-   Domain specialization through patterns (tool execution, API orchestration).
-   Observability and reproducibility.
-   Feedback loops as first-class citizens.

## 2. Doing Engine architecture
### 2.1 Components
-   **Decision Validator:** Checks preconditions, safety assertions, and entitlements.
-   **Tool Orchestrator:** Selects tools/APIs and binds parameters.
-   **Execution Monitor:** Tracks progress and detects drift against expected effects.
-   **Outcome Synthesizer:** Compares observed vs. expected effects and produces the `Execution Outcome Package`.

### 2.2 Interface contracts (canonical)
-   **Input: `Decision Package` v1** (from DER)
    -   IEE uses fields: `decision_id`, `task_id`, `selected_action` (name, parameters, preconditions, expected_effects), `safety_assertions`, `confidence_score`, `human_review_required`, `reasoning_trace_ref`, `references`, `schema_version`.
-   **Output: `Execution Outcome Package` v1** (to State Manager)
    -   IEE produces fields: `outcome_id`, `decision_id`, `status`, `observed_effects`, `deviations`, `safety_validation_results`, `telemetry`.

### 2.3 Safety invariant revalidation
-   All `safety_assertions` in the `Decision Package` are rechecked before execution.
-   On failure, the Doing Engine aborts and emits an `Execution Outcome Package` with a failure status and diagnostics.

### 2.4 DER re-engagement
-   **Triggers:** Precondition unsatisfied, safety violations, unresolvable errors, significant deviations.
-   **Mechanism:** Emit an `Execution Outcome Package` with `reengagement_advice` and notify DER via a State Manager event.

## 3. Execution patterns
-   **Tool Execution:** Sandboxed shell, git, filesystem actions.
-   **API Orchestration:** REST/gRPC/DB calls with rate limiting and schema validation.
-   **Human Interaction:** UI prompts and confirmations.

## 4. Integration boundaries
-   **IDE → IEE:** `Decision Package` v1 is the sole directive interface.
-   **IEE → State Manager (IAE):** Persist `Execution Outcome Package` and update Execution State.
-   **IEE → ICCM:** No direct interface; effects observed by the State Manager drive subsequent context updates.
-   **IEE ↔ Half-MADs:** Rare, policy-gated conversations only (e.g., to **LLM Conductor** for non-decisional consults); the default path is DER re-engagement.

## 5. Conclusion
IEE formalizes execution as a first-class discipline in the quaternary IAE structure. By standardizing interfaces with IDE and the State Manager, enforcing safety revalidation, and closing the loop with detailed outcomes, Doing Engines make MAD agents not just smart, but reliably effective and governable.

---
## Appendix: Key terms
-   **Decision Package:** The directive from DER to the Doing Engine.
-   **Execution Outcome Package:** The Doing Engine’s report to the State Manager.
-   **Re-engagement:** A policy-driven request for DER assistance when execution cannot proceed.
-   **LLM Conductor:** A Half-MAD offering the LLM Orchestra capability via conversations (not part of the Thinking Engine).

***

### 4. 00_ICCM_Intelligent_Context_Conversation_Management_v1.1.md (Corrected)

--- 00_ICCM_Intelligent_Context_Conversation_Management_v1.1.md ---
# Paper 00: Intelligent Context and Conversation Management (ICCM) - Master Document

**Version:** 1.1
**Date:** 2025-10-06
**Status:** DRAFT - Council of Elders Synthesis (v1.1)
**Repository:** Joshua (ICCM discipline within IAE ecosystem)
**Synthesized by:** Council of Elders

---

## Changelog
- **v1.1 (2025-10-06):** First complete version. Aligned with the normalized quaternary structure (ICCM + IDE + IEE + IAE). Defines the Context Engineering Transformer (CET) as the first component of the Thinking Engine. Establishes the `Structured Context` contract as its sole output. Introduces the transformation-only principle and a progressive training methodology.
- **v1.0 (2025-10-06):** Placeholder for the ICCM discipline.

---

## Executive Summary

**Intelligent Context and Conversation Management (ICCM)** is the discipline of context engineering. It produces the **Context Engineering Transformer (CET)**, the first of four components in the MAD architecture's Thinking Engine. The CET's sole responsibility is to receive raw, unstructured inputs and transform them into the canonical `Structured Context` contract required by the IDE discipline.

A core principle of ICCM is that the CET is **transformation-only**; it classifies, extracts, condenses, and formats information but does not generate novel content or perform synthesis. This ensures the cognitive entry point is deterministic, auditable, and free from the risk of generative hallucination. ICCM is the foundational layer of the **quaternary structure**, enabling principled decision-making by providing clean, well-formed context.

## 1. Introduction: The Discipline of Context Engineering
Raw inputs from users, APIs, and sensors are inherently ambiguous, verbose, and unstructured. Attempting to make decisions directly from this raw data is inefficient and unsafe. ICCM formalizes the pre-processing of this data as a distinct engineering discipline.

-   **Role in the Quaternary Structure:** ICCM is the first stage. Its output, the CET, feeds the IDE (decisions), which in turn directs the IEE (execution), with IAE providing assembly and state management for the entire system.
-   **Core Product:** The Context Engineering Transformer (CET).
-   **Core Principle:** Transformation, not generation. Synthesis and reasoning are the responsibilities of IDE's DER, which consults the LLM Conductor Half-MAD for such tasks.

## 2. Theoretical Foundation
### 2.1 Context as a Prerequisite for Intelligence
Effective decisions are impossible without well-framed context. The CET's mission is to structure the "what" and "why" of a task, so the IDE can focus on the "how."

### 2.2 The Transformation-Only Constraint
The CET is strictly forbidden from generative synthesis. This constraint is critical for:
-   **Auditability:** Every field in the output `Structured Context` can be traced back to a specific piece of the raw input.
-   **Safety:** Prevents hallucinations and fabricated data from entering the decision-making process at its earliest stage.
-   **Efficiency:** Transformation tasks can be accomplished with smaller, faster, and cheaper models than large-scale generative ones.
-   **Separation of Concerns:** Allows the DER and the LLM Conductor to handle complex reasoning under controlled conditions, after the context is securely framed.

### 2.3 The Feedback Loop
The quality of a CET is measured by the success of the downstream execution. ICCM leverages the `Execution Outcome Package` stored in the IAE State Manager as a primary source of feedback for retraining and improving context transformation models.

## 3. CET Architecture
The CET is a pipeline of specialized transformation components.

### 3.1 Input Ingestor
-   Accepts multi-modal raw inputs (e.g., text, user queries, API responses, system events).

### 3.2 Classification & Routing
-   Identifies the user's intent, the task type, and the relevant domain.
-   Routes the input to the appropriate extraction and condensation models.

### 3.3 Feature Extraction & Condensation
-   Extracts entities, parameters, and key features from the input.
-   Summarizes verbose text into concise facts.
-   Normalizes data formats (e.g., dates, currencies).

### 3.4 Constraint & Policy Precheck
-   Validates inputs against predefined schemas and static policy checks; flags violations and missing required information for IDE. CET does not enforce policy or make final decisions.

### 3.5 Context Assembler
-   Gathers the outputs from all previous stages.
-   Constructs the final `Structured Context` object, ensuring it conforms to the canonical contract defined in IAE Paper 00 v1.1.

## 4. Canonical Contract (ICCM View)
*(Authoritative definition in IAE Paper 00 v1.1)*

### 4.1 `Structured Context` v1 (produced)
The CET's sole output is this contract, delivered to the IDE's Rules Engine.
-   **Key Fields Produced:** `context_id`, `schema_version`, `task_id`, `problem_frame` (objectives, constraints), `features` (name, value), `world_refs` (world_version_id).
-   This contract acts as a hard boundary, decoupling context engineering from decision engineering.

## 5. Integration with the MAD Ecosystem
-   **Input:** Receives raw data from the agent's external interfaces.
-   **Output (ICCM → IDE):** Publishes the `Structured Context` contract for consumption by the Rules Engine. This is the primary handoff in the Thinking Engine's flow.
-   **Feedback (State Manager → ICCM):** The CET's training process subscribes to `Execution Outcome Package` events from the IAE State Manager. A high frequency of `deviations` or `failure` statuses correlated with a specific context structure can trigger model retraining.

## 6. Progressive Training Methodology
CETs are trained and improved through a four-phase lifecycle.

-   **Phase 1: Heuristic & Rule-Based:** Initial bootstrapping using regular expressions and keyword matching for basic classification and extraction.
-   **Phase 2: Supervised Fine-Tuning:** Use human-annotated datasets (raw input → correct `Structured Context`) to train smaller, specialized transformer models for each CET component.
-   **Phase 3: Reinforcement Learning from Human Feedback (RLHF):** Domain experts rate the quality and accuracy of the CET's `Structured Context` output, providing a reward signal to further refine the models.
-   **Phase 4: Reinforcement Learning from Agent Feedback (RLAF):** Automate the feedback loop by using the `status` field from the `Execution Outcome Package`. Successful executions provide a positive reward; failures provide a negative reward, allowing the CET to learn which context structures lead to effective outcomes.

## 7. Conclusion
ICCM establishes context engineering as the disciplined, safety-critical foundation of the MAD architecture. By producing the CET—a transformation-only engine that delivers a canonical `Structured Context`—ICCM ensures that the entire cognitive process begins with a clear, auditable, and well-formed understanding of the problem, enabling the rest of the quaternary to operate with greater safety and effectiveness.

---
## Appendix: Master Glossary (selected)
-   **ICCM:** Intelligent Context and Conversation Management; the discipline of context engineering.
-   **CET:** Context Engineering Transformer; the transformation-only component produced by ICCM.
-   **Transformation-Only:** The core principle that the CET must not generate novel content, only classify, extract, and structure existing information.
-   **Structured Context:** The canonical contract produced by the CET and consumed by the IDE.
-   **Quaternary Structure:** The four-part disciplinary model: ICCM (context), IDE (decisions), IEE (execution), and IAE (assembly/state).
