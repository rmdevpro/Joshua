Here is the synthesized, unified set of 1-page requirements for each of the 13 MADs, taking the best elements from the trio's outputs and maintaining a consistent, implementable format.

***

### **Grace V1 - Conversation UI Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Grace V1 is a web-based conversation user interface that allows humans to participate in and monitor conversations within the MAD (Machine-Assisted Development) ecosystem. It serves as the foundational human interface for the MAD Conversation Protocol (MAD CP), connecting to the Rogers conversation bus. The scope is limited to a basic, functional chat interface.

**2. Key Features & Functional Requirements**

*   **FR1: Three-Panel Layout:** The UI will be organized into three distinct panels.
    *   **Left Panel (Conversation Selector):** Displays a scrollable list of all available conversations. A user can click a conversation to load it into the main chat panel. The currently selected conversation is visually highlighted.
    *   **Center Panel (Main Chat):** The primary interaction area. It displays the full message history of the selected conversation and includes a multi-line text input box for sending new messages.
    *   **Right Panel (Watchers):** Contains three independent, read-only "watcher" windows. Each watcher has its own dropdown menu to select and monitor any available conversation, allowing a user to view up to three conversations simultaneously in a compact format.

*   **FR2: Real-Time Conversation:**
    *   Users can send and receive messages in the main chat panel in near real-time.
    *   Messages will display the sender's identity, a timestamp, and the message content, including support for visible tags (e.g., `#status`, `#ack`).
    *   The main chat and watcher panels will automatically scroll to the newest message upon arrival.

**3. Technical & Integration Requirements**

*   **TR1: Technology:** The application will be a standard web interface (HTML/CSS/JS) and can reuse the existing Grace aesthetic. A new backend service is required to connect to Rogers.
*   **TR2: Rogers Integration:** Grace is a client of the Rogers conversation bus.
    *   It will fetch the list of available conversations via Rogers' REST API.
    *   It will send messages and retrieve message history via the Rogers REST API.
    *   It will use a WebSocket connection for receiving real-time message updates.
*   **TR3: User Identity:** A user must have a configurable identity (e.g., `@J`) that is used when sending messages.

**4. Out of Scope for V1**

*   Tag-based message filtering
*   Conversation creation or user management
*   Message search, editing, or deletion
*   Imperator integration (smart features)
*   File attachments or mobile-responsive design

**5. Success Criteria**

*   ✅ A user can successfully view a list of conversations, select one for the main chat, and send messages.
*   ✅ New messages from other participants appear in the main chat and relevant watchers in near real-time (<2s latency).
*   ✅ A user can simultaneously monitor three additional conversations in the read-only watcher panels.
*   ✅ The application successfully integrates with the Rogers bus for all conversation data.

---
### **Rogers V1 - Conversation Bus Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
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

---
### **Fiedler V1 - Conversational LLM Recommender Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
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

---
### **Dewey V1 - Conversational DBA Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
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

---
### **Horace V1 - Conversational NAS Gateway Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
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

---
### **Marco V1 - Conversational Web Explorer Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Marco V1 enhances the "Web Explorer" MAD by adding a powerful **Imperator**. This transforms Marco from a simple scraper into an intelligent agent capable of performing multi-step, conversational web research tasks autonomously. Due to the maturity of browser automation, this V1 is expected to be a more feature-complete implementation.

**2. Key Features & Functional Requirements**

*   **FR1: Add Intelligent Imperator:** Integrate an LLM brain into Marco that can plan and execute complex web research tasks based on a natural language goal.
*   **FR2: Conversational Research Tasking:** Introduce a new MCP tool, `marco_research`, that accepts high-level research requests.
    *   *Examples:* "Marco, what's the latest news about GPT-5?" or "Find me documentation on MCP servers and summarize the key points."
*   **FR3: Autonomous Web Navigation:** The Imperator must be able to:
    *   Navigate across multiple websites.
    *   Intelligently decide which links to follow to achieve its goal.
    *   Identify and extract relevant information from web pages.
    *   Synthesize the collected information into a coherent summary.
*   **FR4: Preserve Existing Tools:** All of Marco's existing browsing and scraping tools must remain functional.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Marco V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: Browser Automation:** Must integrate with a robust browser automation framework (e.g., Selenium, Playwright) to perform its actions.

**4. Out of Scope for V1**

*   Handling complex authentication flows or CAPTCHAs.
*   Long-term, stateful browsing sessions.

**5. Success Criteria**

*   ✅ Marco can successfully execute a high-level, conversational web research request.
*   ✅ Marco can autonomously navigate multiple web pages to find relevant information.
*   ✅ The final output is a coherent and accurate summary of the findings.
*   ✅ Existing web scraping tools continue to function correctly.

---
### **Brin V1 - Conversational Google Docs Specialist Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Brin V1 is a MAD specialized in creating and manipulating Google Workspace documents. This version adds an **Imperator** to enable users to manage Google Docs, Sheets, and Slides through simple, conversational requests.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Brin that can understand natural language instructions for document creation and editing.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `brin_converse`, to accept document-related requests.
    *   *Examples:* "Brin, create a report summarizing our Q1 results," "Update that slide deck with the new architecture diagram," or "Make a spreadsheet to track our MAD development progress."
*   **FR3: Multi-Format Support:** Brin must be able to create and edit documents across the Google Workspace suite: Docs, Sheets, and Slides.
*   **FR4: Preserve Existing Tools:** Any existing, non-conversational tools for document manipulation must remain functional.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Brin V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: Google Workspace API Integration:** Brin must be securely authenticated with and use the official Google Workspace APIs to perform all document operations.

**4. Out of Scope for V1**

*   Complex formatting, charts, or embedding objects.
*   Execution of Google Apps Script.
*   Management of document permissions or sharing settings.

**5. Success Criteria**

*   ✅ A user can successfully request the creation of a new Google Doc, Sheet, or Slide using a conversational command.
*   ✅ A user can request basic content updates to an existing document.
*   ✅ The resulting document accurately reflects the user's request.

---
### **Gates V1 - Conversational Microsoft Office Specialist Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Gates V1 is a MAD specialized in creating and manipulating Microsoft Office documents. This version adds an **Imperator** to enable users to manage Word documents, Excel spreadsheets, and PowerPoint presentations through simple, conversational requests.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Gates that can understand natural language instructions for document creation and editing.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `gates_converse`, to accept document-related requests.
    *   *Examples:* "Gates, create a Word report summarizing our Q1 results," "Update that PowerPoint with the new architecture diagram," or "Make an Excel spreadsheet to track our MAD development progress."
*   **FR3: Multi-Format Support:** Gates must be able to create and edit documents across the Microsoft Office suite: Word, Excel, and PowerPoint.
*   **FR4: Preserve Existing Tools:** Any existing, non-conversational tools for document manipulation must remain functional.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Gates V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: Microsoft Office API Integration:** Gates must integrate with relevant Microsoft APIs (e.g., Microsoft Graph) or file-format libraries to perform all document operations.

**4. Out of Scope for V1**

*   Complex formatting, charts, or embedding objects.
*   Execution of VBA macros.
*   Management of document permissions or sharing settings.

**5. Success Criteria**

*   ✅ A user can successfully request the creation of a new Word, Excel, or PowerPoint file using a conversational command.
*   ✅ A user can request basic content updates to an existing document.
*   ✅ The resulting document accurately reflects the user's request.

---
### **Stallman V1 - Conversational Open Source Docs Specialist Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Stallman V1 is a MAD specialized in creating and manipulating open source and OpenDocument Format (ODF) files, such as those used by LibreOffice. This version adds an **Imperator** to enable users to manage these documents through simple, conversational requests.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Stallman that can understand natural language instructions for document creation and editing.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `stallman_converse`, to accept document-related requests.
    *   *Examples:* "Stallman, create an ODT report summarizing our Q1 results," "Update that ODP presentation with the new architecture diagram," or "Make an ODS spreadsheet to track our MAD development progress."
*   **FR3: Multi-Format Support:** Stallman must be able to create and edit files in standard OpenDocument Formats: .odt (Writer), .ods (Calc), and .odp (Impress).
*   **FR4: Preserve Existing Tools:** Any existing, non-conversational tools for document manipulation must remain functional.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Stallman V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: ODF Library Integration:** Stallman must use appropriate libraries capable of programmatically creating and manipulating files in the OpenDocument Format.

**4. Out of Scope for V1**

*   Complex formatting, charts, or embedding objects.
*   Conversion between ODF and other document formats.

**5. Success Criteria**

*   ✅ A user can successfully request the creation of a new ODT, ODS, or ODP file using a conversational command.
*   ✅ A user can request basic content updates to an existing document.
*   ✅ The resulting document is a valid ODF file that accurately reflects the user's request.

---
### **Playfair V1 - Conversational Chart Master Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Playfair V1 enhances the "Chart Master" MAD by adding an **Imperator**. This allows users to generate a wide variety of diagrams, charts, and visualizations using simple, conversational requests.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into Playfair that can understand natural language descriptions of diagrams and translate them into a visual format.
*   **FR2: Conversational Interface:** Introduce a new MCP tool, `playfair_converse`, to accept visualization requests.
    *   *Examples:* "Playfair, create a flowchart showing the MAD architecture," "Make a bar chart of our LLM usage by provider," or "Draw a sequence diagram for the Rogers message flow."
*   **FR3: Multi-Format Support:** Playfair must be able to generate various common diagram types, including but not limited to flowcharts, sequence diagrams, organizational charts, and architecture diagrams, using backends like Graphviz and Mermaid.
*   **FR4: Preserve Existing Tools:** Any existing, non-conversational tools for diagram generation must remain functional.

**3. Technical & Integration Requirements**

*   **TR1: LLM Client Library Dependency:** Playfair V1 requires integration with the shared **LLM Client Library** to implement its Imperator.
*   **TR2: Diagramming Tool Integration:** The backend must integrate with command-line tools or libraries for rendering diagrams (e.g., Graphviz, Mermaid CLI).

**4. Out of Scope for V1**

*   Highly customized, aesthetically detailed visualizations.
*   Interactive charts or data dashboards.
*   Generation of complex 3D models.

**5. Success Criteria**

*   ✅ A user can successfully request a common diagram type using a conversational command.
*   ✅ Playfair correctly interprets the request and generates a visually accurate diagram.
*   ✅ The generated diagram is output in a standard image format (e.g., PNG, SVG).

---
### **Hopper V1 - Autonomous Development Coordinator Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Hopper V1 is an autonomous software engineering MAD that coordinates development projects. V1 implements a **Project Manager (PM)-led workflow**. A user engages Hopper's Imperator with a development goal, which then spawns a dedicated PM eMAD. This PM eMAD orchestrates an entire team of developer eMADs to plan, design, build, test, and deploy the software.

**2. Key Features & Functional Requirements**

*   **FR1: PM-Led Workflow:**
    *   The user initiates a project by making a request to Hopper's main Imperator (e.g., "I need to build a new MAD").
    *   The Imperator gathers initial requirements and then spawns a persistent Project Manager eMAD to lead the project.
*   **FR2: Autonomous Project Management:** The PM eMAD is responsible for the entire development lifecycle:
    *   **Planning:** Creates project structure and issues in Git.
    *   **Design:** Spins up a "consulting team" of eMADs to create design documents.
    *   **Development:** Spins up a "development team" (e.g., Senior and Junior Dev eMADs) to write the code.
    *   **Testing & Deployment:** Manages the team through testing and deployment cycles.
    *   **Documentation:** Updates Git with all code, documentation, and creates a final Pull Request.
*   **FR3: Orchestration, Not Implementation:** The PM eMAD's primary role is to coordinate and manage the specialist eMADs. It does not write production code itself but reviews and directs the work of the dev team.

**3. Technical & Integration Requirements**

*   **TR1: Rogers Conversation Bus:** All communication between the PM and its eMAD team members must occur on the Rogers bus.
*   **TR2: Fiedler Integration:** The PM eMAD must query Fiedler to get recommendations for the best LLMs for specific roles (e.g., Senior Dev, consultant).
*   **TR3: eMAD Framework:** Requires a robust framework for spawning, managing, and terminating ephemeral MADs.
*   **TR4: Git Integration:** Deep integration with a Git provider is required for all project management, code commits, and documentation tasks.
*   **TR5: LLM Client Library:** Requires specialized clients from the library for different roles (e.g., `ProjectManagerClient`, `SeniorDevClient`).

**4. Out of Scope for V1**

*   Fully autonomous architectural decisions (the PM will escalate to the user for guidance).
*   Managing multiple, concurrent development projects.
*   Advanced, automated testing strategies (V1 will focus on basic testing).

**5. Success Criteria**

*   ✅ A user can provide a high-level development request to Hopper.
*   ✅ Hopper successfully spawns a PM eMAD that autonomously assembles a team and manages the project.
*   ✅ A complete, documented, and functional software project is delivered and committed to Git without the user writing any code.

---
### **McNamara V1 - Security Operations Coordinator Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

McNamara V1 is the security specialist MAD for the ecosystem. This version acts as a central point for security operations, providing a conversational interface for security inquiries, performing basic monitoring, and coordinating specialized security eMAD teams for tasks like penetration testing.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into McNamara for conversational security guidance and operations.
*   **FR2: Conversational Interface:** Introduce a tool (`mcnamara_converse`) for users to ask security questions or request security tasks.
    *   *Examples:* "Are there any security anomalies today?" or "I need a penetration test on the new authentication system."
*   **FR3: Basic Security Monitoring:**
    *   Monitor the Rogers conversation bus for security-related events (e.g., messages with a `#security` tag).
    *   Track high-level access patterns across MADs to detect simple anomalies.
    *   Generate alerts by posting messages to a dedicated security conversation.
*   **FR4: Security eMAD Team Coordination:** McNamara must be able to spin up and coordinate ephemeral security teams for specialized tasks, such as a Penetration Testing Team or a Code Security Audit Team.

**3. Technical & Integration Requirements**

*   **TR1: Rogers Integration:** Must be able to monitor messages and participants on the Rogers conversation bus.
*   **TR2: Fiedler Integration:** Must query Fiedler to get recommendations for appropriate LLMs for security eMAD roles.
*   **TR3: eMAD Framework:** Requires the ability to spawn, manage, and terminate security-focused eMADs.

**4. Out of Scope for V1**

*   Automated threat response or remediation.
*   Advanced, deep automated scanning of all MADs and infrastructure.
*   Automated security policy enforcement.

**5. Success Criteria**

*   ✅ A user can ask McNamara security-related questions and receive a helpful response.
*   ✅ McNamara can successfully orchestrate a security task (e.g., a penetration test) by spawning an eMAD team and reporting the results.
*   ✅ McNamara detects basic access anomalies and generates a corresponding alert on the conversation bus.

---
### **Turing V1 - Secrets Manager Requirements**
| **Version:** 1.0 | **Status:** Draft | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Turing V1 is the dedicated secrets management MAD for the ecosystem. It is responsible for the secure storage, retrieval, and lifecycle management of all cryptographic secrets, including API keys, certificates, and other credentials.

**2. Key Features & Functional Requirements**

*   **FR1: Imperator for Guidance:** Integrate an LLM brain into Turing for conversational guidance on secrets management best practices.
*   **FR2: Secure Storage & Retrieval:** Provide a secure, encrypted storage mechanism for secrets. A programmatic interface will allow authorized MADs to retrieve the secrets they need to function.
*   **FR3: Lifecycle Management:** Support operations for managing the lifecycle of secrets, such as key rotation, either on a schedule or upon user request via a conversational interface (`turing_converse`).
*   **FR4: Security and Auditing:**
    *   **Zero-Trust Logging:** Secret values must **never** be exposed in plain text in any conversation log on the Rogers bus.
    *   **Audit Trail:** All secret access events (who accessed what, and when) must be logged to a secure conversation, which can be monitored by McNamara.

**3. Technical & Integration Requirements**

*   **TR1: Encryption:** All secrets must be encrypted at rest using a strong, industry-standard cryptographic method.
*   **TR2: Authorization:** The system must implement a robust, identity-based authorization mechanism to enforce access controls.
*   **TR3: Client Integration:** All MADs that require secrets (e.g., Fiedler, Marco) will be clients of Turing.
*   **TR4: McNamara Integration:** Turing must forward all audit logs to McNamara for security monitoring.

**4. Out of Scope for V1**

*   Complex, dynamic policy-based access control.
*   Hardware Security Module (HSM) integration.

**5. Success Criteria**

*   ✅ MADs can securely and programmatically retrieve the API keys they are authorized to access.
*   ✅ A user can conversationally request the rotation of an API key, and Turing successfully completes the action.
*   ✅ No secret value is ever logged to the Rogers conversation bus.
*   ✅ A complete and accurate audit trail of all secret access is available to McNamara.
