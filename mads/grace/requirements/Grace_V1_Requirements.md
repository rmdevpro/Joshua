# Grace V1 - Conversation UI Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Grace V1 is a basic web-based conversation UI that allows humans to participate in and monitor MAD ecosystem conversations. This is the foundational user interface for the MAD Conversation Protocol (MAD CP).

**Purpose:** Enable humans to join, view, and participate in conversations on the Rogers conversation bus.

**Scope:** Basic conversation viewing and participation. No Imperator, no advanced AI features - just a functional chat interface.

---

## User Interface Layout

### Three-Panel Design

```
┌──────────────┬────────────────────────┬──────────────┐
│              │                        │   Watcher 1  │
│ Conversation │                        │  [dropdown]  │
│   Selector   │     Main Chat          │  ┌─────────┐ │
│              │                        │  │ msgs    │ │
│  □ Conv 1    │  ┌──────────────────┐  │  └─────────┘ │
│  □ Conv 2    │  │                  │  │              │
│  ■ Conv 3    │  │  Messages        │  │   Watcher 2  │
│  □ Conv 4    │  │                  │  │  [dropdown]  │
│              │  │                  │  │  ┌─────────┐ │
│              │  └──────────────────┘  │  │ msgs    │ │
│              │  [input box          ] │  └─────────┘ │
│              │  [Send]               │  │              │
│              │                        │   Watcher 3  │
│              │                        │  [dropdown]  │
│              │                        │  ┌─────────┐ │
│              │                        │  │ msgs    │ │
│              │                        │  └─────────┘ │
└──────────────┴────────────────────────┴──────────────┘
```

### Panel Specifications

#### Left Panel: Conversation Selector
- **Width:** ~20% of viewport
- **Function:** List of available conversations
- **Display:**
  - Conversation name/ID
  - Visual indicator for selected conversation (highlighted/bold)
  - Checkbox or radio button selection
- **Interaction:** Click to load conversation into main chat
- **Scrollable:** Yes, if conversation list exceeds panel height

#### Center Panel: Main Chat
- **Width:** ~50% of viewport
- **Function:** Primary conversation participation
- **Components:**
  - **Message display area:**
    - Scrollable message history
    - Shows sender, timestamp, message content
    - Auto-scroll to bottom on new messages
    - Support for tags (#ack, #status, #error, #human, etc.)
  - **Input area:**
    - Text input box (multi-line support)
    - Send button
    - Enter to send, Shift+Enter for new line
- **No dropdown:** Conversation selected via left panel

#### Right Panel: Watchers (3x)
- **Width:** ~30% of viewport (10% each watcher)
- **Function:** Monitor up to 3 conversations simultaneously (read-only)
- **Components per watcher:**
  - **Dropdown selector:** Choose which conversation to watch
  - **Message display:**
    - Scrollable, read-only
    - Smaller font/compact view
    - Shows sender, message content (timestamps optional)
    - Auto-scroll on new messages
- **No input capability:** Watchers are monitoring only

---

## Functional Requirements

### FR1: Conversation Selection
- **FR1.1:** User can view list of all available conversations
- **FR1.2:** User can select a conversation to load into main chat
- **FR1.3:** Selected conversation highlights in the selector list
- **FR1.4:** Conversation list updates when new conversations are created

### FR2: Main Chat Participation
- **FR2.1:** User can view full message history of selected conversation
- **FR2.2:** User can send messages to the selected conversation
- **FR2.3:** Messages display sender identity, timestamp, and content
- **FR2.4:** New messages appear in real-time (or near real-time)
- **FR2.5:** Message tags (#ack, #status, etc.) are visible
- **FR2.6:** Auto-scroll to newest message on arrival

### FR3: Watcher Functionality
- **FR3.1:** Each watcher has independent conversation selection
- **FR3.2:** Watchers display messages in read-only mode
- **FR3.3:** Watchers update in real-time (or near real-time)
- **FR3.4:** User can change which conversation a watcher monitors
- **FR3.5:** Watchers can display the same conversation as main chat or each other

### FR4: Tag-Based Filtering (Future Enhancement - Not V1)
- Note: V1 shows all messages. Filtering capability deferred to V2.

---

## Technical Requirements

### TR1: Frontend Technology
- **TR1.1:** Web-based interface (HTML/CSS/JavaScript)
- **TR1.2:** Can reuse existing Grace look and feel (HTML/CSS)
- **TR1.3:** New backend implementation required
- **TR1.4:** Responsive design (minimum width: 1024px recommended)

### TR2: Backend Integration
- **TR2.1:** Connects to Rogers (conversation bus) for data
- **TR2.2:** Retrieves conversation list from Rogers
- **TR2.3:** Retrieves message history for selected conversations
- **TR2.4:** Sends messages to Rogers on behalf of user
- **TR2.5:** Receives real-time updates for new messages

### TR3: Communication Protocol
- **TR3.1:** WebSocket connection for real-time updates (preferred)
  - Alternative: HTTP polling if WebSocket not feasible
- **TR3.2:** RESTful API for conversation list and message history
- **TR3.3:** MCP tools integration for Rogers communication (if applicable)

### TR4: Data Format
- **TR4.1:** Messages include: sender, timestamp, content, tags
- **TR4.2:** Conversations include: ID, name, participant list, metadata
- **TR4.3:** Standard JSON format for data exchange

### TR5: User Identity
- **TR5.1:** User has identity (e.g., "@J") when sending messages
- **TR5.2:** User identity configurable (settings or login)
- **TR5.3:** User can join/leave conversations (Rogers manages this)

---

## Integration Requirements

### IR1: Rogers Integration
- **IR1.1:** Grace queries Rogers for available conversations
- **IR1.2:** Grace subscribes to conversation updates via Rogers
- **IR1.3:** Grace sends messages through Rogers
- **IR1.4:** Grace receives real-time message broadcasts from Rogers

### IR2: MAD CP Compliance
- **IR2.1:** Messages support @ mentions (e.g., "@Fiedler")
- **IR2.2:** Messages support tags (e.g., "#status")
- **IR2.3:** No enforcement of rigid protocol - free-form text allowed

---

## Non-Functional Requirements

### NFR1: Performance
- **NFR1.1:** Message latency < 2 seconds (send to display)
- **NFR1.2:** UI remains responsive with 1000+ messages in conversation
- **NFR1.3:** Supports monitoring 4 concurrent conversations (1 main + 3 watchers)

### NFR2: Usability
- **NFR2.1:** Clean, uncluttered interface
- **NFR2.2:** Consistent with existing Grace aesthetic
- **NFR2.3:** Clear visual distinction between main chat and watchers
- **NFR2.4:** Intuitive conversation selection

### NFR3: Scalability
- **NFR3.1:** Handle 50+ active conversations in selector
- **NFR3.2:** Support multiple concurrent users (handled by Rogers)

---

## Success Criteria

### SC1: Core Functionality
- ✅ User can view list of conversations
- ✅ User can select and load a conversation
- ✅ User can send messages to selected conversation
- ✅ User can see new messages in real-time
- ✅ User can monitor 3 additional conversations simultaneously

### SC2: Integration Success
- ✅ Grace successfully connects to Rogers
- ✅ Messages sent via Grace appear in Rogers conversation store
- ✅ Messages sent by MADs appear in Grace UI
- ✅ Human and MAD messages indistinguishable in format

### SC3: User Experience
- ✅ No user training required (intuitive chat interface)
- ✅ No UI freezing or lag during normal operation
- ✅ Visual design consistent with Grace branding

---

## Out of Scope (Deferred to Future Versions)

### V2 and Beyond
- Tag-based message filtering
- Conversation creation UI
- User management/authentication
- Message search
- Imperator integration (smart conversation suggestions)
- Message editing/deletion
- File attachments
- Conversation archiving
- Export conversation history
- Custom themes
- Mobile responsive design

---

## Development Milestones

### Milestone 1: Backend Integration
- Rogers API/MCP integration
- Conversation retrieval
- Message send/receive

### Milestone 2: Basic UI
- Three-panel layout
- Conversation selector (static list)
- Main chat display (no input)

### Milestone 3: User Interaction
- Message input and send
- Real-time updates
- Conversation switching

### Milestone 4: Watchers
- Watcher dropdowns
- Independent conversation monitoring
- Real-time updates in watchers

### Milestone 5: Polish
- UI refinements
- Performance optimization
- Testing and bug fixes

---

## Dependencies

### Critical Dependencies
1. **Rogers (Conversation Bus):** Must be operational for Grace to function
2. **MAD CP Standard:** Message format must be defined
3. **User Identity System:** How users identify themselves (@J, etc.)

### Technical Dependencies
- Web server (Node.js, Python Flask/FastAPI, etc.)
- WebSocket library (if using WebSocket approach)
- Rogers API or MCP tools availability

---

## Risks and Mitigations

### Risk 1: Rogers Not Ready
- **Impact:** Grace cannot function without conversation backend
- **Mitigation:** Build Rogers and Grace in parallel, use mock data for Grace development

### Risk 2: Real-Time Updates Complexity
- **Impact:** WebSocket implementation may be complex
- **Mitigation:** Start with HTTP polling, upgrade to WebSocket in V1.1

### Risk 3: UI Performance with Large Conversations
- **Impact:** 1000+ message conversations may slow UI
- **Mitigation:** Virtual scrolling, message pagination, lazy loading

---

## Open Questions

1. **User authentication:** How do users log in and get their identity?
2. **Conversation creation:** Can users create conversations in V1, or only join existing ones?
3. **Rogers API specification:** What endpoints does Rogers expose?
4. **Deployment:** Where does Grace web server run (localhost, server, cloud)?

---

*Requirements document v1.0 - To be refined during development*

---

## Conversation History

### Design Discussion

**User:** Lets just call grace step 2. Just a very basic grace that is a very basic web page chat bot. We can use the look and feel from the existing grace work, but we'd just create new code for the back end. I think I'd use the grace look and feel, the selected chat would be in the middle and then there's probably a conversation selector list to the left. and probably three smaller chat watchers to the right. Each chat window would have a drop down selector above it to pick what goes in that window, but only the main chat has the ability to particpate in. Does that sound onerous?

**Assistant:** Not onerous at all! That's a solid, practical UI design.

[Initial layout showed dropdowns on all windows including main chat]

**User:** the main chat does not need a drop down because the selector would provide that

**Assistant:** You're absolutely right! The conversation selector on the left IS the selector for the main chat. Only the three watchers need dropdowns.

[Corrected layout - main chat no dropdown, only watchers have dropdowns]

**User:** yeah, that's it. Make that a requirements doc

*Conversation captured: 2025-10-09*
