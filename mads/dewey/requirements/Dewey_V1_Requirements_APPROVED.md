# Dewey V1 - Conversational DBA Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Dewey V1 enhances the existing Dewey "Librarian" MAD by adding an **Imperator**. This allows users and other MADs to ask conversational, natural language questions about the state and structure of the data lake (Winnipesaukee) that Dewey manages.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Dewey that can understand and answer questions related to database administration.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `dewey_converse`, that accepts natural language questions about the data lake.
    *   *Examples:* "Hey Dewey, what tables do we have in the lake?", "How much storage are we using?", or "Show me the schema for the conversation data."
*   **FR3: Preserve Existing Tools:** All of Dewey's existing data and database management tools must remain fully functional and unchanged.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Dewey V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: Data Access:** The Imperator must have a mechanism to query the data lake's metadata (and potentially data) to formulate its answers.
*   **TR3: Open Question - Data Access Architecture:** The method for querying large amounts of data within a conversation-centric paradigm is an open question. The design phase must determine if data queries should happen via the conversation bus, a direct API, or a hybrid model.

**4. Out of Scope for V1**

*   Executing large-scale data queries or transfers directly through the conversation bus.
*   Performing data modification (write/update/delete) operations via the conversational interface.

**5. Success Criteria**

*   ✅ A user can ask Dewey a conversational question about the data lake's status, schemas, or storage.
*   ✅ Dewey provides an accurate and helpful conversational response.
*   ✅ All existing data management functionalities of Dewey remain operational.
