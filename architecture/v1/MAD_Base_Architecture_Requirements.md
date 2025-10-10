# MAD Base Architecture Requirements

## Version: 1.0
## Status: Approved

---

## Overview
This document specifies the foundational requirements for the core MAD (**[CORRECTED]** Multipurpose Agentic Duo) structure. It defines the composition, lifecycle, and extension mechanisms for all MAD instances in the V1 ecosystem, while establishing the architectural runway for future versions.

---

## Requirements

### 1. Core Composition
#### Requirement 1.1: Composite Duo Structure
**Priority:** High
**[CORRECTED]** **Description:** Every MAD (with the exception of Rogers) MUST be composed of two primary component containers: an `ActionEngine` and a `ThoughtEngine`.
- The `ActionEngine` is the execution framework, containing the `MCP Server` as its core internal interface, along with tools and resource connectors.
- The `ThoughtEngine` is the cognitive framework. For V1, its primary component is `Imperator`. The architecture MUST allow for additional cognitive components to be added in future versions (e.g., DTR, LPPM, CET).

#### Requirement 1.2: Base Class Implementation
**Priority:** High
**Description:** The system MUST provide abstract base classes, `ActionEngineBase` and `ThoughtEngineBase`, that all MAD implementations inherit from. These classes will define the core interface for receiving messages, interacting with the component's counterpart, and sending responses.

### 2. MAD Lifecycle
#### Requirement 2.1: Ephemeral MAD (eMAD) Lifecycle
**Priority:** High
**Description:** The system, through a factory MAD like Hopper, MUST support the dynamic instantiation and destruction of ephemeral MADs (eMADs) for specific tasks. eMADs are stateless and retrieve all necessary context from the conversation history in Rogers upon instantiation.
**Example:** `@Hopper #spawn eMAD=SeniorDev role=code-review`

#### Requirement 2.2: Persistent Role-Based Learning
**Priority:** Medium
**Description:** While eMAD instances are ephemeral, their role-based learnings MUST be persistent. All conversational history associated with a role (e.g., "SeniorDev") shall be stored in Rogers, allowing future eMADs of the same role to access and learn from past interactions.

### 3. Extensibility
#### Requirement 3.1: ActionEngine Extension Mechanism
**Priority:** High
**Description:** The `ActionEngine` MUST provide a well-defined mechanism for injecting plugins or modules that grant new capabilities (e.g., accessing a new API). This allows MADs to be extended without altering their core logic.

**[CORRECTED]**
#### Requirement 3.2: ThoughtEngine Extension Mechanism
**Priority:** Medium
**Description:** The `ThoughtEngine` architecture MUST support extension. While V1 focuses on `Imperator`, the design must accommodate the future integration of additional cognitive components, such as pre-processing filters or specialized decision models, without requiring a fundamental architectural change.

### 4. System Exceptions
#### Requirement 4.1: Rogers Architectural Exception
**Priority:** High
**Description:** The Rogers messaging bus is a special-case MAD. It MUST be implemented as an `ActionEngine`-only component. It does not possess a `ThoughtEngine` as its routing and state management logic is deterministic.

---

## Success Criteria
- ✅ A developer can create and deploy a new MAD by inheriting from the base classes in under an hour.
- ✅ The Hopper MAD can successfully spawn an eMAD, which performs a task and is then terminated.
- ✅ A newly spawned eMAD can read its role's past conversations from Rogers to gain context.
- ✅ Rogers is implemented and verified to operate without a ThoughtEngine component.

---

## Dependencies
- Rogers Messaging Bus Requirements
- LLM Client Library Requirements (for `Imperator` integration into the `ThoughtEngine`)

---

## Notes
**[CORRECTED]** This V1 architecture establishes the foundational `ThoughtEngine` container. The concept of role-based learning is a prerequisite for the V2 LPPM component, which will be integrated into this extensible `ThoughtEngine` framework.
```
