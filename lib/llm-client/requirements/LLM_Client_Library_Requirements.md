# LLM Client Library Requirements

## Version: 1.1
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document specifies the requirements for the LLM Client Library, a shared package used by MADs to interact with the broader MAD ecosystem and underlying LLM services. This updates the library from v1.0 to v1.1.

---

## Requirements

### 1. Helper MCP Integration
#### Requirement 1.1: High-Level Helper Access
**Priority:** High
**Description:** The library MUST provide high-level, asynchronous methods for interacting with the standard V1 Helper MCPs. These methods shall abstract the underlying conversational message exchange.
**Example:** `result = await client.code_executor.run(script="print('hello')")`

### 2. State Management
#### Requirement 2.1: State Management via Rogers
**Priority:** High
**Description:** The library MUST provide methods for reading from and writing to a MAD's state, which is persisted in a dedicated conversation on the Rogers bus.
**Example:** `await client.state.set('key', 'value')` and `value = await client.state.get('key')`

### 3. Initialization
#### Requirement 3.1: Client Initialization and Discovery
**Priority:** High
**Description:** The library's client object MUST be initialized through a discovery process that connects to Rogers. This process shall be used to locate essential services like Fiedler.
**Example:** On init, client sends `@Rogers #find_service type=LLM_Gateway` to locate Fiedler.

### 4. LLM Orchestration
#### Requirement 4.1: Fiedler Integration for All LLM Calls
**Priority:** High
**Description:** All outbound requests to LLMs (including the MAD's own Imperator) MUST be routed through the Fiedler MAD. The library shall handle this routing transparently.

### 5. eMAD Support
#### Requirement 5.1: eMAD Client Loading Mechanism
**Priority:** High
**Description:** The library MUST support a specific initialization path for ephemeral MADs (eMADs). When an eMAD starts, the client library will be responsible for connecting to Rogers and loading the necessary role-based context from the conversation history.

**REVISED:**
### 6. Internal MAD Communication
#### Requirement 6.1: Direct Component Communication
**Priority:** High
**Description:** The library MUST facilitate direct, low-latency communication between a MAD's ThoughtEngine and ActionEngine without routing through Rogers. This internal cognitive loop is a performance-critical path and is an exception to the "all communication via Rogers" rule for inter-MAD messages.

---

## Success Criteria
- ✅ A MAD can use the library to execute code on the Code Execution MCP with a single line of code.
- ✅ A MAD can persist a value using `client.state.set()` and retrieve the same value after a restart.
- ✅ All LLM calls made from a MAD are verified to be routed through and logged by Fiedler.
- ✅ An eMAD, upon startup, correctly loads its context using the client library.

---

## Dependencies
- Rogers Messaging Bus Requirements
- Helper MCP Infrastructure Requirements
- Fiedler MAD (as a service)

---

## Notes
The "Open Questions" section from v1.0 has been resolved. This version reflects the finalized V1 architecture decisions.

---

*Requirements v1.1 - The toolkit for every agent.*

---
---