# Security & Permissions Baseline Requirements

## Version: 1.0
## Status: Approved

---

## Overview
This document establishes the baseline security requirements for the MAD (**[CORRECTED]** Multipurpose Agentic Duo) V1 ecosystem. The primary security boundary is the conversational interface itself.

---

## Requirements

### 1. Authentication & Authorization
#### Requirement 1.1: MAD Identity
**Priority:** High
**Description:** Every MAD instance MUST have a unique, verifiable identity registered with Rogers. Unauthenticated MADs are not permitted to join the message bus.

#### Requirement 1.2: Role-Based Access Control (RBAC)
**Priority:** Medium
**Description:** The system SHOULD support RBAC for controlling which MADs can perform certain actions or talk to specific Helper MCPs. For V1, this may be implemented as simple allow/deny lists managed by Rogers.

### 2. Data Security
#### Requirement 2.1: Encryption in Transit
**Priority:** High
**Description:** All communication between MADs and the Rogers messaging bus MUST be encrypted using industry-standard protocols (e.g., TLS 1.3).

#### Requirement 2.2: Sandboxing
**Priority:** High
**Description:** Any MAD component that executes external code or accesses the file system, such as the `CodeExecutor` Helper MCP, MUST operate within a secure, sandboxed environment to prevent privilege escalation or system compromise. **[CORRECTED]** This is a critical function of the `ActionEngine` in such MADs.

### 3. Auditability
#### Requirement 3.1: Immutable Ledger
**Priority:** High
**Description:** The conversation history stored in Rogers MUST be treated as an immutable ledger. Messages cannot be altered or deleted, providing a complete and tamper-evident audit trail of all system activity.

---

## Success Criteria
- ✅ An unauthorized MAD is prevented from connecting to Rogers.
- ✅ The `CodeExecutor` MCP is proven to be unable to access files outside of its designated working directory.
- ✅ An administrator can reconstruct the exact sequence of events leading to a specific outcome by reviewing the Rogers message history.
```
