# Observability & Monitoring Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document specifies the requirements for observability, monitoring, and debugging within the MAD V1 ecosystem. In keeping with architectural tenets, observability mechanisms MUST be implemented conversationally.

---

## Requirements

### 1. Tracing
#### Requirement 1.1: Distributed Tracing via Conversation Tags
**Priority:** High
**Description:** The system MUST support distributed tracing of requests across multiple MADs and conversations. A unique trace ID shall be generated at the start of a workflow and propagated as a `#trace-id:[ID]` tag in all related messages.

### 2. Health and Metrics
#### Requirement 2.1: Conversational Health Checks
**Priority:** High
**Description:** All MADs MUST respond to a standardized health check message. An operator or automated system can send a message like `@TargetMAD #healthcheck` and expect a reply indicating status, such as `@Operator #ack #status:healthy`.

**REVISED:**
#### Requirement 2.2: Metric Emission via Tags
**Priority:** High
**Description:** MADs MUST emit key performance indicators and business metrics by sending messages with a `#metric` tag to a dedicated metrics conversation.
**Example:** `@MetricsCollector #metric #name:request_latency #value:150ms #source:Dewey`

### 3. Logging and Debugging
#### Requirement 3.1: Conversational Logging
**Priority:** High
**Description:** The primary logging mechanism MUST be conversational. MADs shall log significant events by sending messages to a dedicated logging conversation. The logs themselves are the conversation history, allowing for natural language queries and analysis.

#### Requirement 3.2: Error Visibility in Conversation
**Priority:** High
**Description:** When a MAD encounters an unrecoverable error while processing a request, it MUST post a message to the original conversation containing an `#error` tag and a description of the failure. This makes errors visible directly within the context of the failed workflow.

---

## Success Criteria
- ✅ By filtering for a single `#trace-id`, an operator can view all messages related to a single user request across multiple MADs.
- ✅ A monitoring system can ping `@Fiedler #healthcheck` and correctly parse the "healthy" response within 50ms.
- ✅ A dashboard can be built by consuming messages from the dedicated metrics conversation.
- ✅ A developer can debug a failed task by reading the conversation history, which includes the specific `#error` message.

---

## Dependencies
- Rogers Messaging Bus Requirements (for tag filtering)
- MAD CP Interface Library Requirements (for tag parsing)

---

## Notes
This approach treats observability data not as a separate stream of information, but as an integral part of the system's overall conversation.

---

*Requirements v1.0 - If you can't talk about it, you can't measure it.*