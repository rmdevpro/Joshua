# Rogers V1 - Conversation Bus Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Rogers V1 is the central conversation bus and infrastructure for the entire MAD ecosystem. It manages the lifecycle of all conversations, stores message history, and distributes messages in real-time to all participants (human or MAD). The core principle is that **everything is a conversation**, including logs, metrics, and machine-to-machine traffic.

**2. Key Features & Functional Requirements**

*   **FR1: Conversation Management:** Provide a programmatic API to create, list, and retrieve details for conversations. Each conversation will have a unique ID, participants, and metadata.
*   **FR2: Message Management:** Provide an API to send messages to a specific conversation and retrieve its full message history. The system must support pagination for large histories.
*   **FR3: Participant Management:** Provide an API for participants to `join` or `leave` conversations. This controls who receives real-time updates.
*   **FR4: Real-Time Distribution:** When a message is sent to a conversation, Rogers must immediately push that message to all currently joined participants (subscribers) via a real-time connection.
*   **FR5: Tag Support:** Messages can contain tags (e.g., `#status`, `#error`). Rogers will store these tags as metadata. V1 will not provide server-side filtering based on tags.

**3. Technical & Integration Requirements**

*   **TR1: API:** Rogers must expose both a RESTful API for stateful operations (create conversation, get history) and a WebSocket endpoint for real-time message subscriptions.
*   **TR2: Data Storage:** A document-oriented database (e.g., MongoDB) is the preferred backend for storing conversation and message objects in a flexible JSON format.
*   **TR3: MCP Integration:** Rogers will provide a set of MCP server tools (e.g., `rogers_send_message`) that act as wrappers around its REST API, allowing MADs to easily interact with the conversation bus.
*   **TR4: MAD Architecture:** Rogers V1 is an **Action Engine only**. It is foundational infrastructure and does not contain a Thought Engine (Imperator) or any cognitive capabilities.

**4. Out of Scope for V1**

*   Thought Engine (Imperator) and intelligent routing
*   Advanced analytics, message search, and tag-based filtering
*   User permissions, access control lists (ACLs), and message encryption
*   Hot/warm/cold storage tiers for conversation data

**5. Success Criteria**

*   ✅ The system provides reliable APIs for creating conversations, sending messages, and retrieving history.
*   ✅ The Grace UI can successfully connect, display conversations, and receive real-time message updates.
*   ✅ MADs can successfully communicate with each other using the provided MCP tools.
*   ✅ End-to-end message delivery latency (from send to real-time receipt) is under 500ms.
