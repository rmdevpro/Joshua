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

```playfair-mermaid
graph TD
    subgraph IAE [Intelligent Agentic Engineering: The Overarching Discipline]
        direction LR
        subgraph ICCM [ICCM: Context]
            A[Context Engineering]
        end
        subgraph IDE [IDE: Decisions]
            B[Rules Engine & DER]
        end
        subgraph IEE [IEE: Execution]
            C[Doing Engines]
        end
        subgraph IAE_Core [IAE: Assembly & State]
            D[State Manager & Integration]
        end
    end

    ICCM --> IAE_Core
    IDE --> IAE_Core
    IEE --> IAE_Core

    style IAE fill:#f9f,stroke:#333,stroke-width:2px,color:#000
    style ICCM fill:#ccf,stroke:#333,color:#000
    style IDE fill:#cfc,stroke:#333,color:#000
    style IEE fill:#fcf,stroke:#333,color:#000
    style IAE_Core fill:#ffc,stroke:#333,color:#000
```

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

```playfair-mermaid
graph LR
    subgraph MAD [MAD Architecture]
        TE[Thinking Engine]
        DE[Doing Engine]
    end

    TE -- "Decision Package" --> DE
    DE -- "Execution Outcome Package" --> TE

    style TE fill:#cce5ff,stroke:#333,stroke-width:2px,color:#000
    style DE fill:#d4edda,stroke:#333,stroke-width:2px,color:#000
```

### 2.2 Thinking Engine composition (four components)
-   **CET (ICCM):** transformation-only context engineering
-   **Rules Engine (IDE):** deterministic policy, safety, and known regimes
-   **DER (IDE):** synthesis under uncertainty, multi-objective arbitration
-   **State Manager (IAE):** authoritative memory and world model
*Note: LLM Orchestra is provided externally by the **LLM Conductor** Half-MAD and consulted via conversations.*

```playfair-mermaid
C4Component
    title Thinking Engine Architecture

    System_Ext(llm_conductor, "LLM Conductor", "Half-MAD providing LLM Orchestra")

    System_Boundary(te, "Thinking Engine") {
        Component(cet, "CET", "ICCM", "Context Engineering & Transformation")
        Component(rules, "Rules Engine", "IDE", "Deterministic policy and safety")
        Component(der, "DER", "IDE", "Synthesis and arbitration under uncertainty")
        ComponentDb(state, "State Manager", "IAE", "Authoritative memory and world model")
    }

    Rel(cet, rules, "Provides Structured Context")
    Rel(rules, der, "Provides Rule Engine Output")
    Rel(der, llm_conductor, "Consults via Conversations")
    Rel(der, state, "Reads World Model & Task Context")
    Rel(cet, state, "Reads World Model & Task Context")
    Rel(rules, state, "Reads World Model & Task Context")
```

### 2.3 Doing Engine philosophy (IEE)
-   Domain-specific execution through tools and APIs
-   Safety validation, monitoring, and outcome synthesis
-   Reporting outcomes to the State Manager

### 2.4 Operational feedback loop
-   Decision → Execution → Outcome → State Update → Context Refresh → Better Decision
-   All links are standardized through canonical contracts and State Manager APIs.

```playfair-mermaid
graph TD
    A[1. Decision] --> B(2. Execution);
    B --> C{3. Outcome};
    C --> D[4. State Update];
    D --> E[5. Context Refresh];
    E --> A;

    subgraph IDE
        A
    end
    subgraph IEE
        B
    end
    subgraph IAE
        D
        E
    end
    subgraph World
        C
    end

    style IDE fill:#cfc,stroke:#333,color:#000
    style IEE fill:#fcf,stroke:#333,color:#000
    style IAE fill:#ffc,stroke:#333,color:#000
    style World fill:#eee,stroke:#333,color:#000
```

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

```playfair-mermaid
flowchart TD
    subgraph "Thinking Engine"
        direction LR
        CET(CET) -- "Structured Context" --> IDE_Sub
        subgraph IDE_Sub [IDE]
            Rules(Rules Engine) -- "Rule Engine Output" --> DER(DER)
        end
    end

    subgraph "Doing Engine (IEE)"
        DoingEngine(Execution)
    end

    subgraph "State & Audit (IAE)"
        StateManager[State Manager]
        Trace(Reasoning Trace)
    end

    DER -- "Decision Package" --> DoingEngine
    DoingEngine -- "Execution Outcome Package" --> StateManager
    DER -- "references" --> Trace

    classDef component fill:#ccf,stroke:#333,stroke-width:2px,color:#000
    class CET,Rules,DER,DoingEngine,StateManager,Trace component
```

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
