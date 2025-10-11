Excellent. As the Senior Member, I have synthesized the critical feedback from both Junior Members. The identified security and reliability gaps are valid and must be addressed for a viable V1 release. My approach is to accept and integrate all critical fixes that can be implemented pragmatically, while clearly deferring more complex architectural changes to maintain V1 velocity.

This revised document is the new source of truth.

---

### **V1 MAD Group Requirements - Unified Synthesis (Revised)**

**Document Version:** 1.1
**Status:** Approved for Design Phase
**Synthesizer:** Senior Member

### **Changelog (v1.0 to v1.1)**

This revision incorporates critical feedback from peer review, focusing on hardening the V1 architecture for a production-ready deployment.

| Change Type | Area | Rationale & Impact |
| :--- | :--- | :--- |
| **SECURITY (Critical)** | Redis Bus | Added **REQ-JC-09** mandating Redis authentication. An unauthenticated message bus, even on an internal network, is an unacceptable security risk. This is a simple, high-impact fix. |
| **SECURITY (Critical)** | SSH Access | Added **REQ-JS-05** for network isolation and **REQ-JS-06** for a baseline key management process. Prevents accidental exposure and hardens the debug interface against unauthorized access. |
| **RELIABILITY (Critical)** | Fiedler State | Updated **REQ-FD-04** to mandate SQLite's Write-Ahead Logging (WAL) mode. This is a low-effort configuration change that significantly improves crash-resilience and data integrity. |
| **RELIABILITY** | Fiedler Errors | Updated **REQ-FD-06** to require more detailed error state capture (e.g., stack traces). This makes debugging distributed failures, a high-likelihood problem, significantly easier. |
| **SECURITY** | Imperator | Added **REQ-FD-10** to enforce read-only, whitelisted access to internal state. This provides a pragmatic security boundary for the LLM, preventing potential query exploits. |
| **DEFERRED (V1+)** | Redis HA | **Rationale:** Implementing Redis Sentinel/Streams is a significant operational and architectural task. V1 will accept Redis as a single point of failure (with auto-reconnect for transience) to prioritize core feature delivery. This risk is tracked. |
| **DEFERRED (V1+)** | Observability | **Rationale:** A full Prometheus metrics stack is out of scope for V1. We will rely on enhanced logging and the SSH `mad-state` commands for initial operational visibility. |

---

### **1. Unified Requirements Document**

#### **1.1. Core Libraries (Prerequisites)**

**A. `joshua_conversation` v0.1: Rogers Bus Client**
*   **REQ-JC-01:** Provide a Python async library for connecting to the Rogers Conversation Bus.
*   **REQ-JC-02:** Implement the client using **Redis Pub/Sub** as the V1 transport layer.
*   **REQ-JC-03:** Support sending direct (to a specific recipient), broadcast, and topic-based messages.
*   **REQ-JC-04:** Support receiving messages via a callback-based decorator (`@client.on_message`).
*   **REQ-JC-05:** Define and handle a standard JSON message envelope (see API section).
*   **REQ-JC-06:** Automatically manage `conversation_id`s, generating a new UUID if one is not provided.
*   **REQ-JC-07:** Implement automatic reconnection with exponential backoff if the Redis connection is lost.
*   **REQ-JC-08:** Integrate with `joshua_logger` for all internal logging.
*   **REQ-JC-09 (New):** The client MUST support authentication with the Redis server via a password provided in its configuration. Connection attempts without valid authentication MUST fail.

**B. `joshua_ssh` v0.1: MAD SSH Server**
*   **REQ-JS-01:** Provide a mechanism to run an **OpenSSH server** within each MAD's Docker container.
*   **REQ-JS-02 (Updated):** The SSH server must use key-based authentication only; password authentication MUST be disabled.
*   **REQ-JS-03:** Provide a standardized set of shell commands (`mad-status`, `mad-logs`, `mad-state`, `mad-config`).
*   **REQ-JS-04:** Provide a Python library with decorators for MADs to register custom commands and expose internal state.
*   **REQ-JS-05 (New):** The SSH server MUST be configured to only accept connections from within the internal Docker network. It MUST NOT be exposed to the host's public interfaces.
*   **REQ-JS-06 (New):** A secure, documented process for generating and distributing `authorized_keys` files MUST be established for V1. Keys must be mounted into the container as a read-only file.

#### **1.2. Grace V0: Conversation Bus Relay**

*   **REQ-GR-01:** Implement a MAD that acts as a bridge between the existing MCP protocol and the Rogers Conversation Bus.
*   **REQ-GR-02:** Expose MCP tools: `grace_send_message`, `grace_poll_messages`, `grace_subscribe`.
*   **REQ-GR-03:** Utilize `joshua_conversation` to connect to and communicate with the Rogers bus.
*   **REQ-GR-04:** Maintain a simple, in-memory, per-client message queue with a configurable size limit (e.g., 100 messages) and an LRU (Least Recently Used) eviction policy to prevent memory exhaustion.

#### **1.3. Fiedler V1: Conversational Orchestrator**

*   **REQ-FD-01 (Imperator):** Integrate an LLM-based reasoning engine (Imperator) into Fiedler.
*   **REQ-FD-02 (Conversational Interface):** Add a new MCP tool, `fiedler_converse`, that accepts natural language queries and routes them to the Imperator.
*   **REQ-FD-03 (Backward Compatibility):** All existing Fiedler tools (`fiedler_send`, etc.) must remain fully functional.
*   **REQ-FD-04 (Updated - Task State Management):** Implement a robust state management system using an **in-memory dictionary for active tasks, backed by a SQLite database for persistence.** The database MUST be configured to use Write-Ahead Logging (WAL) mode. State must survive MAD restarts.
*   **REQ-FD-05 (Visibility Tools):** The Imperator must be able to access internal Fiedler state to answer queries like "What is the status of my tasks?".
*   **REQ-FD-06 (Updated - Error Handling):** Failures in background tasks must be captured and stored in the task state with a distinct 'failed' status, including the error message and stack trace. This state must be immediately visible via status queries. No silent failures.
*   **REQ-FD-07 (Streaming):** Support streaming token responses back to the original caller.
*   **REQ-FD-08 (Notifications):** Upon task completion or failure, Fiedler must publish a notification message to the Rogers bus via `joshua_conversation`, directed to the original requester.
*   **REQ-FD-10 (New - Imperator Security):** The Imperator's access to internal Fiedler state (per REQ-FD-05) MUST be read-only. Access shall be limited to a whitelist of pre-defined state query functions to prevent arbitrary data exposure.

---

### **2. Technology Decisions with Rationale**

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Conversation Bus** | **Redis Pub/Sub** | **Pragmatic & Performant.** For V1, it is simple, fast, has mature libraries, and avoids the operational overhead of systems like RabbitMQ or NATS. Its "at-most-once" delivery is acceptable for the initial notification use case. V1 requires password authentication. |
| **Fiedler Task State** | **SQLite (WAL Mode) + In-Memory Cache** | **Balanced & Robust.** This hybrid approach provides the performance of in-memory access while ensuring durability and crash-resilience via a zero-dependency SQLite database in WAL mode. |
| **MAD Debug Access** | **OpenSSH Server** | **Standard & Secure.** Using the industry-standard OpenSSH is more secure and reliable than a custom solution. V1 requires key-only authentication and network isolation. |

---

### **3. Implementation Phases with Dependencies**

*(No changes to the implementation plan)*

```mermaid
graph TD
    subgraph "Phase 1: Foundation (1-2 weeks)"
        A[Task 1.1: joshua_conversation]
        B[Task 1.2: joshua_ssh]
    end
    subgraph "Phase 2: Bridge (1 week)"
        C[Task 2.1: Grace V0]
    end
    subgraph "Phase 3: Fiedler Core Upgrade (2-3 weeks)"
        D[Task 3.1: Task State (SQLite)]
        E[Task 3.2: Imperator & Converse]
        F[Task 3.3: Bus Integration]
    end

    A --> C
    A --> F
    C --> F
    D --> E
    D --> F
```

---

### **4. API Designs**

*(No changes to API designs)*

---

### **5. Risk Mitigation Strategies (Updated)**

| Risk Category | Risk Description | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Technical** | **Async Complexity:** Improperly handled background tasks in Fiedler lead to memory leaks or silent failures. | High | High | Implement a dedicated `TaskManager` class. All tasks must have exception handlers that update the persistent state with detailed error info (REQ-FD-06). |
| **Technical** | **Message Loss:** Redis Pub/Sub is "at-most-once". If a MAD is down, it will miss messages. | Medium | Medium | **V1:** Accept this risk for non-critical notifications. System must be resilient to missed notifications. **V1+:** Plan to migrate to Redis Streams for "at-least-once" delivery. |
| **Technical** | **Redis as a Single Point of Failure:** If the Redis server goes down, the entire conversation bus stops. | Medium | High | **V1:** Accept this risk. The `joshua_conversation` client's auto-reconnect logic will handle transient failures. **V1+:** Implement Redis Sentinel for High Availability. |
| **Security** | **Unauthenticated Bus:** *(Mitigated)* | **LOW** | Medium | **V1:** Risk mitigated by mandating Redis authentication (REQ-JC-09). Access to the bus requires credentials. |
| **Security** | **SSH Key Lifecycle Management:** Improper handling, rotation, or auditing of keys grants unauthorized access over time. | Medium | High | **V1:** Establish a secure baseline for key generation and read-only distribution (REQ-JS-06). **V1+:** Introduce automated key rotation and auditing. |
| **Operational** | **Debugging Distributed Systems:** Tracing a request through Grace, the bus, and Fiedler can be difficult. | High | Medium | Enforce a standard `correlation_id` that is generated at the start of a request and passed through every component and log message. Centralized logging via `joshua_logger` is critical. |
