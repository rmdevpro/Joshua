# Rogers Architecture Correction - Requirements Summary

## 🚨 CRITICAL ARCHITECTURE ERROR IDENTIFIED

**Current Implementation**: Rogers is a simple API service with NO cognitive capability
**Required Architecture**: EVERY MAD must have Thought Engine + Action Engine

---

## Core Architecture Principles (Previously Ignored)

### 1. CONVERSATION IS THE CORE
- MADs communicate through **conversations**, not API calls
- When Hopper needs session info, it ASKS Rogers: *"Can you tell me about session X?"*
- Not just `GET /api/v1/sessions/X` - that's missing the point entirely!

### 2. Every MAD Has Two Engines

#### Thought Engine (Cognitive Side)
- **Purpose**: Reasoning, decision-making, conversation handling
- **Implementation**: LLM interface (embedded or connected)
- **Capabilities**:
  - Understands natural language requests
  - Reasons about optimal strategies
  - Makes decisions about HOW to fulfill requests
  - Participates in multi-MAD conversations
  - Learns from interactions

#### Action Engine (Execution Side)
- **Purpose**: Performs actual work as directed by Thought Engine
- **Implementation**: Traditional service code (APIs, database ops, etc.)
- **Capabilities**:
  - CRUD operations
  - Database management
  - File operations
  - Network calls
  - Resource management

---

## Rogers Phase 1 Requirements

### Classification: Phase 1 MAD
- **Focus**: Primarily Action Engine with basic Thought Engine
- **Evolution**: Can enhance Thought Engine capabilities over time

### Thought Engine Requirements (Minimal for Phase 1)

1. **Conversational Interface**
   ```
   Input: "Rogers, can you create a new session for user123?"
   Process: Thought Engine understands intent → directs Action Engine
   Output: "I've created session abc-123 for user123. It's now active."
   ```

2. **MAD-to-MAD Communication**
   ```
   Hopper: "Rogers, what sessions are currently active?"
   Rogers: "I have 5 active sessions. Three are in heavy use, two are idle."

   Dewey: "Rogers, I need to archive conversations from session xyz-789"
   Rogers: "Session xyz-789 is dormant. Here's the session metadata..."
   ```

3. **Decision Capability**
   - When to move sessions from hot → warm → cold storage
   - How to handle version conflicts
   - When to wake dormant sessions
   - Resource optimization decisions

4. **Learning/Adaptation**
   - Track session patterns
   - Optimize caching strategies
   - Improve response to common queries

### Action Engine Requirements (Already Partially Built)

1. **Session Management**
   - ✅ Create/Read/Update/Delete sessions
   - ✅ Version control with optimistic locking
   - ✅ State management (active/dormant/archived)

2. **Storage Tier Management**
   - ✅ Redis for hot cache
   - ✅ MongoDB for warm storage
   - ⚠️ S3 for cold archive (mocked)

3. **Participant Management**
   - ✅ Add/remove MADs from sessions
   - ✅ Lease management

---

## Proposed Modifications

### 1. Add Thought Engine to Rogers

```python
class RogersThoughtEngine:
    """
    Cognitive layer for Rogers - handles reasoning and conversation
    """
    def __init__(self, llm_interface):
        self.llm = llm_interface  # Connection to LLM (local or remote)
        self.action_engine = RogersActionEngine()

    async def process_conversation(self, message: str, from_mad: str) -> str:
        """
        Handle conversational requests from other MADs or Imperator
        """
        # Parse intent using LLM
        intent = await self.llm.parse_intent(message)

        # Reason about best approach
        strategy = await self.reason_about_strategy(intent)

        # Direct Action Engine
        result = await self.action_engine.execute(strategy)

        # Formulate conversational response
        response = await self.llm.generate_response(intent, result)

        return response

    async def reason_about_strategy(self, intent):
        """
        Make decisions about HOW to fulfill requests
        """
        # Should we check cache first?
        # Is this session likely to be reactivated?
        # Should we pre-warm related sessions?
        # etc...
```

### 2. Conversational Interface via MCP

```python
# MCP tool exposed by Rogers
@tool
async def converse_with_rogers(message: str, from_mad: str) -> str:
    """
    Natural language interface to Rogers
    Examples:
    - "Create a session for user123"
    - "What's the status of session abc-123?"
    - "Archive all dormant sessions older than 7 days"
    """
    return await thought_engine.process_conversation(message, from_mad)
```

### 3. Inter-MAD Conversation Examples

```yaml
# Example conversation flow
Imperator: "Rogers, we need to handle a new user connection"
Rogers: "I'll create a new session. What's the user identifier?"
Imperator: "User ID is prod-user-456"
Rogers: "Session created: sess-789-abc. It's active and ready."

Dewey: "Rogers, I have 10GB of conversations for session sess-789-abc"
Rogers: "That session is currently active. I'll note the size for optimization."

Godot: "Rogers, session sess-old-123 hasn't been accessed in 30 days"
Rogers: "Thanks Godot. I'll mark it for archival. Checking with Dewey first..."
Rogers: "Dewey, can you prepare session sess-old-123 conversations for S3 archive?"
Dewey: "Prepared 2.3GB for archive. Ready when you are."
Rogers: "Initiating cold storage migration..."
```

### 4. Phase 1 Limitations (Acceptable)

- Simple intent parsing (not complex reasoning)
- Basic decision trees (not advanced planning)
- Template-based responses (not fully generative)
- Single-turn conversations (not multi-turn dialogue)

### 5. Evolution Path to Phase 2

- Enhanced reasoning capabilities
- Multi-turn conversation memory
- Learning from conversation patterns
- Predictive session management
- Collaborative problem-solving with other MADs

---

## Implementation Priority

1. **Immediate**: Add basic Thought Engine with conversational interface
2. **Next**: Enable MAD-to-MAD conversation via MCP
3. **Then**: Test conversation flows with other MADs
4. **Finally**: Deploy and iterate based on usage

---

## Key Insight Acknowledgment

I apologize for ignoring the fundamental architecture where:
- **Everything belongs in a MAD**
- **Each MAD has both Thought and Action Engines**
- **Conversation is the core communication mechanism**
- **MADs are cognitive entities, not just services**

This is not just a service mesh - it's a **cognitive mesh** where intelligent agents collaborate through conversation to accomplish tasks.

---

*This document corrects the fundamental misunderstanding of MAD architecture*