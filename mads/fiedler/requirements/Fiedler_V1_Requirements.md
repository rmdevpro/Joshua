# Fiedler V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Fiedler V1 adds an **Imperator** (LLM brain) to the existing Fiedler MCP server, enabling conversational LLM recommendations while keeping all existing orchestration tools unchanged.

---

## What Fiedler Currently Has

- MCP tools: `fiedler_send`, `fiedler_list_models`, `fiedler_get_config`, etc.
- Orchestrates 20+ LLMs across multiple providers
- Knows LLM characteristics (costs, capabilities, context limits, etc.)
- Docker deployment with secure API key storage

---

## What V1 Adds

### 1. Imperator
- LLM brain for Fiedler
- Uses **LLM Client Library** (see separate requirements)
- Can reason about which LLM fits a given task

### 2. Conversation Capability
- New MCP tool: `fiedler_converse` (or similar name)
- Accepts natural language questions about LLMs
- Returns conversational responses

### 3. Example Usage
```
User: "Hey Fiedler, who should I use for my code review task?"

Fiedler's Imperator:
- Reasons about requirements (code understanding, accuracy)
- Considers LLM characteristics (which models are good at code)
- Recommends: "I'd suggest GPT-5 or Claude Sonnet 4.5 - both excel at code review"
```

### 4. Existing Tools Unchanged
- `fiedler_send`, `fiedler_list_models`, etc. still work as before
- No changes to existing functionality
- Imperator is additive only

---

## What V1 Does NOT Include

- Joining Rogers conversation bus (deferred to V2)
- Making existing tools conversational
- Advanced routing intelligence (DTR/LPPM)
- eMAD spawning

---

## Dependencies

### Critical Dependency: LLM Client Library
Fiedler V1 requires the **LLM Client Library** (see separate requirements) which provides:
- Base client with Sequential Thinking MCP
- Imperator-specific client class
- Helper MCP integration (architecture TBD - see open questions)

---

## Open Architecture Questions

**For expert consultation:**

### Question 1: How should helper MCPs be structured?

**Context:**
- Fiedler has an **MCP Server** (what it offers TO the ecosystem)
- Fiedler's Imperator needs **helper MCPs** (Sequential Thinking, etc.) for internal reasoning
- These are different things

**Options:**
1. **Library approach:** Import helpers as Python libraries (simple, no extra containers)
2. **Shared helper MCP server:** One container with all helper tools, all MADs connect to it
3. **Use existing MCP servers via relay:** Sequential Thinking already available in relay, just use that

**Need guidance on:** Best architecture for scalability, maintainability, resource efficiency

### Question 2: Should each MAD run helper MCPs in its own container?
- Pro: Isolation, independent scaling
- Con: Resource duplication, more containers to manage

### Question 3: Can helper MCPs be shared across all Imperators/eMADs?
- All would use same Sequential Thinking server
- Does this create contention or state issues?

---

## Success Criteria

- ✅ Fiedler can answer: "Who should I use for X task?"
- ✅ Imperator uses Sequential Thinking for reasoning
- ✅ Existing MCP tools still work
- ✅ Conversational responses are helpful and accurate

---

*Requirements v1.0 - Awaiting expert input on helper MCP architecture*

---

## Conversation History

### LLM Client Library & Helper MCPs Discussion

**User:** Ok, lets do fielder then. In order to add the imperator, we are going to have to create some kind of LLM client library that will serve both the imperator and the LLM emads. It would include some basic MCP Servers that assist all LLMs in our case.

[Discussion of Sequential Thinking MCP and other helper MCPs like code execution, reflection servers, RAG]

**User:** well we need to see the LLM clients through the lense of inherticance. So you probably hae a base clent that has just sequential thinking, then there are specilize ones that you can see used by the emads. A Senior Code Engineer would possily get a different set of augmenting capabilities to a Project Manager, or a Paralegal.

**Assistant:** Perfect - inheritance model!
```
LLMClientBase
├── Sequential Thinking MCP (everyone gets this)
└── Specialized clients:
    ├── ImperatorClient
    ├── SeniorDevClient (+ code execution, reflection)
    ├── ProjectManagerClient (+ knowledge graph, RAG)
    └── ParalegalClient (+ legal RAG, doc processing)
```

**User:** yes that is right. I'm torn about the MCP server part of this because each MAD will have an MCP server. Do we just add sequential thinking to the MAD MCP server? Does it just run in a single container as a helper tool? And if there are other MCP Servers out there that help the client, do they need to be MCP Servers? Or are we best coding it a different way? I don't know enough about this to decide.

**Assistant:** Great architectural question! Options:
1. Library approach (import as Python libraries)
2. Shared helper MCP server (one container, all helpers)
3. Use existing MCP servers via relay (Sequential Thinking already available)

**User:** Lets generate the requirements with the question left open so the experts can guide us.

*Conversation captured: 2025-10-09*
