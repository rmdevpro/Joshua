# Helper MCP Infrastructure Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document specifies requirements for Helper MCPs (Master Control Programs). Helper MCPs are persistent, conversational MADs that provide core, system-wide services, acting as the LLM-native replacement for a traditional microservices architecture.

---

## Requirements

### 1. Service Model
#### Requirement 1.1: Conversational Service Interface
**Priority:** High
**Description:** All Helper MCPs MUST expose their functionality exclusively through the MAD conversational interface. They shall not expose any traditional API endpoints (e.g., REST, gRPC). A client "uses" a Helper MCP by talking to it.

#### Requirement 1.2: V1 Helper MCP Implementations
**Priority:** High
**Description:** The V1 system MUST include the following persistent Helper MCPs:
- **Sequential Thinking MAD:** To perform chain-of-thought style reasoning.
- **Code Execution MAD:** To securely execute code snippets.
- **Reflection Server MAD:** To analyze and critique its own or another MAD's output.
- **RAG Service MAD:** To perform Retrieval-Augmented Generation against a knowledge base.

### 2. Discovery and Interaction
#### Requirement 2.1: Service Discovery via Rogers
**Priority:** High
**Description:** Helper MCPs MUST register with Rogers. Client MADs MUST be able to discover available Helper MCPs by querying Rogers.
**Example:** Client sends `@Rogers #find_service type=RAG`, Rogers replies with the MCP's handle.

#### Requirement 2.2: Conversational Request/Response Pattern
**Priority:** High
**Description:** Interactions with Helper MCPs MUST follow a conversational request/response pattern. The client sends a request, and the MCP responds in a subsequent message, using tags to indicate status.
**Example Flow:**
1.  Client: `@CodeExecutor Please run this python: [code: print('hello')] #trace-id:123`
2.  MCP: `@ClientMAD Request received. #ack #trace-id:123`
3.  MCP: `@ClientMAD Execution complete. Output: "hello" #status:done #trace-id:123`

### 3. Concurrency
#### Requirement 3.1: Concurrent Request Handling
**Priority:** High
**Description:** Each Helper MCP MUST be able to handle concurrent conversations and requests from multiple different client MADs simultaneously, maintaining context for each conversation independently.

**REVISED:**
### 4. Error Handling
#### Requirement 4.1: Standardized Error Reporting
**Priority:** High
**Description:** Helper MCPs MUST return `#error` tags with human-readable explanations for failed operations. This ensures that failures are visible, auditable, and actionable within the conversational context.
**Example:** `@ClientMAD Request failed. #error #reason:"Could not execute script due to syntax error on line 5" #trace-id:123`

---

## Success Criteria
- ✅ All four specified V1 Helper MCPs are deployed and discoverable via Rogers.
- ✅ A MAD can successfully send a Python script to the Code Execution MAD and receive the output in a reply message.
- ✅ Two different MADs can talk to the RAG Service MAD at the same time without their requests interfering.
**REVISED:**
- ✅ When a script sent to the Code Execution MAD fails, it returns a message with an `#error` tag and a clear explanation.

---

## Dependencies
- MAD Base Architecture Requirements
- Rogers Messaging Bus Requirements
- LLM Client Library Requirements

---

## Notes
This conversational approach to infrastructure is a core tenet of the MAD architecture.

---

*Requirements v1.0 - Infrastructure that talks back.*

---
---