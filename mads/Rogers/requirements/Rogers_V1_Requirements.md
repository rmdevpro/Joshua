# Rogers V1 - Conversation Bus Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Executive Summary

Rogers V1 is the **Conversation Bus** for the MAD ecosystem. It manages all conversations between humans and MADs, provides conversation storage, enables join/leave semantics, and distributes messages in real-time. Rogers is the foundation that enables the MAD Conversation Protocol (MAD CP).

**Key Shift from Previous Vision:** Rogers is NOT just a "session manager" - it is the central conversation infrastructure for the entire ecosystem.

---

## Overview

### Purpose
Rogers provides the conversation infrastructure that enables:
- Human-to-MAD communication
- MAD-to-MAD communication
- Human-to-human communication (via MAD ecosystem)
- Logging as conversations (logs ARE conversations)
- Monitoring and metrics as conversations

### Core Principle
**Everything is a conversation.** Rogers manages them all through a single, unified conversation model.

### Version 1 Scope
- Basic conversation management (create, join, leave, send, receive)
- Message storage and retrieval
- Real-time message distribution
- Tag support (visible, not filtered)
- Grace UI integration
- **No Thought Engine** (V1 is infrastructure only)
- **No advanced intelligence** (routing, pattern learning, etc.)

---

## Functional Requirements

### FR1: Conversation Management

#### FR1.1: Create Conversation
- **Capability:** Create new conversation with unique ID
- **Inputs:** Conversation name (optional), creator identity, initial participants (optional), metadata (optional)
- **Outputs:** Conversation ID, creation timestamp
- **Behavior:**
  - Generate unique conversation ID (UUID recommended)
  - Initialize empty message list
  - Add creator as participant
  - Store conversation metadata
  - Return conversation ID

#### FR1.2: List Conversations
- **Capability:** Retrieve list of all conversations
- **Filters:** All conversations, by participant, by tag, by date range (optional for V1)
- **Outputs:** Conversation list with ID, name, participant count, last message timestamp
- **Behavior:**
  - Query conversation store
  - Return sorted list (most recent first)
  - Include basic metadata for each conversation

#### FR1.3: Get Conversation Details
- **Capability:** Retrieve full conversation details
- **Inputs:** Conversation ID
- **Outputs:** Conversation metadata, participant list, message count
- **Behavior:**
  - Fetch conversation from store
  - Return metadata without full message history (use FR2.1 for messages)

#### FR1.4: Delete Conversation (Optional for V1)
- **Capability:** Remove conversation and all messages
- **Inputs:** Conversation ID, requester identity
- **Authorization:** Creator only, or admin role
- **Behavior:**
  - Verify authorization
  - Delete all messages
  - Delete conversation record
  - Notify participants (optional)

### FR2: Message Management

#### FR2.1: Send Message
- **Capability:** Add message to conversation
- **Inputs:** Conversation ID, sender identity, message content, tags (optional)
- **Outputs:** Message ID, timestamp
- **Behavior:**
  - Validate conversation exists
  - Validate sender is participant
  - Store message with timestamp
  - Assign message ID
  - Distribute to active subscribers (real-time)
  - Return confirmation

#### FR2.2: Retrieve Message History
- **Capability:** Get messages from conversation
- **Inputs:** Conversation ID, offset (optional), limit (optional)
- **Outputs:** List of messages with sender, timestamp, content, tags
- **Behavior:**
  - Fetch messages from conversation
  - Support pagination (offset/limit)
  - Return in chronological order
  - Include all message metadata

#### FR2.3: Real-Time Message Distribution
- **Capability:** Deliver new messages to active subscribers
- **Mechanism:** WebSocket or Server-Sent Events (SSE)
- **Behavior:**
  - When message sent to conversation
  - Identify active subscribers (joined participants)
  - Push message to all active subscribers
  - Handle subscriber disconnections gracefully

### FR3: Participant Management

#### FR3.1: Join Conversation
- **Capability:** Add participant to conversation
- **Inputs:** Conversation ID, participant identity
- **Outputs:** Join confirmation, current participant list
- **Behavior:**
  - Add participant to conversation
  - Mark participant as "joined" (active)
  - Return participant list
  - Optionally broadcast join event to other participants

#### FR3.2: Leave Conversation
- **Capability:** Remove participant from conversation
- **Inputs:** Conversation ID, participant identity
- **Outputs:** Leave confirmation
- **Behavior:**
  - Mark participant as "left" (inactive)
  - Close real-time subscription if active
  - Optionally broadcast leave event to other participants
  - Participant can rejoin later

#### FR3.3: List Participants
- **Capability:** Get current participants in conversation
- **Inputs:** Conversation ID
- **Outputs:** Participant list with join timestamp, active status
- **Behavior:**
  - Return all participants (active and inactive)
  - Include metadata (when joined, last active)

### FR4: Tag Support

#### FR4.1: Message Tags
- **Capability:** Messages include tags for categorization
- **Tag Examples:** `#ack`, `#status`, `#error`, `#human`, `#metric`
- **Behavior:**
  - Tags stored with message
  - Tags visible in message display
  - **V1:** No filtering by tags (display all)
  - **V2+:** Tag-based filtering

#### FR4.2: Tag Format
- **Syntax:** `#tagname` (hashtag prefix)
- **Location:** Can appear anywhere in message content
- **Multiple Tags:** Message can have multiple tags
- **Parsing:** Tags extracted and stored as metadata

---

## Technical Requirements

### TR1: Data Model

#### TR1.1: Conversation Object
```json
{
  "conversation_id": "uuid",
  "name": "string (optional)",
  "created_by": "string (participant ID)",
  "created_at": "timestamp",
  "participants": [
    {
      "participant_id": "string",
      "joined_at": "timestamp",
      "active": "boolean"
    }
  ],
  "metadata": {
    "tags": ["string"],
    "custom_fields": {}
  },
  "message_count": "integer",
  "last_message_at": "timestamp"
}
```

#### TR1.2: Message Object
```json
{
  "message_id": "uuid",
  "conversation_id": "uuid",
  "sender": "string (participant ID)",
  "content": "string",
  "timestamp": "timestamp",
  "tags": ["string"],
  "metadata": {
    "custom_fields": {}
  }
}
```

### TR2: Storage Backend

#### TR2.1: Database Selection
- **Primary Option:** MongoDB (document store for conversations and messages)
- **Alternative:** PostgreSQL with JSONB columns
- **Rationale:** Flexible schema, good for conversation data model

#### TR2.2: Storage Strategy (V1 Simplified)
- **All conversations:** Single tier (database)
- **No hot/warm/cold tiers in V1** (defer to V2+)
- **Performance:** Database indexing for common queries
- **Future:** Add Redis cache layer in V2

#### TR2.3: Indexes Required
- Conversation ID (primary key)
- Conversation participant list (for filtering)
- Message conversation_id (for retrieval)
- Message timestamp (for sorting)

### TR3: API Design

#### TR3.1: RESTful API Endpoints
```
POST   /api/v1/conversations              Create conversation
GET    /api/v1/conversations              List conversations
GET    /api/v1/conversations/{id}         Get conversation details
DELETE /api/v1/conversations/{id}         Delete conversation (optional)

POST   /api/v1/conversations/{id}/messages      Send message
GET    /api/v1/conversations/{id}/messages      Get message history

POST   /api/v1/conversations/{id}/participants  Join conversation
DELETE /api/v1/conversations/{id}/participants  Leave conversation
GET    /api/v1/conversations/{id}/participants  List participants
```

#### TR3.2: Real-Time API
- **WebSocket endpoint:** `/ws/conversations/{id}`
  - Client connects to subscribe to conversation
  - Server pushes new messages to connected clients
  - Client disconnects to unsubscribe
- **Alternative:** Server-Sent Events (SSE) if WebSocket too complex

#### TR3.3: Authentication & Authorization (Basic for V1)
- **Identity:** Participant ID passed in requests (header or body)
- **No authentication in V1** (trust-based, research environment)
- **V2+:** Add proper authentication (JWT, API keys, etc.)

### TR4: MCP Integration

#### TR4.1: MCP Server Tools (for MAD access)
```
rogers_create_conversation
rogers_list_conversations
rogers_get_conversation
rogers_send_message
rogers_get_messages
rogers_join_conversation
rogers_leave_conversation
```

#### TR4.2: Tool Behavior
- Tools wrap REST API calls
- Provide MCP-friendly interface for MADs
- Return structured responses

### TR5: Performance Requirements

#### TR5.1: Latency
- **Message send → storage:** < 100ms
- **Message send → real-time delivery:** < 500ms
- **Message history retrieval:** < 1 second (100 messages)

#### TR5.2: Scalability (V1 Targets)
- **Concurrent conversations:** 100+
- **Messages per conversation:** 10,000+
- **Concurrent real-time subscribers:** 50+
- **Messages per second (total):** 100+

#### TR5.3: Reliability
- Message delivery guaranteed (at-least-once)
- Conversation data persisted durably
- Graceful degradation under load

---

## Integration Requirements

### IR1: Grace Integration
- **IR1.1:** Grace queries Rogers for conversation list
- **IR1.2:** Grace retrieves message history via REST API
- **IR1.3:** Grace sends messages via REST API
- **IR1.4:** Grace subscribes to conversations via WebSocket
- **IR1.5:** Grace receives real-time messages from Rogers

### IR2: MAD Integration
- **IR2.1:** MADs access Rogers via MCP tools
- **IR2.2:** MADs can create conversations for collaboration
- **IR2.3:** MADs join/leave conversations as needed
- **IR2.4:** MADs send/receive messages

### IR3: Future MAD Integrations
- **Dewey:** Query conversation history for archival
- **Godot:** Logging conversations (logs ARE conversations)
- **Fiedler:** Request LLM recommendations via conversation
- **Hopper:** Development team conversations

---

## MAD Architecture Compliance

### Rogers as a MAD (V1 Limitations)

**V1: Action Engine Only**
- Rogers V1 is **infrastructure-focused**
- No Thought Engine (no Imperator)
- No cognitive/reasoning capabilities
- Operates as a service (traditional API)

**V2+: Add Thought Engine**
- Add Imperator for conversational interface
- Enable Rogers to participate in MAD-to-MAD conversations
- Decision-making for conversation optimization
- Pattern learning for intelligent routing

### Why V1 is Action Engine Only
- **Foundation first:** Build reliable conversation infrastructure
- **Complexity management:** Separate infrastructure from intelligence
- **Iteration:** Add cognitive layer after foundation proven
- **Pragmatism:** V1 delivers value immediately without full MAD complexity

---

## Non-Functional Requirements

### NFR1: Availability
- **Target:** 99% uptime (research environment)
- **Recovery:** Automatic restart on failure
- **Monitoring:** Health endpoint for status checks

### NFR2: Data Durability
- **Conversations:** Never lost once created
- **Messages:** Never lost once sent
- **Backups:** Daily backups of conversation database (optional for V1)

### NFR3: Maintainability
- **Code quality:** Clean, documented, testable
- **Logging:** Comprehensive logging for debugging
- **Configuration:** Environment-based config (dev/prod)

---

## Success Criteria

### SC1: Core Functionality
- ✅ Create conversations
- ✅ Send messages to conversations
- ✅ Retrieve message history
- ✅ Join/leave conversations
- ✅ Real-time message delivery to subscribers

### SC2: Integration Success
- ✅ Grace successfully connects and displays conversations
- ✅ Grace can send messages and see them stored
- ✅ Grace receives real-time updates
- ✅ MADs can access Rogers via MCP tools

### SC3: Performance
- ✅ Message latency < 500ms end-to-end
- ✅ Support 10 concurrent conversations without degradation
- ✅ Handle 100+ messages per conversation smoothly

---

## Out of Scope (Deferred to V2+)

### V2 and Beyond
- Thought Engine (Imperator) for Rogers
- Hot/warm/cold storage tiers
- Advanced conversation analytics
- Message search/indexing
- Tag-based filtering
- Conversation permissions/ACLs
- Message editing/deletion
- Read receipts
- Typing indicators
- File attachments in messages
- Conversation archival
- Message encryption
- Rate limiting
- Advanced monitoring/metrics

---

## Development Milestones

### Milestone 1: Core Storage (Week 1)
- Database schema design
- Basic conversation CRUD
- Message storage and retrieval

### Milestone 2: REST API (Week 2)
- API endpoint implementation
- Participant management
- API testing

### Milestone 3: Real-Time Distribution (Week 3)
- WebSocket implementation
- Real-time message push
- Subscription management

### Milestone 4: MCP Integration (Week 4)
- MCP server implementation
- Tool definitions
- MAD integration testing

### Milestone 5: Grace Integration (Week 5)
- Grace backend connection
- End-to-end testing
- Bug fixes and polish

---

## Dependencies

### Critical Dependencies
1. **Database:** MongoDB or PostgreSQL deployment
2. **Web Framework:** FastAPI/Flask (Python) or Express (Node.js)
3. **WebSocket Library:** Socket.io, ws, or native WebSocket support

### Technical Dependencies
- **Storage:** Database server accessible to Rogers
- **Network:** Accessible from Grace and MADs
- **Environment:** Docker deployment (consistent with other MADs)

---

## Risks and Mitigations

### Risk 1: Real-Time Complexity
- **Impact:** WebSocket implementation may be complex
- **Mitigation:** Start with simple WebSocket, iterate; fallback to polling if needed

### Risk 2: Scaling Challenges
- **Impact:** Performance degrades with many conversations
- **Mitigation:** Database optimization, indexing; defer sharding to V2

### Risk 3: Grace Dependency
- **Impact:** Rogers useless without UI
- **Mitigation:** Build Rogers and Grace in parallel; provide API testing interface

---

## Open Questions

1. **Conversation creation:** Who can create conversations? Anyone? Only admins?
2. **Participant permissions:** Can anyone join any conversation, or are there access controls?
3. **Message retention:** Do messages ever expire, or stored forever?
4. **Database choice:** MongoDB vs. PostgreSQL - what's the preference?
5. **Deployment:** Docker Compose? Kubernetes? Standalone?

---

## Appendix: Conversation vs. Session

### Clarification
- **Session (old concept):** Tied to user connection, ephemeral state management
- **Conversation (new concept):** Persistent, multi-participant message stream

Rogers V1 manages **conversations**, not sessions. Sessions may be built on top of conversations, but conversations are the core primitive.

---

*Requirements document v1.0 - Rogers as Conversation Bus foundation*

---

## Conversation History

### Architecture Discussion

**Context:** Discussion about logs and conversations being the same thing

**User:** which then means that logs and conversations are not separate things. So perhaps there is nothing that captures logs. Its just part of what Rogers does

**Assistant:** Realized logs and conversations are the same thing - Rogers manages all conversations, no separate Godot needed.

**User:** I suppose for consistency of terminology, one would "Join" or "Leave" the conversation and not "Subscribe"

**Assistant:** Fixed terminology to join/leave (not subscribe/unsubscribe) - consistent with chat paradigm.

**User:** yes and so chat systems between people and machine traffic all share the same paradigm

**Key Insight:** One paradigm for everything - human chat, MAD coordination, machine traffic, logging, monitoring - all use same conversation model.

*Conversation captured: 2025-10-09*
