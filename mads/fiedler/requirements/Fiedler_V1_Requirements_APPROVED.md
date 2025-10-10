# Fiedler V1 - Conversational LLM Recommender Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Fiedler V1 enhances the existing Fiedler LLM orchestration server by adding an **Imperator** (an LLM-based reasoning engine). This allows Fiedler to provide conversational recommendations on which Language Model (LLM) is best suited for a given task, while preserving all existing functionality.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Fiedler that can reason about the characteristics of available LLMs (e.g., cost, context window, code capabilities).
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `fiedler_converse`, that accepts natural language questions.
    *   *Example:* A user or MAD can ask, "Hey Fiedler, who should I use for my code review task?"
    *   Fiedler's Imperator will analyze the request and provide a reasoned, conversational recommendation (e.g., "I'd suggest GPT-5 or Claude Sonnet 4.5...").
*   **FR3: Preserve Existing Tools:** All current Fiedler MCP tools (`fiedler_send`, `fiedler_list_models`, etc.) must remain fully functional and unchanged. The Imperator is an additive feature only.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Fiedler V1 is critically dependent on a new, shared **LLM Client Library**. This library will provide the base classes and helper tools (like Sequential Thinking) necessary for the Imperator to function.
*   **TR2: Open Question - Helper MCP Architecture:** The architecture for how the Imperator accesses its internal "helper" MCPs (e.g., Sequential Thinking) needs to be determined. Options include treating them as Python libraries, a shared helper server, or using existing MCP relays. This question must be answered during the design phase.

**4. Out of Scope for V1**

*   Joining the Rogers conversation bus.
*   Making existing orchestration tools (`fiedler_send`) conversational.
*   Advanced routing intelligence (DTR/LPPM) or spawning eMADs.

**5. Success Criteria**

*   ✅ Fiedler can successfully respond to a conversational query like, "Who should I use for task X?"
*   ✅ The response is an accurate and helpful recommendation based on the Imperator's reasoning.
*   ✅ All existing Fiedler orchestration tools continue to work as expected.
*   ✅ The Imperator successfully utilizes the LLM Client Library and its helper tools.
