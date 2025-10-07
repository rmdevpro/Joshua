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

