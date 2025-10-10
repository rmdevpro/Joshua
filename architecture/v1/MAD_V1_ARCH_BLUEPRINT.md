# MAD V1 Architecture Blueprint

## Version: 1.0
## Status: Approved

---

## Overview

This blueprint provides a high-level structural map of the MAD V1 system. It defines the core components and illustrates their primary interaction patterns. This document answers the question: "What are the building blocks and how do they connect?"

---

## Core Components

1.  **[CORRECTED]** **MAD (Multipurpose Agentic Duo):** The fundamental unit of agency. A MAD is a composite system composed of two extensible containers: an `ActionEngine` and a `ThoughtEngine`.
2.  **Rogers (Messaging Bus):** The central nervous system. A specialized, `ActionEngine`-only MAD that manages all conversations, state, and routing.
3.  **[CORRECTED]** **ThoughtEngine:** The "thinking" half of the duo. An extensible container for cognitive components. In V1, its primary component is the `Imperator` LLM. Future versions will add components like DTR, LPPM, and CET to form a progressive cognitive pipeline.
4.  **[CORRECTED]** **ActionEngine:** The "doing" half of the duo. An extensible container for execution components. It always contains the `MCP Server`, which acts as the bridge to the `ThoughtEngine` and manages access to databases, files, and other tools.
5.  **[CORRECTED]** **MCP Server:** A critical component within the `ActionEngine` that acts as the sole interface and bridge for communication between the `ActionEngine` and the `ThoughtEngine`.
6.  **Imperator:** The primary cognitive component within the `ThoughtEngine` for V1. An LLM responsible for understanding, reasoning, planning, and generating conversational responses.
7.  **Helper MCPs (Master Control Programs):** Persistent, specialized MADs providing core infrastructure services via conversation (e.g., Code Execution, RAG).
8.  **eMAD (Ephemeral MAD):** A temporary, role-based MAD instance spawned by a factory (e.g., Hopper) to perform a specific, time-bound task.
9.  **Fiedler (LLM Gateway):** A specialized MAD that acts as a proxy for all outbound LLM calls, managing model selection, cost, and orchestration.

---

## Primary Interaction Patterns

### Pattern 1: Basic MAD-to-MAD Communication

All communication is mediated by Rogers. A MAD never communicates directly with another.

```text
  [Requester MAD]
       |
       | 1. Sends message: "@Dewey import //project/docs/spec.yml"
       v
   [Rogers Bus]
       |
       | 2. Routes message based on @mention
       v
 [Target MAD: Dewey]
```

### Pattern 2: Internal MAD Cognitive Loop

**[CORRECTED]** A MAD's internal processing flow, where the MCP Server in the ActionEngine mediates all communication with the ThoughtEngine.

```text
[Rogers Bus] -> 1. Message In -> [ActionEngine: MCP Server]
                                          ^          |
                                          |          | 2. Request for cognitive processing
                                          |          v
                                4. Plan/Action -> [ThoughtEngine: Imperator]
                                          |          |
                                          |          | 3. Reasons and plans
                                          v          |
      <- 5. Executes actions & sends response out <-
```

### Pattern 3: Helper MCP Service Request

Using an infrastructure service is identical to talking to any other MAD.

```text
  [Client MAD]
       |
       | 1. "@CodeExecutor, run this Python script..."
       v
   [Rogers Bus]
       |
       | 2. Routes to Code Executor MCP
       v
[Helper MCP: Code Execution]
       |
       | 3. Executes code, prepares response
       v
   [Rogers Bus]
       |
       | 4. Routes response back to Client MAD
       v
  [Client MAD]
       |
       | 5. Receives: "Execution complete. Here is the output..."
       v
```
```
