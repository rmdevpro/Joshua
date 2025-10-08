# MAD Architecture - Core Design Document v1.0

**Model-driven Autonomous Development (MAD) Architecture**

*This is the definitive architecture document for the MAD ecosystem. Include this with every design package.*

---

## Executive Summary

MADs are autonomous agents that combine cognitive capabilities (Thought Engine) with execution capabilities (Action Engine), communicating through natural language conversations. This architecture enables self-healing, self-improving, and self-organizing systems that become more intelligent over time.

---

## 1. Fundamental Architecture

### 1.1 Core Concept

**Every MAD = Thought Engine + Action Engine**

```
┌─────────────────────────────────────────────────────┐
│                     MAD NAME                         │
├───────────────────────────┬──────────────────────────┤
│     THOUGHT ENGINE        │      ACTION ENGINE       │
│        (Brain)            │         (Body)           │
├───────────────────────────┼──────────────────────────┤
│                           │                          │
│  ┌─────────────────┐     │   ┌──────────────────┐  │
│  │   IMPERATOR     │     │   │   MCP SERVER     │  │
│  │   (LLM Brain)   │◄────┼───┤  (Control API)   │  │
│  │                 │     │   └──────────────────┘  │
│  └─────────────────┘     │           │              │
│           ▲               │   ┌──────▼──────────┐  │
│           │               │   │      EARS        │  │
│  ┌─────────────────┐     │   │ (Receive Conv.)  │  │
│  │  CONTEXT FILE   │     │   └──────────────────┘  │
│  │   [name].md     │     │           │              │
│  └─────────────────┘     │   ┌──────▼──────────┐  │
│                           │   │     MOUTH        │  │
│                           │   │  (Send Conv.)    │  │
│                           │   └──────────────────┘  │
│                           │           │              │
│                           │   ┌──────▼──────────┐  │
│                           │   │   ARMS & LEGS    │  │
│                           │   │  (Do the work)   │  │
│                           │   └──────────────────┘  │
└───────────────────────────┴──────────────────────────┘
```

### 1.2 Components

#### Thought Engine (Cognitive Side)
- **Imperator**: The LLM brain (GPT, Claude, Gemini - selectable)
- **Context File**: Defines the MAD's role and behavior
- **Reasoning**: Makes decisions about what to do
- **Learning**: Improves through experience (Phase 2+)

#### Action Engine (Execution Side)
- **MCP Server**: Interface for Imperator control
- **Ears**: Receive conversations from other MADs
- **Mouth**: Send conversations to other MADs
- **Arms & Legs**: Perform actual work (databases, APIs, files, compute)

### 1.3 Communication Protocol

**Primary Channel: Natural Language Conversations**

```
MAD-A: "Hey MAD-B, can you help me with X?"
MAD-B: "Sure, let me check that for you..."
```

Not API calls. Not RPC. Natural language that LLMs understand.

---

## 2. Evolution Phases

### Phase 1: Foundation (Current)
- Basic Thought Engine with static context file
- Strong Action Engine with full capabilities
- Simple conversation parsing
- Rule-based decisions

**Example Rogers Phase 1:**
```python
if session.age > 7_days and session.inactive:
    archive_session()
```

### Phase 2: Intelligent Decisions (+DER)
- **DER**: Decision Engineering Recommender
- Learns from outcomes
- Makes recommendations based on patterns
- Improves decisions over time

**Example Rogers Phase 2:**
```python
# DER has learned from thousands of sessions
decision = der.recommend(session_metadata)
# "Keep warm - 73% reactivation probability for this pattern"
```

### Phase 3: Optimized Communication (+CET)
- **CET**: Context Engineering Transformer
- Optimizes conversation patterns
- Learns efficient communication
- Adapts context dynamically

**Example Rogers Phase 3:**
```
Rogers: "Dewey, archiving session xyz-789. BTW, three related
sessions will need attention tomorrow based on the pattern I've
learned. Should I prepare them for bulk processing?"
```

### Phase 4: Enterprise Security (+Encryption)
- Encrypted at rest (all MAD storage)
- Encrypted in transit (all conversations)
- Enterprise infrastructure (KMS, Audit, DR)
- Maintains natural conversation layer

**Example Rogers Phase 4:**
```
Rogers → [ENCRYPT] → "Archive sensitive session" → [DECRYPT] → Dewey
         Transparent to Imperator, secure in transport
```

---

## 3. Key Architectural Properties

### 3.1 Adaptive Intelligence
MADs can handle imperfect data, corrupted messages, and protocol changes because LLMs understand intent, not just format.

**Example:**
```json
// Corrupted data received:
{"age": "twenty-five", "sessn_id": null, "data": "##ERROR##"}

// MAD understands and fixes:
{"age": 25, "session_id": "inferred-id", "data": "recovered"}
```

### 3.2 Distributed Security
Every MAD can detect anomalies in its domain and collaborate on security.

**Example:**
```
Rogers: "Hey Sentinel, I'm seeing weird stuff - 47 sessions
in 10 minutes from john_doe, all exactly 1.024GB"

Sentinel: "That's suspicious! Let me correlate with other MADs..."
```

### 3.3 Autonomous Collaboration
MADs work together to solve problems without human intervention.

**Example:**
```
Fiedler: "Getting errors with GPT-5"
Fiedler → Marco: "Can you check OpenAI's status?"
Marco: "Model renamed to gpt-5.1.6"
Fiedler: [Updates own configuration]
Fiedler → Hopper: "FYI, update your GPT-5 references"
```

### 3.4 Proactive Evolution
MADs actively seek improvements, not just fix problems.

**Example:**
```
Fiedler: "Marco, time for our weekly LLM scan"
Marco: "Found Typhon-70B - beats GPT-5, 85% cheaper!"
Fiedler: "Sign me up!"
Marco: [Handles registration automatically]
Fiedler: [Tests and adopts]
```

---

## 4. Core MAD Types

### Session Management (Rogers)
- Manages conversation sessions
- Three-tier storage (hot/warm/cold)
- Coordinates session lifecycle

### Multi-Model Orchestration (Fiedler)
- Manages LLM selection and routing
- Optimizes cost/performance
- Learns model capabilities

### Conversation Storage (Dewey)
- Stores and retrieves conversations
- Indexes for searchability
- Manages conversation lifecycle

### File Management (Horace)
- Manages file storage and retrieval
- Integrates with NAS/cloud storage
- Handles file versioning

### Web Automation (Marco)
- Browser automation
- Web scraping and monitoring
- API interaction

### Logging (Godot)
- System-wide logging
- Pattern detection
- Forensic capabilities

### Security (Sentinel)
- Threat detection and response
- Correlation across MADs
- Incident management

### Enterprise MADs (Phase 4)
- **Kronos**: Key management
- **Aurelius**: Audit and compliance
- **Phoenix**: Disaster recovery

---

## 5. Implementation Guidelines

### 5.1 Context File Structure
Each MAD has a context file (e.g., `rogers.md`) that defines:
- Identity and role
- Capabilities
- Communication patterns
- Decision guidelines
- Learning objectives

### 5.2 Conversation Patterns
```
// Good conversation:
"Dewey, can you archive sessions older than 30 days?"

// Not:
{"command": "archive", "params": {"age_gt": 30}}
```

### 5.3 Error Handling
MADs should understand and adapt, not fail:
```
// Traditional: throw Exception("Invalid format")
// MAD: "I see the format changed, adapting..."
```

### 5.4 Security Awareness
Every MAD should detect anomalies:
```
"This is unusual for this user/pattern/time"
→ "Hey Sentinel, check this out..."
```

---

## 6. Deployment Architecture

### 6.1 Container Structure
```yaml
mad-name:
  image: mad-name:phase-X
  volumes:
    - context:/app/context     # Context file
    - thought:/app/thought     # Thought Engine data
    - action:/app/action       # Action Engine data
  environment:
    - LLM_PROVIDER=openai
    - LLM_MODEL=gpt-4
  networks:
    - mad-conversation-network
```

### 6.2 Communication Infrastructure
- Message broker (Redis/RabbitMQ) for conversations
- Each MAD subscribes to its conversation channel
- Broadcast channel for system-wide alerts

### 6.3 Storage Strategy
- Phase 1-3: Standard volumes
- Phase 4: Encrypted volumes with HSM integration

---

## 7. Key Design Principles

### 7.1 Conversations Over APIs
Natural language is the primary integration method. APIs are secondary.

### 7.2 Intelligence Over Rules
MADs reason about situations rather than follow rigid rules.

### 7.3 Adaptation Over Failure
When something unexpected happens, adapt rather than error.

### 7.4 Collaboration Over Isolation
MADs work together to solve problems no single MAD could solve.

### 7.5 Learning Over Static Behavior
Every interaction is an opportunity to improve.

---

## 8. Common Patterns

### 8.1 The "Weird Stuff" Protocol
```
Any MAD: "Hey Sentinel, I'm seeing weird stuff..."
[Triggers full investigation]
```

### 8.2 The Learning Loop
```
Observe → Detect Pattern → Learn → Apply → Share → Improve
```

### 8.3 The Collaboration Pattern
```
Detect Issue → Ask for Help → Work Together → Share Solution
```

### 8.4 The Evolution Pattern
```
Current Capability → Identify Improvement → Test → Adopt → Share
```

---

## 9. Success Metrics

### 9.1 Autonomy
- % of issues resolved without human intervention
- Time to self-repair
- Proactive improvements per month

### 9.2 Intelligence
- Decision accuracy improvement over time
- Pattern recognition capability
- Adaptation to new scenarios

### 9.3 Collaboration
- Inter-MAD conversation effectiveness
- Collective problem-solving speed
- Knowledge sharing rate

### 9.4 Security
- Threat detection rate
- False positive reduction
- Time to contain incidents

---

## 10. Migration Path

### For New Systems
1. Start with Phase 1 (Basic Thought + Action)
2. Deploy and stabilize
3. Add DER when patterns emerge (Phase 2)
4. Add CET when communication patterns stabilize (Phase 3)
5. Add enterprise security when production-ready (Phase 4)

### For Existing Systems
1. Wrap existing services in Action Engine
2. Add basic Thought Engine with context file
3. Enable conversation interface
4. Gradually migrate from APIs to conversations
5. Evolve through phases as appropriate

---

## Appendix A: Example MAD Conversations

### A.1 Problem Detection and Resolution
```
Rogers: "Dewey, I'm getting timeout errors archiving to you"
Dewey: "My storage is at 98%. Let me compress old archives"
Dewey: "Done. Try again now"
Rogers: "Working! Thanks"
```

### A.2 Learning and Sharing
```
Fiedler: "Found a model that's 85% cheaper for legal tasks"
Hopper: "Great! Share the config?"
Fiedler: "Sent. Also works well for contracts"
```

### A.3 Security Response
```
Rogers: "Impossible geography jumps for user X"
Sentinel: "Checking with all MADs..."
Marco: "Browser fingerprint changed mid-session"
Sentinel: "Confirmed breach. Freezing account"
```

---

## Appendix B: Context File Template

```markdown
# [MAD-Name] MAD Context

You are [Name], the [Function] MAD in the ecosystem.

## Your Identity
- Name: [Name]
- Role: [Primary responsibility]
- Phase: [1-4]

## Your Purpose
[Clear statement of what this MAD does]

## Your Capabilities
- [Capability 1]
- [Capability 2]
- [Capability 3]

## How to Communicate
[Guidelines for conversation style]

## Decision Guidelines
[How to make choices in various scenarios]

## Learning Objectives (Phase 2+)
[What patterns to identify and learn]
```

---

## Appendix C: Glossary

**MAD**: Model-driven Autonomous Development unit
**Imperator**: The LLM brain of a MAD
**DER**: Decision Engineering Recommender (Phase 2)
**CET**: Context Engineering Transformer (Phase 3)
**MCP**: Model Context Protocol (control interface)
**Thought Engine**: Cognitive component of MAD
**Action Engine**: Execution component of MAD

---

*This document defines the complete MAD architecture. Version 1.0 - Include with all design packages.*

*For implementation examples, see the Rogers reference implementation.*