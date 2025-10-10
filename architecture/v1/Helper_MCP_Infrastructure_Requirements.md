# Helper MCP Infrastructure Requirements

## Version: 1.0
## Status: Approved

---

## Overview
This document outlines the requirements for creating and operating Helper MCPs (Master Control Programs). Helper MCPs are persistent, specialized MADs that provide core infrastructure services to the entire MAD (**[CORRECTED]** Multipurpose Agentic Duo) ecosystem through the standard conversational interface.

---

## Requirements

### 1. Service Definition
#### Requirement 1.1: Conversational API
**Priority:** High
**Description:** Every Helper MCP MUST expose its functionality exclusively through a natural language conversational API. There will be no traditional REST/RPC endpoints.

#### Requirement 1.2: Service Discovery
**Priority:** High
**Description:** All active Helper MCPs MUST be discoverable through Rogers. A client MAD should be able to query Rogers to get a list of available services (e.g., `"@Rogers #list services"`).

### 2. Architectural Constraints
#### Requirement 2.1: Standard MAD Composition
**Priority:** High
**[CORRECTED]** **Description:** Helper MCPs MUST adhere to the standard MAD architecture, possessing both an `ActionEngine` (for executing the specialized task) and a `ThoughtEngine` (for understanding requests and formatting responses). This ensures they are first-class citizens in the ecosystem.

#### Requirement 2.2: High Availability
**Priority:** Medium
**Description:** Critical Helper MCPs (e.g., CodeExecutor, Fiedler) SHOULD be deployed in a high-availability configuration to ensure system resilience.

### 3. Example V1 Helper MCPs
#### Requirement 3.1: CodeExecutor MCP
**Priority:** High
**Description:** A Helper MCP named `CodeExecutor` MUST be provided to execute arbitrary code (e.g., Python, shell scripts) in a sandboxed environment and return the results.

#### Requirement 3.2: RAG MCP
**Priority:** High
**Description:** A Helper MCP named `RAG` MUST be provided to perform Retrieval-Augmented Generation over a specified corpus of documents.

---

## Success Criteria
- ✅ The `CodeExecutor` MCP can receive a Python script via a message, execute it, and return the `stdout`.
- ✅ A developer can create a new Helper MCP that registers with Rogers and becomes available to other MADs.
- ✅ **[CORRECTED]** The architecture of a Helper MCP clearly shows the separation between its `ActionEngine` (the service logic) and its `ThoughtEngine` (the conversational front-end).
```
