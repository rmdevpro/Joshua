# Gates Document Generation Gateway - Triplet Consultation Package

**Purpose:** Architectural review and design validation for Gates, the ICCM document generation gateway

**Component:** Gates (Markdown → ODT converter with Playfair diagram integration)

**Review Type:** Architecture, technology choices, implementation approach

---

## Context

Gates is a new ICCM gateway service that converts Markdown to OpenDocument Text (ODT) format with embedded diagrams from Playfair. This fills a critical gap: Fiedler generates text, Playfair generates diagrams, but no component can combine them into professional documents.

**Use Case:** Convert ICCM academic papers (currently 15+ papers in `/mnt/projects/ICCM/docs/papers/`) from Markdown to ODT format with embedded architecture diagrams, flowcharts, and technical illustrations.

**Requirements Document:** `/mnt/projects/ICCM/gates/REQUIREMENTS.md` (full specification attached below)

---

## Critical Design Questions for Triplet Review

Please provide your expert analysis on these 5 architectural decisions:

### Question 1: ODT Generation Approach

**Options:**
- **A) Direct XML generation** - Build content.xml, styles.xml, meta.xml manually using JSZip
  - Pros: Full control, no external dependencies, lighter container
  - Cons: Complex XML structure, more code to maintain

- **B) LibreOffice headless** - Use `libreoffice --headless --convert-to odt`
  - Pros: Simple implementation, battle-tested conversion
  - Cons: Heavy dependency (~400MB), slower startup

- **C) Hybrid** - Direct XML preferred, LibreOffice fallback for edge cases
  - Pros: Best of both worlds
  - Cons: Increased complexity, dual code paths

**Your recommendation:** Which approach balances simplicity, reliability, and maintainability?

### Question 2: Markdown Parser Selection

**Options:**
- **A) markdown-it** - Comprehensive, plugin-based, 14k stars
  - Pros: Full CommonMark + GFM support, extensible
  - Cons: Larger bundle size

- **B) marked** - Fast, simple, 33k stars
  - Pros: Faster parsing, simpler API
  - Cons: Fewer built-in extensions

- **C) remark** - AST-based, unified ecosystem
  - Pros: Powerful transformations, plugin ecosystem
  - Cons: Steeper learning curve, more complex

**Your recommendation:** Which parser best suits academic paper conversion with tables, code blocks, and complex formatting?

### Question 3: Concurrent Request Handling

**Options:**
- **A) FIFO queue** (Playfair pattern) - Single worker, queued requests
  - Pros: Simple, proven in Playfair
  - Cons: No parallelism, slower for multiple requests

- **B) Worker pool** - Multiple parallel workers (3-5)
  - Pros: Better throughput
  - Cons: More complex, resource contention

- **C) Hybrid** - Queue + workers with priority
  - Pros: Balanced performance
  - Cons: Most complex

**Context:** Expected usage is occasional document generation (not high-volume API)

**Your recommendation:** Which approach fits ICCM's usage pattern?

### Question 4: Diagram Embedding Format

**Options:**
- **A) PNG only** (current plan) - Convert all Playfair diagrams to PNG
  - Pros: Universal ODT support, predictable rendering
  - Cons: Raster format, larger file sizes

- **B) SVG only** - Embed Playfair SVG directly
  - Pros: Vector format, smaller files, scalable
  - Cons: ODT SVG support varies by application

- **C) User choice** - Parameter to select PNG vs SVG
  - Pros: Flexibility
  - Cons: More testing surface, documentation complexity

**Your recommendation:** What format ensures maximum compatibility while maintaining quality?

### Question 5: Document Size Limits

**Current Proposal:**
- Input markdown: 10MB max
- Output ODT: 50MB max
- Embedded images: 5MB per image

**Context:** ICCM papers are typically 40-60KB markdown with 5-10 diagrams

**Your recommendation:** Are these limits reasonable? Should they be higher/lower for Phase 1?

---

## Full Requirements Document

```markdown
[FULL CONTENTS OF /mnt/projects/ICCM/gates/REQUIREMENTS.md INSERTED BELOW]
```

# Gates Document Generation Gateway - Requirements Specification

**Version:** 1.0
**Date:** 2025-10-04
**Status:** Draft - Awaiting Triplet Review
**Component:** Gates (ICCM Document Generation Gateway)

[... full requirements document ...]

---

## Review Instructions

Please provide:

1. **Answer to each of the 5 questions above** with technical reasoning
2. **Overall architecture assessment** - Is the design sound?
3. **Risk identification** - What could go wrong?
4. **Implementation recommendations** - Best practices, libraries, patterns
5. **Timeline estimate** - How long for Phase 1 MVP implementation?
6. **Final verdict:** APPROVE for implementation / REQUEST CHANGES / REJECT with reasons

**Format your response as:**
- Clear answers to Questions 1-5
- Architecture assessment (strengths/weaknesses)
- Implementation guidance
- Timeline estimate
- Final recommendation

Thank you for your expert review.
# Gates Document Generation Gateway - Requirements Specification

**Version:** 1.0
**Date:** 2025-10-04
**Status:** Draft - Awaiting Triplet Review
**Component:** Gates (ICCM Document Generation Gateway)

---

## 1. Executive Summary

### 1.1 Purpose

Gates addresses a critical gap in the ICCM ecosystem: while Fiedler generates text and Playfair generates diagrams, there is no capability to combine these into professional document formats. Gates provides Markdown-to-ODT conversion, enabling LLMs to produce complete, formatted documents with embedded diagrams suitable for academic papers, technical reports, and professional documentation.

### 1.2 Position in ICCM Architecture

**Component Type:** Gateway Service (WebSocket MCP)
**Dependencies:**
- **Playfair** (optional) - Diagram generation for visual aids
- **Fiedler** (optional) - Text generation via LLM orchestra
- **Standalone** - Can accept pre-generated Markdown from any source

**Integration Point:** MCP Relay → Gates (ws://localhost:9050)

### 1.3 Phase 1 Scope

**Primary Goal:** Markdown → ODT conversion with embedded diagrams
**Format:** OpenDocument Text (.odt) - ISO/IEC 26300 standard
**License:** All dependencies must be permissive (MIT, Apache-2.0, LGPL acceptable)

**Out of Scope for Phase 1:**
- PowerPoint/Presentation formats (Phase 2)
- PDF generation (Phase 2)
- DOCX format (Phase 2 - if needed)
- Natural language → document (LLMs already do this via Markdown)
- Document editing/modification (create-only)

---

## 2. Functional Requirements

### 2.1 Core Capability: Markdown to ODT Conversion

**Input:** Markdown text (string or file path)
**Output:** ODT document (base64-encoded or file path)

**Supported Markdown Features (from paper analysis):**

#### Text Formatting
- **Headings:** H1-H6 (`#`, `##`, `###`, `####`, `#####`, `######`)
- **Bold:** `**bold**` or `__bold__`
- **Italic:** `*italic*` or `_italic_`
- **Bold+Italic:** `***bold italic***`
- **Inline Code:** `` `code` ``
- **Strikethrough:** `~~strikethrough~~` (optional)

#### Block Elements
- **Paragraphs:** Text separated by blank lines
- **Code Blocks:** Fenced (` ``` `) with optional language syntax
- **Blockquotes:** `> quoted text`
- **Horizontal Rules:** `---` or `***` or `___`

#### Lists
- **Unordered Lists:** `-`, `*`, or `+` bullets
- **Ordered Lists:** `1.`, `2.`, etc.
- **Nested Lists:** Indentation-based (2 or 4 spaces)
- **Task Lists:** `- [ ]` and `- [x]` (optional)

#### Tables
- **Markdown Tables:** Pipe-delimited with header separator
  ```markdown
  | Column 1 | Column 2 |
  |----------|----------|
  | Data 1   | Data 2   |
  ```
- **Alignment:** `:---` (left), `:---:` (center), `---:` (right)

#### Links and References
- **Inline Links:** `[text](url)`
- **Reference Links:** `[text][ref]` with `[ref]: url` definition
- **Auto-links:** `<https://example.com>`
- **Internal Links:** `[Section Title](#section-title)` (anchor-based)

#### Images
- **Inline Images:** `![alt text](image_url_or_path)`
- **Reference Images:** `![alt][ref]` with `[ref]: path` definition
- **Image Embedding:** Support base64 data URIs and file paths

### 2.2 Diagram Integration (Playfair Integration)

**Capability:** Detect Playfair diagram blocks and convert to embedded images

**Syntax Recognition:**
```markdown
```playfair-dot
digraph G { A -> B; }
```

```playfair-mermaid
graph TD
  A --> B
```
```

**Process:**
1. Parse Markdown, identify `playfair-*` code blocks
2. Extract diagram content and format (dot/mermaid)
3. Call Playfair MCP tool: `playfair_create_diagram(content, format, output_format="png")`
4. Receive base64-encoded PNG
5. Decode and embed as image in ODT at block location
6. Include alt text from preceding line if present

**Fallback:**
- If Playfair unavailable: Render code block as-is with warning comment
- If diagram generation fails: Insert error message in document

### 2.3 Document Styling

**Default Style:** Academic/Professional Paper
- **Font:** Liberation Serif (body), Liberation Sans (headings)
- **Font Size:** 12pt body, 14pt H3, 16pt H2, 18pt H1
- **Line Spacing:** 1.15 (single spacing with breathing room)
- **Margins:** 1 inch all sides (2.54cm)
- **Page Size:** US Letter (8.5" x 11") or A4 (user preference)

**Heading Styles:**
- H1: 18pt, Bold, Liberation Sans, centered (optional)
- H2: 16pt, Bold, Liberation Sans
- H3: 14pt, Bold, Liberation Sans
- H4: 12pt, Bold Italic, Liberation Serif

**Code Block Formatting:**
- Font: Liberation Mono, 10pt
- Background: Light gray (#f5f5f5)
- Border: 1pt solid #cccccc
- Padding: 0.2cm all sides
- Syntax highlighting: Phase 2 (optional)

**Table Formatting:**
- Header row: Bold, background #e8e8e8
- Borders: 1pt solid #cccccc
- Cell padding: 0.1cm
- Auto-width columns

### 2.4 MCP Tools

**Tool 1: `gates_create_document`**

**Input Parameters:**
```json
{
  "content": "string (markdown text)",
  "title": "string (optional - document title metadata)",
  "author": "string (optional - author metadata)",
  "enable_playfair": "boolean (default: true - auto-convert diagram blocks)",
  "page_size": "string (optional: 'letter' or 'a4', default: 'letter')",
  "output_encoding": "string (optional: 'base64' or 'file', default: 'base64')"
}
```

**Output:**
```json
{
  "success": true,
  "format": "odt",
  "encoding": "base64",
  "data": "base64_encoded_odt_file",
  "size_bytes": 12345,
  "metadata": {
    "title": "Document Title",
    "pages": 5,
    "diagrams_embedded": 2
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "CONVERSION_FAILED",
    "message": "Failed to parse markdown: Invalid table syntax at line 45",
    "details": "..."
  }
}
```

**Tool 2: `gates_validate_markdown`**

**Input:**
```json
{
  "content": "string (markdown text)"
}
```

**Output:**
```json
{
  "valid": true,
  "warnings": [
    "Line 23: Unclosed code block detected",
    "Line 67: Table missing header separator"
  ],
  "features_detected": {
    "headings": 15,
    "code_blocks": 7,
    "tables": 3,
    "images": 2,
    "playfair_diagrams": 2
  }
}
```

**Tool 3: `gates_list_capabilities`**

**Output:**
```json
{
  "markdown_features": ["headings", "code_blocks", "tables", "lists", "links", "images"],
  "diagram_integration": true,
  "output_formats": ["odt"],
  "page_sizes": ["letter", "a4"],
  "max_document_size": "10MB",
  "playfair_available": true
}
```

---

## 3. Technical Architecture

### 3.1 Technology Stack

**Core Library:** `odt.js` or `docxtemplater` with ODT support or custom ODT XML generation

**Markdown Parser:** `markdown-it` (MIT license)
- Comprehensive CommonMark support
- Plugin architecture for extensions
- Active maintenance

**ODT Generation:** Direct XML generation using JSZip (MIT/GPL)
- ODT = ZIP archive containing XML files
- `content.xml` - Document content
- `styles.xml` - Document styles
- `meta.xml` - Document metadata

**Alternative:** `libreoffice --headless --convert-to odt` (if needed)
- Fallback for complex conversions
- Requires LibreOffice installation in container

### 3.2 Container Architecture

**Base Image:** `node:22-bookworm-slim`

**Required Packages:**
- Node.js 22+ (for JavaScript runtime)
- LibreOffice (headless) - Optional fallback

**Container Specifications:**
- **Memory Limit:** 1GB (document processing)
- **CPU Limit:** 2 cores
- **Disk:** 500MB workspace for temp files
- **Network:** `iccm_network` (Docker internal)

**Ports:**
- **9050:** Host port (MCP WebSocket)
- **8050:** Container internal port

### 3.3 MCP Server Implementation

**Protocol:** WebSocket MCP (same pattern as Playfair)

**Server Components:**
1. **WebSocket Server:** `ws` library
2. **MCP Protocol Handler:** JSON-RPC 2.0 with MCP extensions
3. **Markdown Processor:** Parse → Transform → Generate ODT
4. **Diagram Processor:** Detect Playfair blocks → Call MCP tool → Embed images
5. **ODT Generator:** Build XML structure → Package as ZIP

**Request Flow:**
```
Client → MCP Relay → Gates WebSocket
  ↓
Parse JSON-RPC request
  ↓
Validate markdown content
  ↓
Parse markdown (markdown-it)
  ↓
Detect Playfair diagram blocks
  ↓
[If diagrams] → Call Playfair MCP → Receive PNG → Embed
  ↓
Generate ODT XML (content.xml, styles.xml, meta.xml)
  ↓
Package as ZIP archive
  ↓
Base64 encode
  ↓
Return JSON-RPC response
```

### 3.4 File Structure

```
/mnt/projects/ICCM/gates/
├── server.js                 # WebSocket MCP server
├── markdown-processor.js     # Markdown parsing and conversion
├── odt-generator.js          # ODT XML generation
├── diagram-handler.js        # Playfair integration
├── styles.js                 # ODT style definitions
├── mcp-tools.js              # MCP tool definitions
├── package.json              # Dependencies
├── Dockerfile                # Container definition
├── docker-compose.yml        # Docker Compose config
├── REQUIREMENTS.md           # This file
├── README.md                 # User documentation
└── examples/                 # Example markdown files
    ├── academic_paper.md
    ├── technical_doc.md
    └── simple_doc.md
```

---

## 4. Performance Requirements

### 4.1 Response Time Targets

**Simple Documents** (<50KB markdown, no diagrams):
- **Target:** <2 seconds
- **Max:** 5 seconds

**Medium Documents** (50-200KB, <5 diagrams):
- **Target:** <10 seconds
- **Max:** 30 seconds

**Complex Documents** (200KB-1MB, 5-20 diagrams):
- **Target:** <30 seconds
- **Max:** 60 seconds

**Timeout:** 120 seconds (hard limit)

### 4.2 Resource Limits

**Memory:**
- Per request: 200MB max
- Container limit: 1GB

**Document Size:**
- Input markdown: 10MB max
- Output ODT: 50MB max
- Embedded images: 5MB per image max

**Concurrent Requests:**
- Phase 1: FIFO queue (1 request at a time)
- Queue size: 10 requests max
- Reject if queue full

---

## 5. Error Handling

### 5.1 Markdown Parsing Errors

**Invalid Syntax:**
- Attempt best-effort parsing
- Return warnings in validation response
- Include partial conversion with error markers

**Unsupported Features:**
- Log warning
- Convert to closest supported equivalent
- Example: Custom HTML → Plain text with warning

### 5.2 Diagram Generation Errors

**Playfair Unavailable:**
- Skip diagram conversion
- Render as code block with comment: `<!-- Diagram conversion unavailable -->`

**Diagram Rendering Failed:**
- Insert error message in document: `[Error: Failed to render diagram - {error_message}]`
- Log error for debugging
- Continue processing document

### 5.3 ODT Generation Errors

**XML Generation Failed:**
- Return detailed error response
- Include line number and context
- Suggest corrections if possible

**File Size Exceeded:**
- Return error with size limits
- Suggest splitting document or reducing images

---

## 6. Security and Validation

### 6.1 Input Validation

**Markdown Content:**
- Size limit: 10MB
- UTF-8 encoding only
- No binary data in markdown text

**File Paths (if supported):**
- Must be absolute paths
- No directory traversal (`../`)
- Whitelist allowed directories

**Base64 Images:**
- Validate base64 encoding
- Check MIME type (PNG, JPEG, SVG only)
- Size limit: 5MB per image

### 6.2 Resource Protection

**Memory:**
- Kill process if memory exceeds container limit
- Return timeout error if processing takes >120s

**Disk:**
- Clean up temp files after each request
- Maximum 10 temp files at once
- Delete files older than 1 hour

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Markdown Parsing:**
- All markdown features from section 2.1
- Edge cases (nested lists, tables, code blocks)
- Malformed markdown handling

**ODT Generation:**
- XML structure validation
- Style application correctness
- ZIP archive integrity

**Diagram Integration:**
- Playfair block detection
- Base64 decoding
- Image embedding

### 7.2 Integration Tests

**End-to-End:**
- Convert example academic paper to ODT
- Verify LibreOffice can open result
- Check formatting preservation

**Playfair Integration:**
- Test with Playfair running
- Test with Playfair unavailable
- Test with diagram errors

### 7.3 Performance Tests

**Load Testing:**
- 10 concurrent simple documents
- 5 concurrent medium documents
- 1 large complex document

**Stress Testing:**
- Maximum markdown size (10MB)
- Maximum diagrams (20)
- Memory leak detection (100 sequential requests)

---

## 8. Deployment

### 8.1 Docker Container

**Build:**
```bash
cd /mnt/projects/ICCM/gates
docker compose build
```

**Run:**
```bash
docker compose up -d
```

**Health Check:**
```bash
curl http://localhost:9050/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "gates",
  "version": "1.0.0",
  "markdown_parser": "ready",
  "odt_generator": "ready",
  "playfair_available": true
}
```

### 8.2 MCP Relay Integration

**Configuration:** `/mnt/projects/ICCM/mcp-relay/backends.yaml`

```yaml
backends:
  - name: gates
    url: ws://localhost:9050
```

**Verification:**
```bash
relay_get_status
```

**Expected:** 3 Gates tools available

---

## 9. Future Enhancements (Phase 2)

### 9.1 Additional Output Formats

- **PDF:** Direct PDF generation (via LibreOffice or PDF library)
- **DOCX:** Microsoft Word format support
- **ODP:** OpenDocument Presentation (PowerPoint equivalent)
- **HTML:** Self-contained HTML with embedded CSS/images

### 9.2 Advanced Features

- **Table of Contents:** Auto-generate from headings
- **Page Numbers:** Header/footer with page numbers
- **Bibliography:** Citation management
- **Index:** Auto-generate index from keywords
- **Templates:** Pre-defined document styles
- **Syntax Highlighting:** Code block syntax coloring

### 9.3 Performance Optimization

- **Parallel Processing:** Multiple workers for concurrent requests
- **Caching:** Cache parsed markdown for regeneration
- **Streaming:** Stream ODT generation for large documents

---

## 10. Dependencies and Licenses

### 10.1 JavaScript Libraries

| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| `markdown-it` | ^14.0.0 | MIT | Markdown parsing |
| `jszip` | ^3.10.0 | MIT/GPL | ZIP archive creation |
| `ws` | ^8.17.0 | MIT | WebSocket server |
| `uuid` | ^9.0.0 | MIT | Request ID generation |

### 10.2 System Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| LibreOffice (optional) | MPL 2.0 | Fallback conversion |
| Node.js 22 | MIT | JavaScript runtime |

**License Compliance:** All dependencies use permissive licenses (MIT, MPL). No copyleft (GPL) in runtime dependencies.

---

## 11. Success Criteria

### 11.1 Phase 1 MVP Acceptance

**Must Have:**
- ✅ Convert markdown to ODT with all features from section 2.1
- ✅ Embed Playfair diagrams as PNG images
- ✅ 3 MCP tools functional (create, validate, capabilities)
- ✅ LibreOffice can open generated ODT files
- ✅ Performance targets met for simple/medium documents
- ✅ MCP Relay integration working

**Nice to Have:**
- Syntax highlighting in code blocks
- Custom styling options
- Template support

### 11.2 Production Readiness

- ✅ Container builds and runs
- ✅ Health check endpoint responding
- ✅ All tests passing (unit + integration)
- ✅ Documentation complete (README + examples)
- ✅ Error handling covers all edge cases
- ✅ Resource limits enforced

---

## 12. Open Questions for Triplet Review

1. **ODT Generation Approach:**
   - Direct XML generation (more control, more complex)
   - LibreOffice headless conversion (simpler, heavier dependency)
   - Hybrid (XML preferred, LibreOffice fallback)?

2. **Markdown Parser:**
   - `markdown-it` (comprehensive, plugin-based)
   - `marked` (faster, simpler)
   - `remark` (AST-based, more powerful)

3. **Concurrent Request Handling:**
   - FIFO queue (Playfair pattern)
   - Worker pool (parallel processing)
   - Hybrid (queue + workers)

4. **Diagram Embedding:**
   - Always PNG (current plan)
   - Support SVG embedding in ODT
   - User choice via parameter

5. **Document Size Limits:**
   - 10MB markdown reasonable?
   - 50MB ODT output reasonable?
   - Adjust based on use cases?

---

**Document Control:**
- **Version:** 1.0 (Draft)
- **Date:** 2025-10-04
- **Author:** Claude Code
- **Next Step:** Submit for Triplet Review (Fiedler's default triplet)
- **Approval Required:** User + Triplet Consensus
