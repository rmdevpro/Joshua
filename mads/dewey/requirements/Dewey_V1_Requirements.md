# Dewey V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Dewey is The Librarian - a DBA MAD that manages the data lake (Winnipesaukee/Winne). V1 adds an Imperator so you can ask database questions conversationally.

---

## Current Capabilities

- Database/data lake management
- (Specific capabilities TBD - need to review existing Dewey)

---

## What V1 Adds

### 1. Imperator
- LLM brain for Dewey
- Can answer DBA questions conversationally
- Uses LLM Client Library (ImperatorClient)

### 2. Conversation Capability
- New MCP tool: `dewey_converse`
- Ask questions about data, schemas, storage

### 3. Example Usage
```
User: "Hey Dewey, what tables do we have in the lake?"
User: "Dewey, how much storage are we using?"
User: "Show me the schema for conversation data"
```

---

## Open Questions

### Question 1: Data Access Through Conversation Bus?
**Current uncertainty:** How does data query/retrieval work in conversation paradigm?

**Options:**
- **Option A:** Data queries go through conversation bus (seems odd for large data)
- **Option B:** Data queries still use direct API/tools, only management conversations on bus
- **Option C:** Hybrid - small queries via conversation, large via API

**Need guidance on:** How to architect data access in conversation-based system?

### Question 2: What DBA Capabilities?
**Need to determine:**
- Schema management?
- Query optimization?
- Backup/restore?
- Data migration?
- Performance monitoring?

(Review existing Dewey implementation to answer)

---

## Success Criteria

- ✅ Can ask Dewey about database/lake status
- ✅ Dewey responds conversationally
- ✅ Existing data operations still work

---

*Requirements v1.0 - Awaiting data access architecture guidance*

---

## Conversation History

### V1 Pattern Discussion

**User:** 4 is accurante. I dont know what capabilities he will need, but they should be DBA like. I imagine access to the Lake will be through the Conversation Bus? Not sure how that would work, but his v1 would have an imperator that could ask queries to.

**Assistant:** Created requirements with Imperator for DBA conversational questions. Added open question: How does data query/retrieval work in conversation paradigm?

*Conversation captured: 2025-10-09*
