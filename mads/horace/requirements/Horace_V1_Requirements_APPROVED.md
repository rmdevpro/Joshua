# Horace V1 - Conversational NAS Gateway Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Horace V1 enhances the existing Horace "NAS Gateway" MAD by adding an **Imperator**. This allows users and other MADs to ask conversational, natural language questions about file systems, directories, and storage status.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Horace that can understand and answer questions related to file and storage management.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `horace_converse`, that accepts natural language questions about the file system.
    *   *Examples:* "Hey Horace, where should I store temporary files?", "How much space is left on /mnt/data?", or "Show me what's in the project directory."
*   **FR3: Preserve Existing Tools:** All of Horace's existing file system management tools must remain fully functional and unchanged.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Horace V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: File System Access:** The Imperator must have a mechanism to access file system metadata (e.g., disk usage, directory listings) to formulate its answers.
*   **TR3: Open Question - File Access Architecture:** Similar to Dewey, the method for handling file operations (especially large file I/O) in a conversation-centric paradigm is an open question. The design must determine if file operations should happen via the conversation bus, a direct API, or a hybrid model.

**4. Out of Scope for V1**

*   Transferring large files directly through the conversation bus.
*   Performing file modifications (write/update/delete) via the conversational interface.

**5. Success Criteria**

*   ✅ A user can ask Horace a conversational question about file or storage status.
*   ✅ Horace provides an accurate and helpful conversational response.
*   ✅ All existing file management functionalities of Horace remain operational.
