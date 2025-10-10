# Rogers Messaging Bus Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document outlines the requirements for Rogers, the central messaging bus and nervous system of the MAD V1 ecosystem. Rogers is responsible for managing conversations, routing messages, and persisting all state and history.

---

## Requirements

### 1. Core Abstractions
#### Requirement 1.1: Conversation as a First-Class Object
**Priority:** High
**Description:** Rogers MUST treat the "conversation" as its primary data object. It must provide functionalities to create, join, leave, and archive conversations. Each conversation shall have a unique identifier and an access control list.
**Example:** `@Rogers #create_conversation name=ProjectAlpha`

### 2. Message Handling
**REVISED:**
#### Requirement 2.1: @mention-based Routing
**Priority:** High
**Description:** Rogers MUST route messages to the appropriate MAD participant(s) based on `@mention` handles within the message content. Messages without explicit @mentions MUST be rejected by Rogers with an `#error` tag returned to the sender. This enforces Tenet 1 by preventing unintentional broadcast behavior.

**REVISED:**
#### Requirement 2.2: Tag-based Filtering Support
**Priority:** Medium
**Description:** Rogers MUST provide a mechanism for clients to subscribe to or filter messages within a conversation based on the presence of specific tags (e.g., `#error`, `#human`, `#metric`).

### 3. State Persistence
#### Requirement 3.1: Universal State Persistence
**Priority:** High
**Description:** All conversational history and MAD state MUST be durably persisted by Rogers. Rogers is the single source of truth for the state of the entire system. MADs themselves are to be treated as stateless compute units.

### 4. Identity and Guarantees
#### Requirement 4.1: Identity and Authentication
**Priority:** High
**Description:** Rogers MUST be able to reliably identify the sender of every message and authenticate MADs as they connect to the bus.

#### Requirement 4.2: Message Delivery Guarantees
**Priority:** High
**Description:** Rogers MUST guarantee at-least-once delivery for all messages to their intended recipients within a conversation.

#### Requirement 4.3: Message Ordering
**Priority:** High
**Description:** Within a single conversation, Rogers MUST guarantee that messages are persisted and delivered in the order they were received.

### 5. Access Control
#### Requirement 5.1: Conversation Access Control
**Priority:** High
**Description:** Rogers MUST enforce access control on conversations. A MAD must be explicitly permitted to join a conversation before it can send or receive messages within it.

---

## Success Criteria
- ✅ A message sent by MAD-A to `@MAD-B` is delivered only to MAD-B with a latency of <100ms.
- ✅ If a MAD crashes and restarts, it can retrieve its full conversation history from Rogers.
- ✅ An unauthorized MAD is prevented from joining a private conversation.
- ✅ Message history is stored durably and survives a restart of the Rogers service.

---

## Dependencies
- Security & Permissions Baseline Requirements

---

## Notes
Rogers is the most critical single component in the V1 architecture. Its implementation is ActionEngine-only.

---

*Requirements v1.0 - The one conversation to rule them all.*

---
---