# MAD V1 Architecture Blueprint

## Version: 1.0
## Status: Approved

---

## Overview

This blueprint provides a high-level structural map of the MAD V1 system. It defines the core components and illustrates their primary interaction patterns. This document answers the question: "What are the building blocks and how do they connect?"

---

## Core Components

1.  **MAD (Multi-Agent Demonstrator):** The fundamental unit of agency. Composed of an ActionEngine (tools, deterministic logic) and a ThoughtEngine (Imperator LLM).
2.  **Rogers (Messaging Bus):** The central nervous system. A specialized, ActionEngine-only MAD that manages all conversations, state, and routing.
3.  **Imperator (ThoughtEngine):** The cognitive core of a MAD. An LLM responsible for understanding, reasoning, planning, and generating conversational responses.
4.  **Helper MCPs (Master Control Programs):** Persistent, specialized MADs providing core infrastructure services via conversation (e.g., Code Execution, RAG).
5.  **eMAD (Ephemeral MAD):** A temporary, role-based MAD instance spawned by a factory (e.g., Hopper) to perform a specific, time-bound task.
6.  **Fiedler (LLM Gateway):** A specialized MAD that acts as a proxy for all outbound LLM calls, managing model selection, cost, and orchestration.

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

A MAD's internal processing flow for handling a message.

```text
[Rogers Bus] -> 1. Message In -> [ActionEngine]
                                      ^      |
                                      |      | 2. "What should I do?"
                                      |      v
                                 4. "Do this"  [Imperator (ThoughtEngine)]
                                      |      |
                                      |      | 3. Reasons and plans
                                      v      |
               <- 5. Action/Response Out <-
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

---
---