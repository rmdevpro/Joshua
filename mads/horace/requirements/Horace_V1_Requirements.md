# Horace V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Horace is The NAS Gateway - manages file systems and storage. V1 adds an Imperator so you can ask conversational questions about files and storage.

---

## Current Capabilities

- NAS/file system management
- File operations
- Storage coordination

---

## What V1 Adds

### 1. Imperator
- LLM brain for Horace
- Can answer questions about files, storage conversationally
- Uses LLM Client Library (ImperatorClient)

### 2. Conversation Capability
- New MCP tool: `horace_converse`
- Ask questions about files, directories, storage usage

### 3. Example Usage
```
User: "Hey Horace, where should I store temp files?"
User: "Horace, how much space is left on /mnt/irina_storage?"
User: "Show me what's in the project directory"
```

---

## Open Questions

### Question 1: File Access Through Conversation Bus?
**Similar to Dewey's data access question:**

**Options:**
- **Option A:** File operations go through conversation bus (seems odd for large files)
- **Option B:** File operations still use direct API/tools, only management conversations on bus
- **Option C:** Hybrid - file metadata/queries via conversation, actual file I/O via API

**Need guidance on:** How to architect file operations in conversation-based system?

---

## Success Criteria

- ✅ Can ask Horace about file/storage status
- ✅ Horace responds conversationally
- ✅ Existing file operations still work

---

*Requirements v1.0 - Awaiting file access architecture guidance*

---

## Conversation History

### V1 Pattern Discussion

**User:** [In response to "What should Horace V1 look like?"] yes I think so [similar pattern to Dewey - Imperator for file questions]

**Assistant:** Created requirements with Imperator for file system conversational questions. Added open question: How do file operations work in conversation paradigm (similar to Dewey's data access question)?

*Conversation captured: 2025-10-09*
