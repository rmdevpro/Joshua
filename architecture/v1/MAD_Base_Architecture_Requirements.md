# MAD Base Architecture Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document specifies the foundational requirements for the core MAD structure. It defines the composition, lifecycle, and extension mechanisms for all MAD instances in the V1 ecosystem.

---

## Requirements

### 1. Core Composition
#### Requirement 1.1: Composite Structure
**Priority:** High
**Description:** Every MAD (with the exception of Rogers) MUST be composed of two primary components: an `ActionEngine` that interfaces with tools and external systems, and a `ThoughtEngine` (Imperator) that provides cognitive capabilities.

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
- LLM Client Library Requirements (for Imperator integration)

---

## Notes
The concept of role-based learning is foundational for the V2 LPPM, but the persistence mechanism is a V1 requirement.

---

*Requirements v1.0 - The building blocks of agency.*

---
---