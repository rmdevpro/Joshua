# LLM Client Library Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

The LLM Client Library provides base and specialized client classes for all Imperators and eMADs in the MAD ecosystem. It uses **inheritance** to provide role-appropriate reasoning augmentation.

---

## Architecture: Inheritance Model

```
LLMClientBase
├── Sequential Thinking MCP (everyone gets this)
├── Basic conversation interface
├── Standard LLM API access
└── Token management

↓ Extends to specialized clients

ImperatorClient (for MAD Imperators)
├── Inherits: Base + Sequential Thinking
├── Minimal additions (just reasoning)
└── Used by: All MADs for the Imperator (V1 MADs require this) and by eMADs as required

SeniorDevClient (for eMAD role: Senior Developer)
├── Inherits: Base + Sequential Thinking
├── Adds: Code execution (Python REPL/sandbox)
├── Adds: Reflection server (code review/self-correction)
└── Used by: Hopper's Senior Dev eMAD

ProjectManagerClient (for eMAD role: Project Manager)
├── Inherits: Base + Sequential Thinking
├── Adds: Knowledge graph/memory (track project state)
├── Adds: RAG for documentation
└── Used by: Hopper's PM eMAD

ParalegalClient (for eMAD role: Paralegal)
├── Inherits: Base + Sequential Thinking
├── Adds: RAG (legal database access)
├── Adds: Document processing
└── Used by: Legal eMADs (future)

... (more specialized clients as needed)
```

---

## Base Client Features

### LLMClientBase provides:

1. **Sequential Thinking Integration**
   - Access to Sequential Thinking MCP for structured reasoning
   - All clients get this foundational capability

2. **Conversation Interface**
   - Send prompts to LLM
   - Receive responses
   - Maintain conversation context

3. **LLM API Access**
   - Connect to underlying LLM via Fiedler
   - Handle API calls, retries, errors
   - Fiedler provides optimal LLM routing

4. **Token Management**
   - Track token usage
   - Budget awareness
   - Warnings on limits

---

## Specialized Clients

### ImperatorClient
**Purpose:** For MAD Imperators (simple reasoning tasks)
**Additions:** None beyond base
**Example usage:** Fiedler V1 Imperator reasoning about LLM recommendations

### SeniorDevClient
**Purpose:** For Senior Developer eMADs
**Additions:**
- Code execution (Python REPL, sandboxed)
- Reflection server (code review loop)
- Possibly: Git access, file system tools

### ProjectManagerClient
**Purpose:** For Project Manager eMADs
**Additions:**
- Knowledge graph/memory (persistent project state)
- RAG for documentation retrieval
- Planning/scheduling helpers

### ParalegalClient
**Purpose:** For Paralegal eMADs (future)
**Additions:**
- RAG for legal databases
- Document processing tools
- Citation checking

---

## Helper MCP Integration

**OPEN QUESTION - Deployment Architecture**

The library needs to integrate with helper MCPs like:
- Sequential Thinking (widely used MCP server - exists)
- Code execution (PAL)
- Reflection servers
- RAG servers
- Knowledge graphs

**Sequential Thinking exists** as one of the most widely used MCP servers. The question is: How do we deploy it within this infrastructure so that all LLMs can access it? Options include:
- Direct MCP relay connection
- Shared helper server
- Per-MAD deployment
- Library wrapper pattern

---

## Usage Example

```python
# Fiedler V1 Imperator
from llm_client import ImperatorClient

imperator = ImperatorClient(
    llm_provider="fiedler",  # or direct LLM API
    model="claude-sonnet-4.5"
)

response = imperator.reason(
    "Which LLM should I use for code review tasks?"
)
# Imperator uses Sequential Thinking internally
# Returns conversational response
```

```python
# Hopper Senior Dev eMAD
from llm_client import SeniorDevClient

senior_dev = SeniorDevClient(
    llm_provider="fiedler",
    model="gpt-5"
)

# Has code execution capability
result = senior_dev.execute_code("""
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)
print(fibonacci(10))
""")

# Has reflection capability
review = senior_dev.review_code(code_snippet)
```

---

## What the Library Must Provide

### Core Infrastructure (Required)
- **LLMClientBase** class - foundation for all clients
- **ImperatorClient** class - used by all V1 MADs for their Imperators
- Sequential Thinking integration
- Basic conversation interface
- Fiedler integration for LLM access

### Specialized Clients (Required for eMADs)
The library must define specialized clients for eMAD roles:
- **SeniorDevClient** - for Senior Developer eMADs (code execution, reflection)
- **JuniorDevClient** - for Junior Developer eMADs
- **ProjectManagerClient** - for PM eMADs (knowledge graph, RAG, planning)
- **ConsultantClient** - for consulting eMADs (domain-specific RAG)
- **TesterClient** - for testing eMADs
- **SecurityAnalystClient** - for security eMADs

These are needed from the start because eMADs are part of the V1 ecosystem (e.g., Hopper V1 spawns PM and Dev eMADs).

### Integration Requirements
- Helper MCP access patterns (Sequential Thinking, code execution, reflection, RAG)
- Rogers integration for state persistence
- Fiedler integration for optimal LLM routing

---

## Success Criteria

- ✅ LLMClientBase provides Sequential Thinking to all clients
- ✅ ImperatorClient successfully used by Fiedler V1
- ✅ Easy to extend for new specialized clients
- ✅ Clean inheritance model
- ✅ Documented API for client creation

---

## Open Questions

1. **Helper MCP deployment architecture** - How do we deploy Sequential Thinking and other helper MCPs so all LLMs can access them? (relay, shared server, per-MAD, library wrapper?)
2. **State management** - All conversational state lives in Rogers conversations (this is a fundamental architectural principle). How do clients interact with Rogers for state persistence?
3. **eMAD lifecycle** - How do ephemeral eMADs instantiate their specialized clients? Do they load the client library on spawn?
4. **Client initialization** - How does a client discover and connect to Fiedler? Via conversation or direct API?

---

*Requirements v1.0 - Inheritance-based LLM client library*
