# Security & Permissions Baseline Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document defines the V1 baseline security and permissions model for the MAD ecosystem. The focus for V1 is on establishing minimal, essential controls for authentication and access. A comprehensive Role-Based Access Control (RBAC) system is deferred to a future version.

---

## Requirements

### 1. Authentication
#### Requirement 1.1: MAD Authentication to Rogers
**Priority:** High
**Description:** Every MAD instance MUST authenticate with the Rogers messaging bus upon connection using a token-based mechanism. Rogers shall be the central authentication authority.
**Example:** `@Rogers #auth id=MAD_01 token=<crypto_token>`

### 2. Authorization and Access Control
#### Requirement 2.1: Conversation-Level Access Control
**Priority:** High
**Description:** Access to resources MUST be controlled at the conversation level. Rogers will maintain an Access Control List (ACL) for each conversation. A MAD can only join a conversation if it is on the ACL or receives an explicit invitation.
**Example:** `@Rogers #invite user=@MAD_C conversation=ProjectAlpha`

#### Requirement 2.2: Data Isolation Between Conversations
**Priority:** High
**Description:** The system MUST ensure strict data isolation between conversations. A MAD that is not a participant in a conversation must have no ability to access its messages or history.

### 3. Privilege Levels
#### Requirement 3.1: Baseline MAD Privilege Levels
**Priority:** Medium
**Description:** A basic privilege model MUST be implemented distinguishing between 'user-level' MADs and 'system-level' MADs (like Hopper, Fiedler, Rogers). System-level MADs have elevated permissions, such as creating new conversations or inviting other MADs.

---

## Success Criteria
- ✅ A MAD with an invalid token is rejected by Rogers, and the attempt is logged.
- ✅ A MAD that is not on a conversation's ACL is denied access when it attempts to join.
- ✅ A system-level MAD like Hopper can create a new private conversation for an eMAD it spawns and successfully invite the eMAD to it.

---

## Dependencies
- Rogers Messaging Bus Requirements

---

## Notes
This is a V1 baseline. The full, enterprise-grade Role-Based Access Control (RBAC) system is explicitly deferred to V5. The V1 goal is to prevent inadvertent access and establish a foundation for future security enhancements.

---

*Requirements v1.0 - Securing the conversation.*

---
---