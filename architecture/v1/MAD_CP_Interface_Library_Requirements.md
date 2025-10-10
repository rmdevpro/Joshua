# MAD Conversation Protocol (CP) Interface Library Requirements

## Version: 1.0
## Status: Approved

---

## Overview
This document defines the requirements for the standard library that all MAD (**[CORRECTED]** Multipurpose Agentic Duo) components will use to communicate. This library will abstract the underlying transport mechanism (Rogers) and provide a high-level, intuitive API for sending and receiving conversational turns.

---

## Requirements

### 1. Core Functionality
#### Requirement 1.1: Connection Management
**Priority:** High
**Description:** The library MUST handle all aspects of connecting to the Rogers messaging bus, including authentication, connection pooling, and automatic reconnection.

#### Requirement 1.2: Message Serialization
**Priority:** High
**Description:** The library MUST provide a standard, versioned format for all conversational messages, including metadata such as sender, recipient(s), timestamp, and conversation ID.

### 2. API Design
#### Requirement 2.1: Fluent Interface
**Priority:** Medium
**Description:** The library SHOULD provide a fluent API for constructing and sending messages to simplify development.
**Example:** `mad.talkTo("Fiedler").withMessage("Analyze this text...").send();`

#### Requirement 2.2: Asynchronous Operations
**Priority:** High
**Description:** All network I/O operations MUST be non-blocking and asynchronous, utilizing async/await patterns or callbacks to ensure MADs remain responsive.

### 3. Component Integration
#### Requirement 3.1: Base Class Integration
**Priority:** High
**[CORRECTED]** **Description:** The library MUST be seamlessly integrated into the `ActionEngineBase` class, providing a `self.messaging` handle for all MADs to use for communication. This ensures that all interactions are standardized.

#### Requirement 3.2: Helper MCP Compatibility
**Priority:** High
**Description:** The library MUST fully support the communication patterns required by Helper MCPs, including long-running job submissions and status updates.

---

## Success Criteria
- ✅ A developer can send a message to another MAD using a single line of code.
- ✅ The library can successfully reconnect to Rogers after a network interruption without losing messages.
- ✅ **[CORRECTED]** The `ActionEngine` of a MAD can use the library to communicate both externally via Rogers and internally with its `ThoughtEngine` via the MCP Server.
```
