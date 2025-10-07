Here is the corrected version of Paper 01, addressing all feedback from the Council of Elders Triplet Review.

---
# Paper 01: Intelligent Agentic Engineering (IAE) - Implementation Specification

**Version:** 1.1
**Date:** 2025-11-16
**Status:** DRAFT - Council of Elders Review (Round 2 Correction)
**Repository:** Joshua (IAE)
**Parent:** Paper 00: IAE - Master Document (v1.1)
**Synthesized by:** Gemini 2.5 Pro, Synthesis Architect

---

### **Changelog v1.1**
*This version incorporates critical revisions and improvements based on feedback from GPT-4o and DeepSeek.*
-   **Data Integrity:** Re-architected State Manager around an append-only event sourcing model to enforce immutability, as mandated by Paper 00. Added `signature` field to execution records for cryptographic auditability.
-   **API Completeness:** Added `POST /contracts/reasoning_traces` endpoint to persist audit trails and `GET /tasks` endpoint with status filtering for task discovery.
-   **Protocol Robustness:** Enhanced the Conversation Protocol with mandatory `idempotency_key` in the message envelope and defined exponential backoff retry policies.
-   **Versioning & Evolution:** Clarified schema versioning with a concrete `Accept-Version` header negotiation pattern for REST APIs and registry-driven deprecation policies.
-   **Operational Resilience:** Added a new section on Chaos Engineering for MAD resilience testing. Expanded operational guidance on service lifecycle management and security (RBAC).
-   **Execution Safety:** Mandated explicit precondition validation in the core decision loop before any action is executed.
-   **Enriched Content:** Updated all data models, API references, and examples to reflect these corrective changes. Added new appendix content for schema validation failure scenarios.

---

## Executive Summary

This document, Paper 01, provides the definitive implementation specification for the Intelligent Agentic Engineering (IAE) discipline, building directly upon the theoretical foundations established in Paper 00. Where Paper 00 defined *what* to build, this paper specifies *how* to build it.

It provides concrete engineering guidance for assembling Multipurpose Agentic Duo (MAD) agents. Key specifications include:

1.  **State Manager:** Detailed API contracts (RESTful), data models (JSON Schema), and storage patterns founded on an **append-only event sourcing model** to guarantee immutability and auditability.
2.  **Conversation Protocol:** A standardized, robust asynchronous messaging protocol for all MAD-to-Half-MAD interactions, including message formats, version negotiation, **idempotency keys, and retry policies**.
3.  **Contract Management:** Strategies for schema validation, evolution through a central registry, and clear policies for handling version mismatches.
4.  **Integration Patterns:** Prescriptive sequences for data flow between ICCM, IDE, and IEE components, with an emphasis on **execution safety and precondition validation**.
5.  **Deployment & Operations:** A reference architecture based on containerized microservices, with expanded guidance on scalability, security, observability, service lifecycle, and **resilience testing via chaos engineering**.

This paper is intended for architects and engineers responsible for constructing the core infrastructure and assembling MAD agents as defined by the IAE discipline.

---

## 1. Introduction

Paper 00 established Intelligent Agentic Engineering (IAE) as the overarching discipline for agent assembly, defining the MAD architecture, the quaternary structure, and the canonical contracts that govern component interaction. This paper operationalizes those concepts.

The primary goal of this specification is to ensure that components developed within the separate disciplines (ICCM, IDE, IEE) can be integrated seamlessly and reliably into a functional, scalable, and maintainable Full MAD. Adherence to these specifications is mandatory for Council-approved agent development.

We will proceed by systematically detailing the implementation of each core IAE responsibility, beginning with its most critical component: the State Manager.

## 2. State Manager Implementation Specification

The State Manager is the authoritative memory and spine of any MAD. Its implementation must prioritize data integrity, auditability, and performance, strictly adhering to the principles of immutability mandated in Paper 00.

### 2.1 Architectural Principles

The design is guided by the global properties defined in Paper 00:

-   **Immutability via Event Sourcing:** All state changes are recorded as a sequence of immutable, cryptographically signed events. The "current state" of any resource (e.g., a Task Context) is a projection of these events. This provides a complete, auditable history and enables time-travel reads. Write operations (`POST`, `PATCH`, `PUT`) do not modify data in place; they append new events to a log.
-   **Content-Addressable Storage (CAS):** Large artifacts (e.g., files, detailed logs) are not stored directly. Instead, they are stored in a dedicated blob store (like S3 or GCS), and the State Manager holds their content-based hash (e.g., SHA-256) as an immutable reference.
-   **Optimistic Concurrency Control:** To prevent lost updates, write operations that modify a projected state (e.g., `PATCH /tasks/{task_id}`) MUST include a header specifying the expected current version of the resource (e.g., `If-Match: "ETag-value"`). The server will reject the request with a `412 Precondition Failed` if the version does not match.
-   **Tenancy and Access Control:** All resources are partitioned by a `tenant_id` and `agent_id`. API requests must be authenticated and authorized, with policies enforced at the API gateway level.

### 2.2 Data Models

The tripartite data model is implemented as three primary resource collections, which are projections of an underlying event log. (See Appendix B for full JSON Schemas).

#### 2.2.1 World Model

Represents the agent's beliefs about the external world. Modeled as a collection of versioned "facts," where each new fact creates a new, consistent `world_version_id`.

```json
// Example World Model Fact (persisted as an event)
{
  "fact_id": "fact_01J8X2Q4Z9N7R6P5E4T3W2A1S0", // ULID
  "agent_id": "agent_alpha_001",
  "created_at": "2025-11-15T10:00:00Z",
  "entity_id": "server_xyz",
  "attribute": "cpu_utilization_percent",
  "value": 85.5,
  "source": { "type": "SENSOR_READING", "source_id": "monitoring_agent_v2" },
  "valid_from": "2025-11-15T09:59:55Z",
  "valid_to": "2025-11-15T10:00:05Z",
  "confidence": 0.98,
  "world_version_id": "wv_01J8X2Q5A..."
}
```

#### 2.2.2 Task Context

Represents a specific problem or job. The object below is a *projection*. An update, such as changing the status, is recorded as a `TaskStatusChanged` event.

```json
// Example Task Context (Projection)
{
  "task_id": "task_01J8X3A8B...",
  "agent_id": "agent_alpha_001",
  "version": 2, // The sequence number of the last event applied
  "status": "IN_PROGRESS", // PENDING, IN_PROGRESS, PAUSED, COMPLETED, FAILED
  "created_at": "2025-11-15T10:05:00Z",
  "updated_at": "2025-11-15T10:15:21Z",
  "definition": {
    "objective": "Reduce CPU utilization on server_xyz to below 60%",
    "constraints": ["Do not terminate critical processes.", "Action must be completed within 5 minutes."],
    "budget": {"max_llm_calls": 10, "max_actions": 5}
  },
  "linked_context_id": "ctx_01J8X4B9C...",
  "linked_decision_ids": ["dec_01J8X5C0D..."]
}
```

#### 2.2.3 Execution State

A record of an action. Each state transition (`PENDING` -> `RUNNING` -> `SUCCESS`) is a separate, signed event.

```json
// Example Execution State (Projection)
{
  "execution_id": "exec_01J8X6D1E...",
  "task_id": "task_01J8X3A8B...",
  "decision_id": "dec_01J8X5C0D...",
  "status": "SUCCESS", // PENDING, RUNNING, SUCCESS, FAILURE, ABORTED
  "started_at": "2025-11-15T10:10:00Z",
  "completed_at": "2025-11-15T10:10:05Z",
  "action_name": "scale_down_service",
  "action_parameters": {"service_name": "billing_processor", "scale_to": 2},
  "outcome_ref": "out_01J8X7E2F...",
  "signature": "..." // Cryptographic signature of the final state event for auditability
}
```

### 2.3 Storage Patterns

A hybrid approach is specified to balance the needs of immutability, auditability, and query performance.

-   **Primary Store (Event Log):** A durable, append-only log service (e.g., Kafka, Pulsar, AWS Kinesis) is the ultimate source of truth. All state change requests are first written here as signed events.
-   **Projected State Store (Document DB):** A document database (e.g., MongoDB, DynamoDB) subscribes to the event log and builds materialized views (projections) of resources. This provides fast, indexed query capabilities for the current state.
-   **World Model Store (Graph DB or KV Store):** A graph database (e.g., Neo4j) or a high-performance key-value store is used to store and query the complex relationships within the `World Model`.
-   **Stress Testing:** The data store interactions, particularly the event consumption and projection logic, MUST be stress-tested for high-throughput, simultaneous read/write scenarios to ensure data consistency and low projection lag.

### 2.4 API Specification

The State Manager exposes a versioned, RESTful HTTP API. API versioning is handled via the `Accept-Version` header. (See Appendix A for a full reference).

**Key Endpoints:**

-   `POST /tasks`: Create a new `Task Context` by creating a `TaskCreated` event.
-   `GET /tasks`: Retrieve a list of tasks, with filtering. E.g., `GET /tasks?status=IN_PROGRESS`.
-   `GET /tasks/{task_id}`: Retrieve the latest projected version of a `Task Context`.
-   `PATCH /tasks/{task_id}`: Update a `Task Context` by appending a new event (e.g., `TaskStatusUpdated`). Requires `If-Match` header.
-   `POST /world/facts`: Persist a new world fact via a `FactAdded` event.
-   `GET /world/snapshot/{world_version_id}`: Retrieve a consistent set of facts.
-   `POST /executions`: Start a new `Execution State` record (`ExecutionStarted` event).
-   `PUT /executions/{execution_id}`: Update the status and outcome (`ExecutionCompleted` event).
-   `POST /contracts/decision_packages`: Persist a `Decision Package` contract.
-   `POST /contracts/execution_outcomes`: Persist an `Execution Outcome Package`.
-   `POST /contracts/reasoning_traces`: Persist a `Reasoning Trace` contract for auditability.

## 3. Conversation Protocol Implementation

MAD-to-Half-MAD communication must be asynchronous, idempotent, and robust.

### 3.1 Message Format

All communication occurs via a standard message envelope.

```json
// Standard Message Envelope
{
  "message_id": "msg_01J8Y... (ULID)",
  "conversation_id": "conv_01J8Y... (ULID)",
  "idempotency_key": "unique-key-for-this-request-01J8Z...", // Prevents duplicate processing
  "schema_version": "1.1",
  "timestamp": "2025-11-15T11:00:00Z",
  "sender": {
    "service_name": "DER_instance_042",
    "service_version": "2.3.1",
    "instance_id": "pod-xyz-123"
  },
  "receiver": {"service_name": "LLM_Conductor"},
  "intent": "REQUEST", // INITIATE, REQUEST, RESPONSE, TERMINATE, ERROR
  "payload": { /* Intent-specific content */ },
  "metadata": {
    "causation_id": "msg_01J8X...",
    "trace_id": "trace-abc-123"
  }
}
```

### 3.2 Version Negotiation Handshake

Conversations begin with a handshake to ensure compatibility. This process remains unchanged from v1.0.

### 3.3 Error Handling

Errors are communicated explicitly with the `ERROR` intent. Common Error Codes: `VERSION_MISMATCH`, `TIMEOUT`, `INVALID_PAYLOAD`, `IDEMPOTENCY_KEY_REPLAY`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

### 3.4 Retry Policies

Message consumers MUST be idempotent. Senders SHOULD implement a retry policy for transient failures (e.g., `TIMEOUT`, `INTERNAL_ERROR`).
-   **Policy:** Exponential backoff with jitter.
-   **Example:** Retry after 1s, 2s, 4s, 8s, then fail and route to a dead-letter queue (DLQ).
-   The `idempotency_key` is critical for ensuring that retried messages are not processed multiple times by the receiver.

## 4. Contract Management and Validation

### 4.1 Schema Registry

A centralized Schema Registry (e.g., Confluent Schema Registry) is the single source of truth for all canonical contract schemas.
-   All schemas are versioned. Evolution rules (e.g., backward compatibility) are enforced.
-   The registry provides **deprecation policies**. Consumers can query the registry to identify deprecated schema versions and plan for upgrades.

### 4.2 Validation Strategy

Validation is a "producer-side and consumer-side" responsibility. This enables "fail fast" on the producer side and "trust but verify" on the consumer side. (See Appendix D for a validation failure example).

### 4.3 Schema Evolution

A non-breaking change policy is enforced for minor versions (e.g., adding optional fields). Breaking changes require a major version increment.

### 4.4 Version Negotiation for Synchronous APIs

While conversations use a handshake, synchronous APIs like the State Manager use HTTP content negotiation.
-   Clients SHOULD specify the desired schema version using an `Accept-Version` header (e.g., `Accept-Version: 1.1`).
-   If omitted, the server will default to its latest stable version.
-   If the requested version is unsupported, the server MUST respond with `406 Not Acceptable`.

## 5. Integration Patterns

### 5.1 The Core Decision Loop

1.  **Task Initiation:** An external trigger creates a `Task Context` in the State Manager.
2.  **Context Engineering (ICCM):** A CET instance is triggered, reads relevant state, and produces a `Structured Context` contract.
3.  **Decision Making (IDE):**
    a. The `Structured Context` is processed by the Rules Engine.
    b. The DER consumes all inputs, consults Half-MADs if needed, and produces a `Decision Package`. It persists this and its associated `Reasoning Trace` via the State Manager.
4.  **Execution (IEE):**
    a. A Doing Engine retrieves the `Decision Package`.
    b. **Safety Gate:** It **MUST** first explicitly validate that all preconditions listed in the `Decision Package` are met in the current world state. If validation fails, the execution is aborted, and a failure event is logged.
    c. If preconditions are met, it starts an `Execution State` record and performs the action.
    d. It synthesizes an `Execution Outcome Package` and updates the `Execution State` with the final status.
5.  **State Update & Loop:** The outcome updates the `World Model`, potentially triggering the next cycle.

### 5.2 Half-MAD Consultation Pattern

This pattern remains the same, but all messages now include the `idempotency_key` and `service_version` fields.

## 6. Deployment Architecture

### 6.1 Logical Architecture

The system is composed of containerized microservices. Communication is via synchronous APIs (State Manager) and asynchronous messaging (conversations).

### 6.2 Physical Deployment

-   **Containerization & Orchestration:** Kubernetes is the reference platform for OCI-compliant containers.
-   **API Gateway & Service Mesh:** Standard components for ingress, security, and inter-service communication.
-   **Service Lifecycle:** Deployments MUST follow a progressive rollout strategy (e.g., blue-green or canary) to minimize the impact of faulty releases. Automated rollbacks based on key metrics (e.g., increased error rate) are required.

## 7. Operational Considerations

### 7.1 Observability

Structured logging, Prometheus metrics, and distributed tracing via OpenTelemetry remain mandatory.

### 7.2 Security

-   **Authentication:** mTLS for service-to-service, OIDC/OAuth2 for external access.
-   **Authorization (RBAC):** The State Manager MUST enforce granular RBAC. For example:
    -   A `CET` service role may have `read` access to `/tasks` and `/world/snapshot`, but no `write` access.
    -   An `IEE-DoingEngine` role may have `write` access to `/executions` and `read` on `/contracts/decision_packages`, but cannot modify `/tasks`.
    -   An `Admin` role is required to create new tasks.
-   **Secret Management:** Managed via a dedicated secrets manager.

### 7.3 Testing Strategies

Unit, contract, integration, and E2E testing form the standard testing pyramid.

### 7.4 Chaos Engineering

To ensure MAD resilience, chaos engineering is a mandatory testing practice.
-   **Goal:** Verify that the system can withstand turbulent conditions in production.
-   **Required Scenarios:**
    1.  **State Manager Partition:** Simulate network partitions between the State Manager's API service and its underlying data stores (event log, projected state DB). Verify that the API returns appropriate errors (`503 Service Unavailable`) and recovers gracefully.
    2.  **Half-MAD Timeout:** Inject latency or timeouts into responses from a critical Half-MAD (e.g., LLM Conductor). Verify that the calling service (e.g., DER) handles the timeout correctly according to its retry policy and can proceed with a fallback decision if necessary.
    3.  **Message Queue Unavailability:** Simulate the conversation message broker being down. Verify that senders buffer messages or fail gracefully without data loss.

## 8. Conclusion

Paper 01, in its corrected v1.1 form, provides the prescriptive, actionable guidance necessary to implement the IAE vision from Paper 00. By reinforcing the principles of immutability, enhancing protocol robustness, and mandating resilience engineering, this specification establishes a hardened foundation for building, integrating, and operating a fleet of sophisticated MAD agents.

---
## Appendices

### Appendix A: State Manager API Reference (v1.1)

*(Summary - `Accept-Version` header is recommended on all calls)*

| Endpoint                          | Method | Description                                                | Key Headers         | Success Code |
| --------------------------------- | ------ | ---------------------------------------------------------- | ------------------- | ------------ |
| `/tasks`                          | POST   | Create a new Task Context.                                 | `Authorization`     | 201 Created  |
| `/tasks`                          | GET    | List tasks, filter by `status`, `agent_id`, etc.           | `Authorization`     | 200 OK       |
| `/tasks/{id}`                     | GET    | Retrieve a Task Context by its ID.                         | `Authorization`     | 200 OK       |
| `/tasks/{id}`                     | PATCH  | Append an event to a Task Context.                         | `Authorization`, `If-Match` | 200 OK       |
| `/world/facts`                    | POST   | Add one or more facts to the World Model.                  | `Authorization`     | 201 Created  |
| `/world/snapshot/{version_id}`    | GET    | Get a consistent snapshot of the world.                    | `Authorization`     | 200 OK       |
| `/executions`                     | POST   | Create a new Execution State record.                       | `Authorization`     | 201 Created  |
| `/executions/{id}`                | PUT    | Update a completed Execution State record.                 | `Authorization`, `If-Match` | 200 OK       |
| `/contracts/decision_packages`    | POST   | Persist a Decision Package contract.                       | `Authorization`     | 201 Created  |
| `/contracts/execution_outcomes`   | POST   | Persist an Execution Outcome Package contract.             | `Authorization`     | 201 Created  |
| `/contracts/reasoning_traces`     | POST   | **New:** Persist a Reasoning Trace contract.               | `Authorization`     | 201 Created  |

### Appendix B: Canonical Contract Schemas (v1.1)

**`Reasoning Trace` (as mandated by Paper 00)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reasoning Trace",
  "type": "object",
  "properties": {
    "trace_id": {"type": "string", "description": "ULID for this trace."},
    "decision_id": {"type": "string", "description": "The decision this trace justifies."},
    "schema_version": {"type": "string", "pattern": "^1\\.[0-9]+$"},
    "structure": {
      "type": "object",
      "description": "A directed acyclic graph (DAG) of reasoning nodes, representing the flow from context to decision."
    }
  },
  "required": ["trace_id", "decision_id", "schema_version", "structure"]
}
```
*(Other schemas like `Structured Context` are updated to use `schema_version` pattern `^1\\.[0-9]+$`)*

### Appendix C: Conversation Protocol Example (DER ↔ LLM Conductor)

**3. DER sends `REQUEST` (Corrected)**
*Queue: `llm_conductor.requests`*
```json
{
  "message_id": "msg_01J8Y2D6B...",
  "conversation_id": "conv_01J8Y2B4Y...",
  "idempotency_key": "der-042-req-987654",
  "schema_version": "1.1",
  "timestamp": "2025-11-15T11:00:02Z",
  "sender": {
    "service_name": "DER_instance_042",
    "service_version": "2.3.1",
    "instance_id": "pod-xyz-123"
  },
  "receiver": {"service_name": "LLM_Conductor"},
  "intent": "REQUEST",
  "payload": {
    "prompt": "Given the objective to reduce CPU, and the current world state, what are three potential actions and their associated risks?",
    "references": {
      "context_id": "ctx_01J8X4B9C...",
      "world_version_id": "wv_01J8X2Q5A..."
    }
  },
  "metadata": {"causation_id": "msg_01J8Y2C5A..."}
}
```

### Appendix D: Schema Validation Failure Scenario

**Scenario:** A newly deployed `CET` (v2.1) produces a `Structured Context` using schema v1.1. It adds a new, optional field `urgency`. An older `DER` (v2.0) is still running and only understands schema v1.0.

**1. Producer-Side (CET):**
-   The CET generates the `Structured Context` contract.
-   It validates against its known schema (v1.1) from the Schema Registry.
-   Validation passes because `urgency` is a valid optional field in v1.1.
-   The contract is sent to the IDE.

**2. Consumer-Side (DER):**
-   The DER receives the contract.
-   As per the "trust but verify" principle, it validates the payload against its expected schema (v1.0).
-   The validator encounters the `urgency` field, which is not defined in the v1.0 schema.
-   **Result:** Validation fails. The DER rejects the contract with a `400 Bad Request` error (if synchronous) or logs an error and moves the message to a DLQ (if asynchronous), creating an alert.
-   **Impact:** The system is protected from processing data it cannot understand. This failure highlights a partial deployment or version mismatch that must be rectified by upgrading the DER or rolling back the CET.
