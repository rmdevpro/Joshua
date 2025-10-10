# Rogers Messaging Bus Requirements

## Version: 1.0
## Status: Approved

---

## Overview
This document details the requirements for Rogers, the central messaging bus of the MAD (**[CORRECTED]** Multipurpose Agentic Duo) ecosystem. Rogers is a specialized, persistent MAD responsible for routing all conversations, persisting history, and managing system state.

---

## Requirements

### 1. Core Architecture
#### Requirement 1.1: ActionEngine-Only Implementation
**Priority:** High
**[CORRECTED]** **Description:** Rogers is a unique architectural exception. It MUST be implemented as an `ActionEngine`-only MAD. It has no `ThoughtEngine`, as its functions of routing, persistence, and state management are purely deterministic and do not require cognitive processing.

#### Requirement 1.2: Message Persistence
**Priority:** High
**Description:** Rogers MUST durably persist every message that passes through it. This conversational history is the source of truth for all system state and is critical for auditability and context reconstruction for eMADs.

### 2. Routing and Delivery
#### Requirement 2.1: @-Mention Routing
**Priority:** High
**Description:** Rogers MUST route messages to their intended recipient(s) based on `@-mentions` in the message body (e.g., `@Fiedler`, `@Dewey`).

#### Requirement 2.2: Guaranteed Delivery
**Priority:** Medium
**Description:** Rogers SHOULD provide at-least-once delivery guarantees for messages to ensure reliable communication between MADs.

### 3. State Management
#### Requirement 3.1: Conversation State
**Priority:** High
**Description:** Rogers MUST manage the state of all conversations, including tracking participants, message sequences, and topic threads (identified by hashtags, e.g., `#code-review-123`).

---

## Success Criteria
- ✅ Rogers correctly routes a message from `MAD-A` to `MAD-B` based on an `@-mention`.
- ✅ A terminated eMAD's entire conversation history can be retrieved from Rogers.
- ✅ **[CORRECTED]** Architectural review confirms that the Rogers implementation contains only `ActionEngine` components and no `ThoughtEngine`.
```
