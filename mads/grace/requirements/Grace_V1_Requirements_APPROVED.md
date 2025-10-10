# Grace V1 - Conversation UI Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
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
