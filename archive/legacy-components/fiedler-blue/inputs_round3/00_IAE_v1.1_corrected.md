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

