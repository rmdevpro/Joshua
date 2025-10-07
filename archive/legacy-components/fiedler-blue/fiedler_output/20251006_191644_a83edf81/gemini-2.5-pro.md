Here is the corrected version of the IEE paper, with the requested changes applied to Section 2.2.

---
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
    -   IEE produces fields: `outcome_id`, `schema_version`, `decision_id`, `status`, `observed_effects`, `deviations`, `safety_validation_results`, `telemetry`, `artifacts`, `world_version_id_before`, `world_version_id_after`, `reengagement_advice`.
    -   The Doing Engine must populate `schema_version` per the canonical IAE schema and treat other fields per their intended use (e.g., `artifacts` and `reengagement_advice` may be empty when not applicable).

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
