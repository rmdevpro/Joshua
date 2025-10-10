# MAD CP Library - MAD Conversation Protocol Library Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

The MAD CP (MAD Conversation Protocol) Library provides the foundational message parsing, formatting, and validation capabilities for all conversations in the MAD ecosystem. This library enables free-form, human-readable communication between MADs and humans while maintaining machine parseability.

**Purpose:** Standardize conversation message handling across all MADs without enforcing rigid protocols.

**Integration:** Library integrated into MCP Relay, accessible to all MADs.

---

## Core Principles (from MAD CP)

### 1. Three Content Types
- **Deterministic:** Commands and code (e.g., `import //irina/temp/conversation.yml`)
- **Fixed:** Data files, images - **linked via paths**, not embedded
- **Prose:** Natural language with abbreviations (e.g., `@Fiedler, r u ok?`)

### 2. Addressing
- **@ mentions:** Like Teams/Slack (e.g., `@Fiedler`, `@J`)
- **Namespace:** Humans and MADs share same namespace
- **Format:** `@name` anywhere in message

### 3. Tags
- **Format:** `#tagname` (hashtag prefix)
- **Examples:** `#ack`, `#status`, `#error`, `#human`, `#metric`
- **Purpose:** Categorization, filtering (future), routing hints
- **Location:** Can appear anywhere in message

### 4. Human Readability
- **Constitutional rules:** Prevent compression to incomprehensible formats
- **Abbreviations:** Common text shortcuts (u, r, hru, etc.)
- **Natural flow:** Chat-like, not formal protocol

---

## Functional Requirements

### FR1: Message Parsing

#### FR1.1: Parse @ Mentions
- **Input:** Message string
- **Output:** List of mentioned participants
- **Behavior:**
  - Extract all `@name` patterns from message
  - Return list of unique mentions
  - Preserve original message content
  - Handle variations: `@name`, `@name,`, `@name.`, `@name?`

**Example:**
```python
msg = "@Fiedler can u send @J the LLM costs for Jan"
mentions = parse_mentions(msg)
# Returns: ["Fiedler", "J"]
```

#### FR1.2: Parse Tags
- **Input:** Message string
- **Output:** List of tags
- **Behavior:**
  - Extract all `#tagname` patterns from message
  - Return list of unique tags
  - Preserve original message content
  - Handle variations: `#tag`, `#tag,`, `#tag.`

**Example:**
```python
msg = "Deploy complete #status #success"
tags = parse_tags(msg)
# Returns: ["status", "success"]
```

#### FR1.3: Parse Content Type
- **Input:** Message string
- **Output:** Content type classification
- **Types:** `deterministic`, `fixed`, `prose`
- **Heuristics:**
  - **Deterministic:** Starts with verb/command, contains paths/code
  - **Fixed:** Contains file paths, links, structured data
  - **Prose:** Natural language, conversational

**Example:**
```python
msg = "@Dewey import //irina/temp/conversation.yml"
content_type = classify_content(msg)
# Returns: "deterministic"

msg = "hey @Fiedler, r u ok?"
content_type = classify_content(msg)
# Returns: "prose"
```

#### FR1.4: Extract File Paths
- **Input:** Message string
- **Output:** List of file paths/links
- **Behavior:**
  - Extract paths starting with `/` or `//`
  - Extract URLs (http://, https://)
  - Return list of paths
  - Validate path format (optional)

**Example:**
```python
msg = "@Dewey import //irina/temp/conversation.yml and /mnt/data/results.json"
paths = extract_paths(msg)
# Returns: ["//irina/temp/conversation.yml", "/mnt/data/results.json"]
```

### FR2: Message Building

#### FR2.1: Build Message with Mentions
- **Input:** Content, list of mentions
- **Output:** Formatted message string
- **Behavior:**
  - Insert @ prefix for mentions
  - Place mentions naturally in content
  - Return formatted string

**Example:**
```python
msg = build_message("can u send the costs?", mentions=["Fiedler", "J"])
# Returns: "@Fiedler can u send @J the costs?"
# OR: could provide template with placeholders
```

#### FR2.2: Build Message with Tags
- **Input:** Content, list of tags
- **Output:** Formatted message string
- **Behavior:**
  - Append tags to message (or insert inline)
  - Add # prefix to tags
  - Return formatted string

**Example:**
```python
msg = build_message("Deploy complete", tags=["status", "success"])
# Returns: "Deploy complete #status #success"
```

#### FR2.3: Build Message with File Links
- **Input:** Content, list of file paths
- **Output:** Formatted message string
- **Behavior:**
  - Insert file paths into message
  - Validate paths exist (optional)
  - Return formatted string

**Example:**
```python
msg = build_message("@Dewey import", files=["//irina/temp/conversation.yml"])
# Returns: "@Dewey import //irina/temp/conversation.yml"
```

### FR3: Message Validation

#### FR3.1: Validate Message Format
- **Input:** Message string
- **Output:** Boolean (valid/invalid), error messages
- **Checks:**
  - Well-formed @ mentions
  - Well-formed tags
  - Valid file paths (if specified)
  - Human readability check (not hex, not compressed)

**Example:**
```python
msg = "@Fiedler r u ok?"
is_valid, errors = validate_message(msg)
# Returns: (True, [])

msg = "0x47445f44..."  # Hex compressed
is_valid, errors = validate_message(msg)
# Returns: (False, ["Message too compressed, not human-readable"])
```

#### FR3.2: Human Readability Check
- **Input:** Message string
- **Output:** Readability score or boolean
- **Heuristics:**
  - Check for excessive compression (hex, binary)
  - Check for common abbreviations (ok)
  - Check for natural language patterns (ok)
  - Reject if mostly non-alphanumeric

**Example:**
```python
msg = "0xABCDEF123456"
is_readable = check_readability(msg)
# Returns: False

msg = "@Dewey pls send logs"
is_readable = check_readability(msg)
# Returns: True
```

### FR4: Conversation Utilities

#### FR4.1: Parse Message Metadata
- **Input:** Message string
- **Output:** Structured metadata object
- **Extracts:**
  - Mentions
  - Tags
  - Content type
  - File paths
  - Core content (message without metadata markers)

**Example:**
```python
msg = "@Fiedler can u send @J the costs? //data/costs.csv #request"
metadata = parse_message(msg)
# Returns:
# {
#   "mentions": ["Fiedler", "J"],
#   "tags": ["request"],
#   "content_type": "prose",
#   "file_paths": ["//data/costs.csv"],
#   "core_content": "can u send the costs?"
# }
```

#### FR4.2: Format Message for Storage
- **Input:** Message object (sender, content, timestamp, etc.)
- **Output:** Standardized storage format (JSON)
- **Fields:**
  - sender
  - content
  - timestamp
  - mentions (extracted)
  - tags (extracted)
  - content_type (classified)
  - file_paths (extracted)

**Example:**
```python
msg_obj = {
  "sender": "J",
  "content": "@Fiedler r u ok? #status",
  "timestamp": "2025-10-09T14:30:00Z"
}
storage_format = format_for_storage(msg_obj)
# Returns:
# {
#   "sender": "J",
#   "content": "@Fiedler r u ok? #status",
#   "timestamp": "2025-10-09T14:30:00Z",
#   "mentions": ["Fiedler"],
#   "tags": ["status"],
#   "content_type": "prose",
#   "file_paths": []
# }
```

---

## Technical Requirements

### TR1: Language and Platform

#### TR1.1: Implementation Language
- **Primary:** Python (matches existing MAD stack)
- **Alternative:** JavaScript/TypeScript (if needed for Grace)
- **Consideration:** Multi-language bindings for flexibility

#### TR1.2: Package Structure
```
mad-cp/
├── __init__.py
├── parser.py        # Parsing functions
├── builder.py       # Message building functions
├── validator.py     # Validation functions
├── utils.py         # Utilities
├── models.py        # Data models
└── tests/
    ├── test_parser.py
    ├── test_builder.py
    └── test_validator.py
```

### TR2: Dependencies

#### TR2.1: Minimal Dependencies
- Standard library only (preferred for V1)
- Regex for pattern matching
- Optional: NLP library for content classification (defer to V2)

#### TR2.2: No External Services
- Library is self-contained
- No network calls
- No database dependencies
- Pure computation

### TR3: Performance

#### TR3.1: Parsing Speed
- Parse 1000 messages/second (single-threaded)
- Minimal memory footprint
- No blocking operations

#### TR3.2: Validation Speed
- Validate message in < 1ms
- Lightweight heuristics
- Optional deep validation

### TR4: Integration with Relay

#### TR4.1: Installation in Relay
- **Package:** Install `mad-cp` library in relay virtual environment
- **Import:** `from mad_cp import parse_message, build_message, validate_message`
- **Usage:** Relay can call library functions directly

#### TR4.2: Relay Utilities (Optional)
- Relay can provide MAD CP utilities as MCP tools
- Tool examples:
  - `mad_cp_parse_message`
  - `mad_cp_validate_message`
  - `mad_cp_build_message`
- Allows MADs to use MAD CP via MCP if needed

---

## API Specification

### API1: Parsing Functions

```python
# Parse @ mentions
parse_mentions(message: str) -> List[str]

# Parse tags
parse_tags(message: str) -> List[str]

# Classify content type
classify_content(message: str) -> str  # "deterministic" | "fixed" | "prose"

# Extract file paths
extract_paths(message: str) -> List[str]

# Parse full message metadata
parse_message(message: str) -> MessageMetadata
```

### API2: Building Functions

```python
# Build message with mentions
build_message_with_mentions(content: str, mentions: List[str]) -> str

# Build message with tags
build_message_with_tags(content: str, tags: List[str]) -> str

# Build message with file paths
build_message_with_paths(content: str, paths: List[str]) -> str

# Build complete message
build_message(content: str,
              mentions: List[str] = None,
              tags: List[str] = None,
              paths: List[str] = None) -> str
```

### API3: Validation Functions

```python
# Validate message format
validate_message(message: str) -> Tuple[bool, List[str]]  # (is_valid, errors)

# Check human readability
check_readability(message: str) -> bool

# Validate tag format
validate_tag(tag: str) -> bool

# Validate mention format
validate_mention(mention: str) -> bool
```

### API4: Utility Functions

```python
# Format message for storage
format_for_storage(message: Dict) -> Dict

# Strip metadata from message content
strip_metadata(message: str) -> str  # Remove @mentions, #tags, keep core content

# Extract core content
extract_core_content(message: str) -> str
```

---

## Data Models

### MessageMetadata
```python
@dataclass
class MessageMetadata:
    """Parsed message metadata"""
    mentions: List[str]
    tags: List[str]
    content_type: str  # "deterministic" | "fixed" | "prose"
    file_paths: List[str]
    core_content: str
    original_message: str
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    """Message validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    readability_score: float  # 0.0-1.0
```

---

## Testing Requirements

### Test Coverage

#### Unit Tests
- Parse mentions: various formats, edge cases
- Parse tags: various formats, edge cases
- Content classification: all three types
- File path extraction: various path formats
- Message building: all combinations
- Validation: valid and invalid messages
- Readability checks: various compression levels

#### Integration Tests
- Parse and rebuild message (round-trip)
- Validate built messages
- Handle malformed input gracefully

#### Performance Tests
- Parse 1000 messages < 1 second
- Validate 1000 messages < 1 second
- Memory usage stays bounded

---

## Success Criteria

### SC1: Parsing Accuracy
- ✅ Correctly extract @ mentions in 100% of test cases
- ✅ Correctly extract tags in 100% of test cases
- ✅ Classify content type with 90%+ accuracy

### SC2: Building Quality
- ✅ Built messages are human-readable
- ✅ Built messages parse correctly (round-trip)
- ✅ Built messages pass validation

### SC3: Validation Effectiveness
- ✅ Catch compressed/hex messages (readability check)
- ✅ Catch malformed mentions/tags
- ✅ No false positives on valid messages

### SC4: Integration Success
- ✅ Library installs in relay without issues
- ✅ Rogers can use library for message handling
- ✅ Grace can use library (if JS version available)

---

## Out of Scope (Deferred to V2+)

### V2 and Beyond
- Advanced NLP-based content classification
- Automatic abbreviation expansion
- Message translation (abbreviations → full text)
- Machine learning for readability scoring
- Multi-language support
- Emoji handling (if allowed)
- Conversation context-aware parsing
- Intelligent message suggestions
- Spelling/grammar correction
- Sentiment analysis

---

## Development Milestones

### Milestone 1: Core Parsing (Week 1)
- Implement mention parsing
- Implement tag parsing
- Implement path extraction
- Unit tests for parsing

### Milestone 2: Message Building (Week 2)
- Implement message builders
- Unit tests for building
- Round-trip tests (parse → build)

### Milestone 3: Validation (Week 3)
- Implement validation functions
- Implement readability checks
- Unit tests for validation

### Milestone 4: Integration (Week 4)
- Package library
- Install in relay
- Integration tests with Rogers
- Documentation

---

## Dependencies

### Critical Dependencies
1. **Python 3.8+** (or current relay Python version)
2. **Regex library** (standard library `re`)

### Optional Dependencies
- **Pytest** (for testing)
- **Type checking** (mypy)

---

## Risks and Mitigations

### Risk 1: Ambiguous Parsing
- **Impact:** @ mentions or tags in URLs, code snippets cause false positives
- **Mitigation:** Context-aware parsing, escape sequences, conservative extraction

### Risk 2: Performance Bottleneck
- **Impact:** Parsing/validation slows down message handling
- **Mitigation:** Optimize regex, cache compiled patterns, profile and optimize

### Risk 3: Readability Subjectivity
- **Impact:** Hard to define "human-readable" algorithmically
- **Mitigation:** Simple heuristics for V1, iterate based on usage

---

## Open Questions

1. **Escaping:** How to escape @ or # when not meant as mention/tag? (e.g., email addresses, prices)
2. **Case sensitivity:** Are mentions case-sensitive? `@fiedler` vs `@Fiedler`
3. **Length limits:** Max message length? Max mention count?
4. **Special characters:** What characters allowed in mention names? (alphanumeric + underscore?)
5. **JavaScript version:** Do we need JS/TS version for Grace, or can Grace use Python via API?

---

## Example Usage in Rogers

```python
from mad_cp import parse_message, validate_message, format_for_storage

# When Rogers receives a message
incoming_msg = "@Fiedler can u recommend an LLM for code review? #request"

# Validate
is_valid, errors = validate_message(incoming_msg)
if not is_valid:
    # Handle invalid message
    pass

# Parse metadata
metadata = parse_message(incoming_msg)
# metadata.mentions = ["Fiedler"]
# metadata.tags = ["request"]
# metadata.content_type = "prose"

# Store with metadata
storage_obj = format_for_storage({
    "sender": "J",
    "content": incoming_msg,
    "timestamp": "2025-10-09T14:30:00Z"
})
# Includes parsed mentions, tags, etc.

# Save to database
conversation_db.insert_message(storage_obj)
```

---

*MAD CP Library Requirements v1.0 - Foundation for conversation protocol*
