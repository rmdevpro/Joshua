# MAD CP Interface Library Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-10

---

## Overview
This document defines requirements for the MAD Conversation Protocol (CP) Interface Library. Its core principle is **format flexibility**. The library must enable, not enforce, communication patterns, treating all conversational formats as potentially valid. This is guided by a critical insight:

> "All of those suggestions around the conversation framework are perfect. They can all work at the same time. The system supports that. In fact the strength of the system is that if you send a format it doesn't recognize within the router, the other elements can figure it out. So a new unknown protocol is not unusable, it's just slow until the system learns it and makes its parsing more efficient."

---

## Requirements

### 1. Core Principle: Format Flexibility
#### Requirement 1.1: Support for Coexisting Patterns
**Priority:** High
**Description:** The library MUST support multiple, simultaneous conversational patterns within the same system and conversation. It shall not enforce a single, rigid syntax.

#### Requirement 1.2: Default Routing for Unknown Formats
**Priority:** High
**Description:** When the library's deterministic parsers encounter a message format they do not recognize, the message MUST be routed to the recipient MAD's Imperator for cognitive interpretation, optionally with a tag like `#unparsed`. This ensures a new protocol is functional, albeit slower, on first contact.

#### Requirement 1.3: Concrete Pattern Enablement
**Priority:** High
**Description:** The library MUST provide utilities to easily construct and parse messages in, but not be limited to, the following patterns:
- **Direct Command:** `@Dewey import //irina/temp/conversation.yml`
- **Persona Wrapper (Prose-first):**
  `"Alright @Dewey, I've finished my analysis. To proceed, please import the conversation archive from //irina/temp/conversation.yml so I can continue."`
- **Command-in-Prose (Brackets/Delimiters):**
  `"Hey @Dewey, I need to import the conversation file. Please do: [import: //irina/temp/conversation.yml]"`
- **Pure Prose:**
  `"Marco please search for peer-reviewed articles on BERT optimizations published after 2023"`

### 2. Message Structure
#### Requirement 2.1: Conversational Message Object
**Priority:** High
**Description:** The library MUST provide a standard message object that wraps technical metadata (sender ID, timestamp, trace ID) within a conversational context.

### 3. Interaction Mechanics
#### Requirement 3.1: @mention Addressing
**Priority:** High
**Description:** The library MUST support parsing and creating `@mention` syntax (e.g., `@Rogers`, `@Hopper`) as the primary mechanism for addressing a specific MAD.

#### Requirement 3.2: Tag Handling
**Priority:** High
**Description:** The library MUST support parsing and embedding tags (e.g., `#ack`, `#status:done`, `#error`) for metadata, filtering, and observability.

### 4. Content Types
#### Requirement 4.1: Support for Multiple Content Payloads
**Priority:** Medium
**Description:** The library MUST handle three distinct types of content within a message:
1.  **Deterministic Commands:** Structured, machine-readable instructions.
2.  **Fixed Content:** References to immutable data (e.g., file paths, URLs).
3.  **Prose:** Unstructured natural language for cognitive interpretation.

---

## Success Criteria
- ✅ A MAD can send a "Persona Wrapper" message and a "Direct Command" message to another MAD, and both are successfully processed.
- ✅ A message with a completely novel syntax is successfully routed to Imperator and interpreted correctly.
- ✅ The library can correctly parse `@mentions` and `#tags` from a block of prose.

---

## Dependencies
- Rogers Messaging Bus Requirements
- MAD Base Architecture Requirements

---

## Notes
The success of this library is measured by its ability to *get out of the way* and let natural language be the primary driver of interaction.

---

*Requirements v1.0 - English is the protocol.*

---
---