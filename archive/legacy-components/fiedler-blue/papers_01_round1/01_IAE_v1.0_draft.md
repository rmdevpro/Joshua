# Paper 01: Intelligent Agentic Engineering (IAE) - Implementation Specification

**Version:** 1.0
**Date:** 2025-11-15
**Status:** DRAFT - Council of Elders Synthesis (v1.0)
**Repository:** Joshua (IAE)
**Parent:** Paper 00: IAE - Master Document (v1.1)
**Synthesized by:** Gemini 2.5 Pro, Synthesis Architect

---

## Executive Summary

This document, Paper 01, provides the definitive implementation specification for the Intelligent Agentic Engineering (IAE) discipline, building directly upon the theoretical foundations established in Paper 00. Where Paper 00 defined *what* to build, this paper specifies *how* to build it.

It provides concrete engineering guidance for assembling Multipurpose Agentic Duo (MAD) agents. Key specifications include:

1.  **State Manager:** Detailed API contracts (RESTful), data models (JSON Schema), and recommended storage patterns (event-sourced, hybrid persistence) to implement the authoritative memory of a MAD.
2.  **Conversation Protocol:** A standardized, asynchronous messaging protocol for all MAD-to-Half-MAD interactions, including message formats, version negotiation, and error handling.
3.  **Contract Management:** Strategies for schema validation, evolution, and the use of a central schema registry to ensure system-wide integrity.
4.  **Integration Patterns:** Prescriptive sequences for data flow between ICCM, IDE, and IEE components, mediated by the State Manager and canonical contracts.
5.  **Deployment & Operations:** A reference architecture based on containerized microservices, with specific guidance on scalability, security, observability, and testing.

This paper is intended for architects and engineers responsible for constructing the core infrastructure and assembling MAD agents as defined by the IAE discipline.

---

## 1. Introduction

Paper 00 established Intelligent Agentic Engineering (IAE) as the overarching discipline for agent assembly, defining the MAD architecture, the quaternary structure, and the canonical contracts that govern component interaction. This paper operationalizes those concepts.

The primary goal of this specification is to ensure that components developed within the separate disciplines (ICCM, IDE, IEE) can be integrated seamlessly and reliably into a functional, scalable, and maintainable Full MAD. Adherence to these specifications is mandatory for Council-approved agent development.

We will proceed by systematically detailing the implementation of each core IAE responsibility, beginning with its most critical component: the State Manager.

## 2. State Manager Implementation Specification

The State Manager is the authoritative memory and spine of any MAD. Its implementation must prioritize data integrity, auditability, and performance.

### 2.1 Architectural Principles

The design is guided by the global properties defined in Paper 00:

-   **Immutability via Event Sourcing:** All state changes are recorded as a sequence of events. The current state is a projection of these events. This provides a complete, auditable history and enables time-travel reads.
-   **Content-Addressable Storage (CAS):** Large artifacts (e.g., files, detailed logs) referenced in state are not stored directly. Instead, they are stored in a dedicated blob store (like S3 or GCS), and the State Manager holds their content-based hash (e.g., SHA-256) as an immutable reference.
-   **Optimistic Concurrency Control:** To prevent lost updates, write operations (`POST`, `PUT`, `PATCH`) must include a header specifying the expected current version of the resource (e.g., `If-Match: "ETag-value"`). The server will reject the request with a `412 Precondition Failed` if the version does not match.
-   **Tenancy and Access Control:** All resources are partitioned by a `tenant_id` and `agent_id`. API requests must be authenticated and authorized, with policies enforced at the API gateway level.

### 2.2 Data Models

The tripartite data model is implemented as three primary resource collections. (See Appendix B for full JSON Schemas).

#### 2.2.1 World Model

Represents the agent's beliefs about the external world. It is modeled as a collection of versioned "facts."

```json
// Example World Model Fact
{
  "fact_id": "fact_01J8X2Q4Z9N7R6P5E4T3W2A1S0", // ULID
  "agent_id": "agent_alpha_001",
  "created_at": "2025-11-15T10:00:00Z",
  "entity_id": "server_xyz", // The subject of the fact
  "attribute": "cpu_utilization_percent",
  "value": 85.5,
  "source": {
    "type": "SENSOR_READING",
    "source_id": "monitoring_agent_v2"
  },
  "valid_from": "2025-11-15T09:59:55Z",
  "valid_to": "2025-11-15T10:00:05Z", // Optional: for transient facts
  "confidence": 0.98,
  "world_version_id": "wv_01J8X2Q5A..." // Links facts in a consistent snapshot
}
```

#### 2.2.2 Task Context

Represents a specific problem or job the agent is working on.

```json
// Example Task Context
{
  "task_id": "task_01J8X3A8B...",
  "agent_id": "agent_alpha_001",
  "version": 1, // Incremented on each update
  "status": "IN_PROGRESS", // PENDING, IN_PROGRESS, PAUSED, COMPLETED, FAILED
  "created_at": "2025-11-15T10:05:00Z",
  "updated_at": "2025-11-15T10:05:00Z",
  "definition": {
    "objective": "Reduce CPU utilization on server_xyz to below 60%",
    "constraints": ["Do not terminate critical processes.", "Action must be completed within 5 minutes."],
    "budget": {"max_llm_calls": 10, "max_actions": 5}
  },
  "linked_context_id": "ctx_01J8X4B9C...", // Reference to the latest Structured Context
  "linked_decision_ids": ["dec_01J8X5C0D..."] // History of decisions for this task
}
```

#### 2.2.3 Execution State

A record of a specific action taken in response to a decision.

```json
// Example Execution State
{
  "execution_id": "exec_01J8X6D1E...",
  "task_id": "task_01J8X3A8B...",
  "decision_id": "dec_01J8X5C0D...",
  "status": "SUCCESS", // PENDING, RUNNING, SUCCESS, FAILURE, ABORTED
  "started_at": "2025-11-15T10:10:00Z",
  "completed_at": "2025-11-15T10:10:05Z",
  "action_name": "scale_down_service",
  "action_parameters": {"service_name": "billing_processor", "scale_to": 2},
  "outcome_ref": "out_01J8X7E2F..." // ULID of the persisted Execution Outcome Package
}
```

### 2.3 Storage Patterns

A single database technology is unlikely to be optimal. A hybrid approach is specified:

-   **Primary Store (Event Log):** A durable, append-only log service (e.g., Kafka, Pulsar, AWS Kinesis) serves as the ultimate source of truth. All state change requests are first written here as events.
-   **Projected State Store (Document DB):** A document database (e.g., MongoDB, DynamoDB) subscribes to the event log and builds materialized views of the `Task Context` and `Execution State`. This provides fast, indexed query capabilities for the current state.
-   **World Model Store (Graph DB or KV Store):** The `World Model` is best stored in a system optimized for relationships and point-in-time queries. A graph database (e.g., Neo4j) is ideal for querying entity relationships. Alternatively, a high-performance key-value store with robust secondary indexing can be used.

### 2.4 API Specification

The State Manager exposes a versioned, RESTful HTTP API. All endpoints are prefixed with `/api/v1`. Authentication is handled via bearer tokens. (See Appendix A for a full reference).

**Key Endpoints:**

-   `POST /tasks`: Create a new `Task Context`.
-   `GET /tasks/{task_id}`: Retrieve the latest version of a `Task Context`.
-   `PATCH /tasks/{task_id}`: Update a `Task Context` (requires `If-Match` header).
-   `POST /world/facts`: Persist a new world fact. Returns the new `world_version_id`.
-   `GET /world/snapshot/{world_version_id}`: Retrieve a consistent set of facts for a given world version.
-   `POST /executions`: Start a new `Execution State` record.
-   `PUT /executions/{execution_id}`: Update the status and outcome of an execution.
-   `POST /contracts/decision_packages`: Persist a `Decision Package` contract.
-   `POST /contracts/execution_outcomes`: Persist an `Execution Outcome Package` contract.

## 3. Conversation Protocol Implementation

MAD-to-Half-MAD communication must be asynchronous, stateful, and robust against component failure or version mismatch. The Conversation Protocol standardizes this interaction.

### 3.1 Message Format

All communication occurs via a standard message envelope. The transport layer is assumed to be a reliable message queue (e.g., RabbitMQ, NATS).

```json
// Standard Message Envelope
{
  "message_id": "msg_01J8Y... (ULID)",
  "conversation_id": "conv_01J8Y... (ULID)",
  "schema_version": "1.0",
  "timestamp": "2025-11-15T11:00:00Z",
  "sender": {"service_name": "DER_instance_042", "instance_id": "pod-xyz-123"},
  "receiver": {"service_name": "LLM_Conductor"},
  "intent": "REQUEST", // INITIATE, REQUEST, RESPONSE, TERMINATE, ERROR
  "payload": {
    // Intent-specific content, e.g., a request for LLM consultation
  },
  "metadata": {
    "causation_id": "msg_01J8X...", // ID of the message that prompted this one
    "trace_id": "trace-abc-123" // For distributed tracing
  }
}
```

### 3.2 Version Negotiation

To prevent breaking changes, conversations begin with a version negotiation handshake.

1.  **INITIATE:** The initiator sends a message with `intent: "INITIATE"`. The payload contains the versions of the conversation protocol it supports.
    ```json
    "payload": {
      "supported_versions": ["1.0", "1.1"]
    }
    ```
2.  **RESPONSE (Accept):** The receiver responds with `intent: "RESPONSE"`. The payload confirms the selected version.
    ```json
    "payload": {
      "status": "ACKNOWLEDGED",
      "selected_version": "1.0"
    }
    ```
3.  **ERROR (Reject):** If no common version is found, the receiver responds with `intent: "ERROR"`.
    ```json
    "payload": {
      "error_code": "VERSION_MISMATCH",
      "error_message": "No supported version found. Receiver supports ['0.9']."
    }
    ```

### 3.3 Error Handling

Errors are communicated explicitly with the `ERROR` intent. The payload contains a machine-readable code and a human-readable message.

**Common Error Codes:** `VERSION_MISMATCH`, `TIMEOUT`, `INVALID_PAYLOAD`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

## 4. Contract Management and Validation

The integrity of the five canonical contracts is paramount for interoperability.

### 4.1 Schema Registry

A centralized Schema Registry (e.g., Confluent Schema Registry, Apicurio) is the single source of truth for all canonical contract schemas (JSON Schema format).

-   All schemas are versioned.
-   Evolution rules are enforced by the registry (e.g., backward compatibility is required for all minor version bumps).

### 4.2 Validation Strategy

Validation is a "producer-side and consumer-side" responsibility.

1.  **Producer Validation:** Any component generating a contract (e.g., CET producing `Structured Context`) MUST validate its output against the relevant schema from the registry before publishing it. This enables a "fail fast" approach.
2.  **Consumer Validation:** Any component consuming a contract SHOULD validate it upon receipt. This "trust but verify" principle isolates the consumer from upstream bugs or violations.

### 4.3 Schema Evolution

A non-breaking change policy is enforced:

-   **Allowed:** Adding new *optional* fields.
-   **Disallowed:** Removing or renaming existing fields, changing a field's data type, making an optional field required.
-   Breaking changes require a major version increment of the schema, which will be treated as a new, distinct contract.

## 5. Integration Patterns

This section describes the flow of data and control for a standard decision-execution loop.

### 5.1 The Core Decision Loop

1.  **Task Initiation:** An external trigger (user, API call, event) creates a `Task Context` in the State Manager via `POST /tasks`.
2.  **Context Engineering (ICCM):** A CET instance is triggered. It reads the `Task Context` and relevant world state (`GET /tasks/{id}`, `GET /world/snapshot/...`). It transforms this data into a `Structured Context` contract.
3.  **Decision Making (IDE):**
    a. The `Structured Context` is passed to the Rules Engine. It produces a `Rule Engine Output` contract.
    b. The DER consumes both contracts. If it requires synthetic reasoning, it initiates a conversation with the LLM Conductor Half-MAD (see 5.2).
    c. The DER synthesizes all inputs and produces a `Decision Package`. It persists this via `POST /contracts/decision_packages` and links it to the task via `PATCH /tasks/{id}`.
4.  **Execution (IEE):**
    a. A Doing Engine, subscribed to new decisions for its domain, retrieves the `Decision Package`.
    b. It starts an `Execution State` record via `POST /executions`.
    c. It performs the action, validating preconditions and monitoring for safety.
    d. Upon completion, it synthesizes an `Execution Outcome Package` and persists it via `POST /contracts/execution_outcomes`.
    e. It updates the `Execution State` record with the final status and outcome reference via `PUT /executions/{id}`.
5.  **State Update & Loop:** The outcome may trigger a state update to the `World Model` (`POST /world/facts`). This change in the world model can trigger the next cycle for the task if the objective is not yet met.

### 5.2 Half-MAD Consultation Pattern (Example: DER to LLM Conductor)

1.  **Initiate:** The DER sends an `INITIATE` message to the LLM Conductor's message queue topic.
2.  **Acknowledge:** The LLM Conductor responds with an `ACKNOWLEDGED` response confirming the protocol version.
3.  **Request:** The DER sends a `REQUEST` message. The payload contains the reasoning prompt, constraints, and references to relevant context (`context_id`, `world_version_id`).
4.  **Response:** The LLM Conductor performs its multi-model orchestration. It returns a `RESPONSE` message containing the synthesized reasoning, confidence scores, and model provenance. The `consultation_id` is included.
5.  **Terminate:** The DER sends a `TERMINATE` message to formally close the conversation.

## 6. Deployment Architecture

### 6.1 Logical Architecture

The system is composed of containerized microservices organized by discipline and function. Communication occurs via synchronous API calls (for State Manager access) and asynchronous messaging (for conversations and event-driven workflows).

-   **IAE Services:** State Manager API, State Projectors.
-   **IDE Services:** Rules Engine, DER.
-   **ICCM Services:** CET instances (often domain-specific).
-   **IEE Services:** Doing Engines (domain-specific).
-   **Half-MADs:** LLM Conductor, Dewey, etc., as independent services.

### 6.2 Physical Deployment

-   **Containerization:** All services MUST be packaged as OCI-compliant container images (e.g., Docker).
-   **Orchestration:** Kubernetes is the reference orchestration platform. Services are deployed as Deployments or StatefulSets.
-   **API Gateway:** An API Gateway (e.g., Kong, Ambassador) sits in front of all synchronous APIs, handling TLS termination, authentication, rate limiting, and routing.
-   **Service Mesh:** A service mesh (e.g., Istio, Linkerd) is recommended for managing inter-service communication, providing mTLS, traffic management, and observability.

## 7. Operational Considerations

### 7.1 Observability

-   **Logging:** All services MUST emit structured logs (JSON). Logs MUST include a `trace_id` and `decision_id` to correlate activity across the system.
-   **Metrics:** Services MUST expose a `/metrics` endpoint in Prometheus format. Key metrics include request latency, error rates, and queue depths (the RED metrics: Rate, Errors, Duration).
-   **Tracing:** Distributed tracing using OpenTelemetry is MANDATORY. The `trace_id` must be propagated across all API calls and message headers.

### 7.2 Security

-   **Authentication:** Service-to-service communication is secured with mTLS (provided by the service mesh). External access via the API Gateway requires OIDC/OAuth2 bearer tokens.
-   **Authorization:** The State Manager MUST enforce Role-Based Access Control (RBAC) policies. For example, a Doing Engine may only be permitted to update `Execution State` but not `Task Context`.
-   **Secret Management:** All secrets (API keys, database credentials) MUST be managed by a dedicated secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager) and injected into containers at runtime.

### 7.3 Testing Strategies

-   **Unit Testing:** Each service's internal logic is tested in isolation.
-   **Contract Testing:** Use a framework like Pact to create consumer-driven contracts. This ensures that a service (e.g., CET) produces contracts that match the expectations of its consumers (e.g., IDE) without requiring full integration testing.
-   **Integration Testing:** Test the flow between a few integrated components, typically using real backing services (e.g., test the DER-to-LLM-Conductor conversation).
-   **End-to-End (E2E) Testing:** Simulate a full decision loop from task creation to execution outcome. These tests are expensive and should be reserved for critical user journeys.

## 8. Conclusion

Paper 01 provides the prescriptive, actionable guidance necessary to implement the IAE vision from Paper 00. By standardizing the State Manager, Conversation Protocol, contract handling, and operational patterns, we establish a robust foundation for building, integrating, and operating a fleet of sophisticated MAD agents.

This specification creates a stable engineering substrate upon which the other disciplines—ICCM, IDE, and IEE—can innovate independently. Adherence to these standards is the primary mechanism for ensuring system-wide coherence, reliability, and scalability.

---
## Appendices

### Appendix A: State Manager API Reference (v1)

*(Summary - a full OpenAPI/Swagger specification will be maintained separately)*

| Endpoint                          | Method | Description                                                | Key Headers         | Success Code |
| --------------------------------- | ------ | ---------------------------------------------------------- | ------------------- | ------------ |
| `/tasks`                          | POST   | Create a new Task Context.                                 | `Authorization`     | 201 Created  |
| `/tasks/{id}`                     | GET    | Retrieve a Task Context by its ID.                         | `Authorization`     | 200 OK       |
| `/tasks/{id}`                     | PATCH  | Partially update a Task Context.                           | `Authorization`, `If-Match` | 200 OK       |
| `/world/facts`                    | POST   | Add one or more facts to the World Model.                  | `Authorization`     | 201 Created  |
| `/world/snapshot/{version_id}`    | GET    | Get a consistent snapshot of the world.                    | `Authorization`     | 200 OK       |
| `/executions`                     | POST   | Create a new Execution State record.                       | `Authorization`     | 201 Created  |
| `/executions/{id}`                | PUT    | Update a completed Execution State record.                 | `Authorization`, `If-Match` | 200 OK       |
| `/contracts/decision_packages`    | POST   | Persist a Decision Package contract.                       | `Authorization`     | 201 Created  |
| `/contracts/execution_outcomes` | POST   | Persist an Execution Outcome Package contract.             | `Authorization`     | 201 Created  |

### Appendix B: Canonical Contract Schemas (v1.0)

*(High-level JSON Schema definitions for clarity. Field descriptions added.)*

**`Structured Context`**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Structured Context",
  "type": "object",
  "properties": {
    "context_id": {"type": "string", "description": "ULID for this context object."},
    "schema_version": {"type": "string", "pattern": "^1\\.0$"},
    "task_id": {"type": "string", "description": "The parent task this context is for."},
    "problem_frame": {
      "type": "object",
      "properties": {
        "objectives": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}}
      }
    },
    "features": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {}}
      }
    },
    "world_refs": {
      "type": "object",
      "properties": {"world_version_id": {"type": "string"}}
    }
  },
  "required": ["context_id", "schema_version", "task_id", "problem_frame", "world_refs"]
}
```

*(Schemas for `Rule Engine Output`, `Decision Package`, `Execution Outcome Package`, and `Reasoning Trace` would follow a similar, detailed format.)*

### Appendix C: Conversation Protocol Example (DER ↔ LLM Conductor)

**1. DER sends `INITIATE`**
*Queue: `llm_conductor.requests`*
```json
{
  "message_id": "msg_01J8Y2B4Z...",
  "conversation_id": "conv_01J8Y2B4Y...",
  "schema_version": "1.0",
  "timestamp": "2025-11-15T11:00:00Z",
  "sender": {"service_name": "DER_instance_042"},
  "receiver": {"service_name": "LLM_Conductor"},
  "intent": "INITIATE",
  "payload": {"supported_versions": ["1.0"]}
}
```

**2. LLM Conductor sends `RESPONSE` (ACK)**
*Queue: `der_instance_042.responses`*
```json
{
  "message_id": "msg_01J8Y2C5A...",
  "conversation_id": "conv_01J8Y2B4Y...",
  "schema_version": "1.0",
  "timestamp": "2025-11-15T11:00:01Z",
  "sender": {"service_name": "LLM_Conductor"},
  "receiver": {"service_name": "DER_instance_042"},
  "intent": "RESPONSE",
  "payload": {"status": "ACKNOWLEDGED", "selected_version": "1.0"},
  "metadata": {"causation_id": "msg_01J8Y2B4Z..."}
}
```

**3. DER sends `REQUEST`**
*Queue: `llm_conductor.requests`*
```json
{
  "message_id": "msg_01J8Y2D6B...",
  "conversation_id": "conv_01J8Y2B4Y...",
  // ... headers ...
  "intent": "REQUEST",
  "payload": {
    "prompt": "Given the objective to reduce CPU, and the current world state, what are three potential actions and their associated risks?",
    "references": {
      "context_id": "ctx_01J8X4B9C...",
      "world_version_id": "wv_01J8X2Q5A..."
    },
    "config": {"model_preference": ["Claude Opus 4", "Gemini 2.5 Pro"], "max_tokens": 1000}
  },
  "metadata": {"causation_id": "msg_01J8Y2C5A..."}
}
```

**4. LLM Conductor sends `RESPONSE`**
*Queue: `der_instance_042.responses`*
```json
{
  "message_id": "msg_01J8Y2E7C...",
  "conversation_id": "conv_01J8Y2B4Y...",
  // ... headers ...
  "intent": "RESPONSE",
  "payload": {
    "consultation_id": "consult_01J8Y2E7B...",
    "status": "COMPLETED",
    "result": [
      {"action": "...", "risk": "...", "confidence": 0.9},
      {"action": "...", "risk": "...", "confidence": 0.7}
    ],
    "provenance": {"model_used": "Gemini 2.5 Pro", "latency_ms": 1200}
  },
  "metadata": {"causation_id": "msg_01J8Y2D6B..."}
}
```
