# Gates Document Generation Gateway - Requirements Specification

**Version:** 2.0
**Date:** 2025-10-04
**Status:** ✅ **APPROVED** - Unanimous Triplet Consensus
**Component:** Gates (ICCM Document Generation Gateway)

---

## CHANGELOG

### Version 2.0 (2025-10-04)
- **Status:** Draft → APPROVED (Unanimous triplet consensus achieved)
- **Critical Decisions Finalized:**
  - ODT Generation: LibreOffice headless (Option B) - unanimous Round 2 consensus
  - Markdown Parser: markdown-it with plugins - unanimous Round 1
  - Concurrency: FIFO queue (Playfair pattern) - unanimous Round 1
  - Diagram Format: PNG only at 300 DPI - unanimous Round 1
  - Image Size Limit: Increased from 5MB → 10MB per image
- **Architecture:** Added Phase 2 migration path ("Strangler Fig" pattern to native XML)
- **Timeline:** Confirmed 4 weeks for Phase 1 MVP

### Version 1.0 (2025-10-04)
- Initial draft requirements
- 5 open architectural questions for triplet review

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

### 1.3 Phase 1 Scope (MVP - 4 Weeks)

**Primary Goal:** Markdown → ODT conversion with embedded diagrams
**Format:** OpenDocument Text (.odt) - ISO/IEC 26300 standard
**ODT Generation:** LibreOffice headless via robust process manager
**License:** All dependencies must be permissive (MIT, Apache-2.0, LGPL acceptable)

**In Scope for Phase 1:**
- ✅ Markdown → ODT conversion with LibreOffice headless
- ✅ Playfair diagram integration (PNG embedding)
- ✅ Academic paper styling (hard-coded styles)
- ✅ 3 MCP tools (create, validate, capabilities)
- ✅ FIFO queue for request handling (queue depth 10)
- ✅ WebSocket MCP server on port 9050
- ✅ Comprehensive error handling and fallbacks

**Out of Scope for Phase 1:**
- ❌ PowerPoint/Presentation formats (Phase 2)
- ❌ PDF generation (Phase 2)
- ❌ DOCX format (Phase 2 - if needed)
- ❌ Natural language → document (LLMs already do this via Markdown)
- ❌ Document editing/modification (create-only)
- ❌ Custom style templates (hard-coded academic style for Phase 1)
- ❌ SVG diagram embedding (PNG only for Phase 1)
- ❌ Direct XML ODT generation (deferred to Phase 2)

### 1.4 Phase 2 Scope (Future - Optimization)

**Primary Goal:** Incremental migration to native XML generation using "Strangler Fig" pattern

**Phase 2 Migration Strategy:**
1. **Phase 1.5 (Post-Launch):** Instrument and gather data
   - Log document complexity metrics (tables, lists, nesting depth)
   - Monitor LibreOffice resource usage (CPU, memory, duration)
   - Identify simple vs complex document distribution

2. **Phase 2 (Future):** Strangler Fig migration
   - Build native XML generator incrementally (start with paragraphs/headings)
   - Route simple documents (95%+) → Native XML generator
   - Route complex documents (5%) → LibreOffice fallback
   - Container optimization: 400MB → 260MB (Alpine) → 100MB (partial native) → 50MB (full native)

**Decision Criteria for Phase 2:**
- Trigger: >95% of documents are "simple" (no nested tables, max 2-level lists)
- OR: Container costs become prohibitive
- OR: Performance bottlenecks identified in production

**Phase 2 Additional Features:**
- Custom style templates (user-provided ODT template)
- SVG diagram embedding (if ODT viewer compatibility improves)
- Worker pool concurrency (if usage increases)
- Font embedding for consistent cross-platform rendering
- Diagram caching for repeated requests

---

## 2. Functional Requirements

### 2.1 Core Capability: Markdown to ODT Conversion

**Input:** Markdown text (string or file path)
**Output:** ODT document (base64-encoded or file path)

**Supported Markdown Features (from ICCM papers analysis):**

#### Text Formatting
- **Headings:** H1-H6 (`#` through `######`)
- **Emphasis:** Bold (`**text**`), Italic (`*text*`), Strikethrough (`~~text~~`)
- **Paragraphs:** Multi-paragraph support with proper spacing
- **Line breaks:** Hard breaks (`  \n` or `\n\n`)

#### Lists
- **Unordered lists:** `- item` or `* item`
- **Ordered lists:** `1. item`
- **Nested lists:** Up to 4 levels deep (from paper analysis)
- **Task lists:** `- [ ]` unchecked, `- [x]` checked (markdown-it-task-lists plugin)

#### Code
- **Inline code:** `` `code` ``
- **Fenced code blocks:** ` ```language\ncode\n``` `
- **Syntax highlighting:** Preserve language identifier in ODT (Phase 1: monospace font only)

#### Tables
- **GFM tables:** Pipe-delimited with header separator
- **Complex tables:** Multi-line cells, alignment (`:---`, `:---:`, `---:`)
- **Nested tables:** Support via markdown-it-multimd-table plugin

#### Links and Images
- **Hyperlinks:** `[text](url)`
- **Images (standard):** `![alt](url)` or `![alt](data:image/png;base64,...)`
- **Images (Playfair):** Special code blocks (see section 2.2)

#### Block Elements
- **Blockquotes:** `> quote text`
- **Horizontal rules:** `---` or `***`

### 2.2 Playfair Diagram Integration

**Mechanism:** Custom markdown-it plugin to intercept special fence blocks

**Supported Diagram Types:**

#### Graphviz (DOT)
```markdown
```playfair-dot
digraph G {
  A -> B;
  B -> C;
}
```
```

#### Mermaid
```markdown
```playfair-mermaid
graph TD
  A[Start] --> B[Process]
  B --> C[End]
```
```

**Processing Flow:**
1. markdown-it parser encounters `playfair-dot` or `playfair-mermaid` fence
2. Custom plugin extracts diagram content
3. Async MCP call to Playfair: `playfair_create_diagram(content, format, theme)`
4. Playfair returns PNG image (base64 or binary)
5. Plugin replaces fence block with image token: `<img src="data:image/png;base64,...">`
6. LibreOffice embeds image in final ODT

**Diagram Configuration:**
- **Format:** PNG only (300 DPI for print quality)
- **Theme:** Use Playfair's default theme (user customization in Phase 2)
- **Timeout:** 10 seconds per diagram (fallback on timeout)
- **Size limit:** 10MB per image (increased from 5MB per triplet recommendation)

**Error Handling:**
- **Playfair unreachable:** Render code block with warning comment
- **Diagram generation fails:** Render code block with error message
- **Timeout exceeded:** Render code block with timeout notice
- **Image too large:** Reject diagram, render error in code block

**Fallback Rendering Example:**
```
<!-- WARNING: Playfair diagram generation failed -->
<!-- Error: Connection timeout after 10s -->
<!-- Original diagram specification below: -->

digraph G {
  A -> B;
}
```

### 2.3 Document Styling (Phase 1 - Hard-coded)

**Academic Paper Style:**
- **Fonts:** Liberation Serif (body), Liberation Mono (code)
- **Margins:** 1 inch (2.54cm) all sides
- **Line spacing:** 1.5 for body, 1.0 for code blocks
- **Heading styles:**
  - H1: 18pt, bold, Liberation Serif
  - H2: 16pt, bold
  - H3: 14pt, bold
  - H4-H6: 12pt, bold
- **Body text:** 12pt, Liberation Serif
- **Code blocks:** 10pt, Liberation Mono, light gray background

**Note:** Custom templates deferred to Phase 2. LibreOffice will apply these styles during conversion.

### 2.4 MCP Tools

**Tool 1: gates_create_document**

```json
{
  "name": "gates_create_document",
  "description": "Convert Markdown to ODT document with embedded diagrams",
  "inputSchema": {
    "type": "object",
    "properties": {
      "markdown": {
        "type": "string",
        "description": "Markdown content to convert"
      },
      "metadata": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "author": { "type": "string" },
          "date": { "type": "string" },
          "keywords": { "type": "array", "items": { "type": "string" } }
        }
      },
      "output_path": {
        "type": "string",
        "description": "Optional: file path for output (default: temp file)"
      }
    },
    "required": ["markdown"]
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "odt_file": "/app/output/document_uuid.odt",
  "size_bytes": 245678,
  "metadata": {
    "title": "ICCM Paper",
    "author": "Research Team",
    "page_count": 12,
    "diagram_count": 3,
    "conversion_time_ms": 4523
  },
  "warnings": [
    "Diagram 2 failed to generate, rendered as code block"
  ]
}
```

**Tool 2: gates_validate_markdown**

```json
{
  "name": "gates_validate_markdown",
  "description": "Validate Markdown syntax and check for potential ODT conversion issues",
  "inputSchema": {
    "type": "object",
    "properties": {
      "markdown": { "type": "string" }
    },
    "required": ["markdown"]
  }
}
```

**Response Format:**
```json
{
  "valid": true,
  "warnings": [
    "Line 42: Nested table detected (may render poorly in some ODT readers)",
    "Line 87: Image URL not accessible (will appear as broken link)"
  ],
  "statistics": {
    "heading_count": 8,
    "paragraph_count": 45,
    "code_block_count": 3,
    "table_count": 2,
    "diagram_count": 5,
    "estimated_page_count": 12
  }
}
```

**Tool 3: gates_list_capabilities**

```json
{
  "name": "gates_list_capabilities",
  "description": "List supported Markdown features and current configuration",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Response Format:**
```json
{
  "version": "2.0",
  "markdown_features": [
    "CommonMark", "GFM tables", "Task lists", "Nested lists (4 levels)",
    "Fenced code blocks", "Playfair diagrams (dot, mermaid)"
  ],
  "diagram_formats": ["playfair-dot", "playfair-mermaid"],
  "output_formats": ["odt"],
  "size_limits": {
    "max_markdown_size_mb": 10,
    "max_odt_size_mb": 50,
    "max_image_size_mb": 10
  },
  "playfair_status": "operational",
  "queue_status": {
    "current_depth": 0,
    "max_depth": 10,
    "processing": false
  }
}
```

---

## 3. Technical Architecture

### 3.1 Technology Stack (Phase 1)

**Core Components:**
- **Runtime:** Node.js 22.x
- **Markdown Parser:** markdown-it 14.x
- **markdown-it Plugins:**
  - `markdown-it-multimd-table` - Advanced table support
  - `markdown-it-attrs` - Custom styling hooks
  - `markdown-it-task-lists` - Checkbox support
- **ODT Generation:** LibreOffice headless (via execa wrapper)
- **Process Manager:** execa 8.x (robust child process handling)
- **WebSocket:** ws 8.x (MCP protocol)
- **Request Queue:** p-queue 8.x (FIFO queue implementation)
- **Logging:** pino 8.x
- **Testing:** Jest 29.x, Supertest 6.x

**Container:**
- **Base Image:** node:22-alpine
- **Additional Packages:** libreoffice (via apk)
- **Total Size:** ~400MB (Phase 1), optimized in Phase 2

### 3.2 ODT Generation Architecture (Phase 1)

**Approach:** LibreOffice Headless (Option B - Unanimous Triplet Consensus)

**Rationale:**
- ✅ Guaranteed ODT compliance (ISO/IEC 26300 standard)
- ✅ Handles complex formatting (tables, lists, styles) reliably
- ✅ 20+ year proven rendering engine
- ✅ Fastest time-to-market (4 weeks)
- ✅ Focus on Markdown→Playfair integration, not XML debugging
- ✅ Acceptable 400MB container size for "occasional usage" service

**Implementation:**

```javascript
import { execa } from 'execa';

async function convertToODT(htmlFile, outputPath) {
  try {
    const result = await execa('libreoffice', [
      '--headless',
      '--convert-to', 'odt',
      '--outdir', path.dirname(outputPath),
      htmlFile
    ], {
      timeout: 120000, // 120 seconds
      cleanup: true,
      killSignal: 'SIGTERM',
      env: {
        HOME: '/tmp' // Prevent LibreOffice config conflicts
      }
    });

    return {
      success: true,
      output: result.stdout,
      file: outputPath
    };
  } catch (error) {
    logger.error({ error: error.message }, 'LibreOffice conversion failed');
    throw new Error(`ODT conversion failed: ${error.message}`);
  }
}
```

**Process Management:**
- **Timeout:** 120 seconds per document
- **Cleanup:** Automatic via execa (zombie process prevention)
- **Signal handling:** SIGTERM for graceful shutdown
- **Temp directory isolation:** Prevent config file conflicts

**Conversion Pipeline:**

```
Markdown Input
    ↓
markdown-it Parser (with plugins)
    ↓
Playfair Plugin (async diagram generation)
    ↓
HTML Intermediate Format
    ↓
LibreOffice --headless --convert-to odt
    ↓
ODT Output (ZIP with content.xml, styles.xml, meta.xml)
```

### 3.3 Concurrency Model

**Approach:** FIFO Queue (Playfair Pattern) - Unanimous Triplet Consensus

**Implementation:**
```javascript
import PQueue from 'p-queue';

const conversionQueue = new PQueue({
  concurrency: 1, // Single worker
  timeout: 120000, // 120s per job
  throwOnTimeout: true
});

// Add conversion to queue
async function queueConversion(markdownInput) {
  if (conversionQueue.size >= 10) {
    throw new Error('SERVER_BUSY: Queue full (10 requests)');
  }

  return conversionQueue.add(async () => {
    return await processDocument(markdownInput);
  });
}
```

**Configuration:**
- **Concurrency:** 1 (single worker - prevents LibreOffice resource contention)
- **Queue Depth:** 10 requests maximum
- **Timeout:** 120 seconds per document
- **Behavior:** FIFO (first-in, first-out)

**Rationale (Unanimous Triplet Agreement):**
- LibreOffice is memory/CPU intensive
- "Occasional document generation" usage pattern
- Prevents resource exhaustion and OOM kills
- Simple, predictable behavior
- Matches Playfair's proven pattern

**Error Handling:**
- Queue full (10 deep) → Return `SERVER_BUSY` error
- Timeout exceeded → Kill process, return `TIMEOUT` error
- Process crash → Log error, continue processing queue

### 3.4 Playfair Integration (markdown-it Plugin)

**Custom Plugin Implementation:**

```javascript
import markdownIt from 'markdown-it';
import { playfairMCPClient } from './playfair-client.js';

function playfairPlugin(md) {
  // Store original fence rule
  const defaultFenceRenderer = md.renderer.rules.fence;

  md.renderer.rules.fence = async (tokens, idx, options, env, slf) => {
    const token = tokens[idx];
    const info = token.info.trim();

    // Check for playfair-* fence types
    if (info.startsWith('playfair-')) {
      const format = info.replace('playfair-', ''); // 'dot' or 'mermaid'
      const content = token.content;

      try {
        // Call Playfair MCP with 10s timeout
        const diagram = await playfairMCPClient.createDiagram({
          content,
          format,
          theme: 'modern',
          output_format: 'png',
          width: 1920,
          timeout: 10000
        });

        // Return image tag with base64 PNG
        return `<img src="data:image/png;base64,${diagram.image}" alt="Diagram: ${format}">`;
      } catch (error) {
        logger.warn({ format, error: error.message }, 'Playfair diagram generation failed');

        // Fallback: render as code block with warning
        return `<!-- WARNING: Playfair diagram generation failed -->\n` +
               `<!-- Error: ${error.message} -->\n` +
               `<!-- Original diagram specification: -->\n` +
               `<pre><code class="${info}">${escapeHtml(content)}</code></pre>`;
      }
    }

    // Not a playfair block, use default renderer
    return defaultFenceRenderer(tokens, idx, options, env, slf);
  };
}

export default playfairPlugin;
```

**MCP Client Configuration:**
```javascript
const playfairMCPClient = new MCPClient({
  url: 'ws://localhost:9040', // Playfair WebSocket
  timeout: 10000, // 10 seconds per diagram
  retries: 0 // No retries (fail fast, use fallback)
});
```

### 3.5 WebSocket MCP Server

**Port:** 9050
**Protocol:** MCP (Model Context Protocol) over WebSocket
**Library:** ws 8.x

**Server Implementation:**
```javascript
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 9050 });

wss.on('connection', (ws) => {
  logger.info('MCP client connected');

  ws.on('message', async (data) => {
    try {
      const request = JSON.parse(data.toString());
      const response = await handleMCPRequest(request);
      ws.send(JSON.stringify(response));
    } catch (error) {
      ws.send(JSON.stringify({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: error.message
        },
        id: request.id
      }));
    }
  });
});

async function handleMCPRequest(request) {
  const { method, params, id } = request;

  switch (method) {
    case 'initialize':
      return {
        jsonrpc: '2.0',
        result: {
          name: 'Gates',
          version: '2.0.0',
          capabilities: ['tools'],
          protocol_version: '1.0'
        },
        id
      };

    case 'tools/list':
      return {
        jsonrpc: '2.0',
        result: { tools: listTools() },
        id
      };

    case 'tools/call':
      const result = await callTool(params.name, params.arguments);
      return {
        jsonrpc: '2.0',
        result: {
          content: [{
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }]
        },
        id
      };

    default:
      throw new Error(`Method '${method}' not supported`);
  }
}
```

### 3.6 Container Configuration

**Dockerfile (Phase 1):**

```dockerfile
FROM node:22-alpine

# Install LibreOffice
RUN apk add --no-cache \
    libreoffice \
    libreoffice-writer \
    ttf-liberation

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output && chmod 777 /app/output

# Expose WebSocket port
EXPOSE 9050

# Set environment
ENV NODE_ENV=production
ENV HOME=/tmp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js

# Start server
CMD ["node", "server.js"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  gates:
    build: .
    container_name: gates-mcp
    ports:
      - "9050:9050"
    volumes:
      - gates-output:/app/output
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
      - PLAYFAIR_URL=ws://playfair-mcp:9040
    networks:
      - iccm-network
    restart: unless-stopped
    mem_limit: 1g
    cpus: 2

volumes:
  gates-output:

networks:
  iccm-network:
    external: true
```

**Resource Limits:**
- **Memory:** 1GB (LibreOffice can be memory-intensive)
- **CPU:** 2 cores
- **Container Size:** ~400MB (node:22-alpine + LibreOffice)

---

## 4. Performance Requirements

### 4.1 Response Times (Phase 1 Targets)

**Simple Documents (1-5 pages, no diagrams):**
- Target: < 2 seconds
- Maximum: 5 seconds

**Medium Documents (5-15 pages, 3-5 diagrams):**
- Target: < 10 seconds
- Maximum: 30 seconds

**Complex Documents (15-40 pages, 5-10 diagrams):**
- Target: < 30 seconds
- Maximum: 120 seconds (hard timeout)

**Queue Wait Time:**
- Empty queue: 0 seconds
- Full queue (10 deep): Up to 20 minutes (10 docs × 120s max each)
- Acceptable for "occasional usage" pattern

### 4.2 Resource Usage

**Memory:**
- Baseline (idle): < 100MB
- During conversion: 200-500MB (LibreOffice process)
- Container limit: 1GB

**CPU:**
- Baseline (idle): < 5%
- During conversion: 50-100% of 2 cores
- LibreOffice is CPU-intensive for complex documents

**Disk:**
- Temp files: Auto-cleaned after conversion
- Output files: User responsible for cleanup
- Max temp usage: 100MB per document

### 4.3 Throughput

**Expected Usage:** Occasional document generation (not high-volume API)

**Capacity:**
- Sustained: ~30 documents/hour (2 min average per doc)
- Peak: 10 documents queued + 1 processing
- FIFO ensures predictable behavior

---

## 5. Size Limits and Validation

### 5.1 Input Limits

**Markdown Input:**
- **Maximum size:** 10MB
- **Rationale:** ICCM papers are 40-60KB; 10MB is 250x buffer
- **Validation:** Check size before parsing

**Image URLs/Data URIs:**
- **Maximum per image:** 10MB (increased from 5MB per triplet recommendation)
- **Rationale:** High-res diagrams may reach 8-9MB at 300 DPI
- **Total images:** No hard limit (constrained by total ODT size)

**Playfair Diagrams:**
- **Maximum per document:** 50 diagrams
- **Timeout per diagram:** 10 seconds
- **Rationale:** Prevents runaway diagram generation

### 5.2 Output Limits

**ODT Output:**
- **Maximum size:** 50MB
- **Rationale:** Accounts for base64 overhead + embedded images
- **Validation:** Reject conversion if ODT exceeds limit

**Estimated Size Calculation:**
```javascript
function estimateODTSize(markdown) {
  const markdownSize = markdown.length;
  const imageCount = countImages(markdown);
  const avgImageSize = 500 * 1024; // 500KB average

  // ODT has ~1.5x overhead for XML structure
  const baseSize = markdownSize * 1.5;
  const imageSize = imageCount * avgImageSize;

  return baseSize + imageSize;
}
```

### 5.3 Validation Rules

**Pre-Processing Validation:**
1. Markdown size ≤ 10MB
2. Valid UTF-8 encoding
3. No malicious content (script injection in HTML output)

**During Processing:**
1. Each Playfair diagram ≤ 10MB
2. Diagram timeout ≤ 10 seconds
3. Total conversion time ≤ 120 seconds

**Post-Processing Validation:**
1. ODT output ≤ 50MB
2. Valid ZIP structure (ODT is a ZIP archive)
3. Contains required files: content.xml, styles.xml, meta.xml

---

## 6. Error Handling

### 6.1 Error Categories

**Category 1: Input Validation Errors**
- `MARKDOWN_TOO_LARGE` - Input > 10MB
- `INVALID_ENCODING` - Not valid UTF-8
- `MALFORMED_MARKDOWN` - Parser cannot process

**Category 2: Processing Errors**
- `PLAYFAIR_UNREACHABLE` - Cannot connect to Playfair MCP
- `DIAGRAM_TIMEOUT` - Diagram generation > 10s
- `DIAGRAM_TOO_LARGE` - Diagram image > 10MB
- `CONVERSION_TIMEOUT` - Total time > 120s
- `LIBREOFFICE_FAILED` - LibreOffice process crashed

**Category 3: Output Errors**
- `ODT_TOO_LARGE` - Output > 50MB
- `ODT_INVALID` - Not a valid ODT file
- `DISK_FULL` - Cannot write output file

**Category 4: System Errors**
- `SERVER_BUSY` - Queue full (10 requests)
- `RESOURCE_EXHAUSTED` - Out of memory/CPU

### 6.2 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "PLAYFAIR_UNREACHABLE",
    "message": "Cannot connect to Playfair MCP at ws://localhost:9040",
    "details": {
      "diagram_number": 3,
      "diagram_format": "dot",
      "connection_error": "ECONNREFUSED"
    }
  },
  "partial_result": {
    "diagrams_succeeded": 2,
    "diagrams_failed": 1,
    "fallback_rendered": true
  }
}
```

### 6.3 Graceful Degradation

**Playfair Failures:**
- Continue processing (render code blocks with warnings)
- Log warnings in metadata
- Return successful ODT with fallback content

**LibreOffice Failures:**
- Cannot gracefully degrade (ODT generation is core function)
- Return error to user
- Retry not applicable (unlikely to succeed on retry)

**Resource Exhaustion:**
- Reject new requests (SERVER_BUSY)
- Allow current request to complete
- Clear queue on catastrophic failure

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Coverage Target:** 80%

**Test Suites:**
1. **Markdown Parser Tests**
   - All supported markdown features (headings, lists, tables, code)
   - Edge cases (empty input, malformed syntax)
   - Plugin functionality (Playfair blocks detected correctly)

2. **Playfair Integration Tests**
   - Successful diagram generation
   - Timeout handling (mock slow Playfair)
   - Failure fallback (mock unreachable Playfair)
   - Large diagram rejection (> 10MB)

3. **LibreOffice Wrapper Tests**
   - Successful conversion (mock LibreOffice)
   - Process timeout handling
   - Process crash recovery
   - Temp file cleanup

4. **Queue Tests**
   - FIFO ordering
   - Queue depth limiting (reject at 10)
   - Timeout handling
   - Concurrent request handling

### 7.2 Integration Tests

**Test Documents (Golden Masters):**

Create test suite from actual ICCM papers:
1. `test_simple.md` - 2 pages, no diagrams (baseline)
2. `test_diagrams.md` - 5 pages, 3 Playfair diagrams
3. `test_complex_tables.md` - Nested tables, multi-line cells
4. `test_full_paper.md` - Complete ICCM paper (40-60KB, 5-10 diagrams)

**Validation:**
```bash
# Generate ODT from test markdown
npm run test:integration

# For each test:
1. Convert markdown to ODT
2. Verify ODT is valid ZIP
3. Extract content.xml and validate structure
4. Open in LibreOffice and visual verify (manual)
5. Convert to PDF and compare against reference (automated)
```

**Golden Master Testing:**
- Generate reference ODT files with known-good configuration
- On each test run, compare new ODT against reference
- Flag differences for manual review

### 7.3 Performance Tests

**Load Testing:**
```javascript
// Simulate 10 concurrent requests (fill queue)
test('Queue handles 10 concurrent requests', async () => {
  const requests = Array(10).fill().map((_, i) =>
    createDocument({ markdown: testMarkdown[i] })
  );

  const results = await Promise.allSettled(requests);
  expect(results.every(r => r.status === 'fulfilled')).toBe(true);
});

// Verify 11th request is rejected
test('11th request returns SERVER_BUSY', async () => {
  // Fill queue with 10 requests
  const queueFillers = Array(10).fill().map(() =>
    createDocument({ markdown: largeDocument })
  );

  // 11th request should fail immediately
  await expect(
    createDocument({ markdown: smallDocument })
  ).rejects.toThrow('SERVER_BUSY');
});
```

**Stress Testing:**
- Maximum size document (10MB markdown, 50 diagrams)
- Verify timeout handling (should abort at 120s)
- Verify memory stays within 1GB limit

### 7.4 Fuzz Testing

**Malformed Markdown:**
```javascript
import { faker } from '@faker-js/faker';

test('Parser handles malformed markdown', () => {
  // Generate random strings with markdown-like syntax
  for (let i = 0; i < 1000; i++) {
    const fuzzInput = generateMalformedMarkdown();

    // Should not crash, may return validation error
    expect(() => validateMarkdown(fuzzInput)).not.toThrow();
  }
});
```

**Edge Cases:**
- Deeply nested lists (10+ levels)
- Extremely wide tables (100+ columns)
- Mixed line endings (CRLF, LF, CR)
- Unicode edge cases (emoji, RTL text, zero-width chars)

---

## 8. Documentation Requirements

### 8.1 User Documentation

**README.md** - Include:
1. Quick start guide
2. MCP tool examples (all 3 tools)
3. Playfair diagram syntax examples
4. Supported markdown features (with examples)
5. Size limits and error codes
6. Troubleshooting common issues

**API Reference** - Document:
1. All 3 MCP tools (schemas, examples, responses)
2. Error codes and meanings
3. Metadata fields
4. Configuration options

### 8.2 Developer Documentation

**ARCHITECTURE.md** - Explain:
1. Overall system architecture
2. LibreOffice integration pattern
3. Playfair integration flow
4. Queue implementation
5. Phase 2 migration strategy

**CONTRIBUTING.md** - Guide:
1. Development setup
2. Running tests
3. Adding new markdown features
4. Adding new diagram types (Phase 2)
5. Code style and linting

### 8.3 Deployment Documentation

**DEPLOYMENT.md** - Cover:
1. Docker container build and run
2. docker-compose configuration
3. MCP relay integration
4. Monitoring and logging
5. Resource limits and tuning
6. Health checks

---

## 9. Open Questions (RESOLVED - Triplet Consensus)

### ~~Question 1: ODT Generation Approach~~

**RESOLVED:** ✅ **Option B - LibreOffice headless** (Unanimous Round 2 consensus)

**Rationale:**
- Guaranteed ODT compliance (zero risk of non-standard files)
- Fastest time-to-market (4 weeks)
- Allows focus on Markdown→Playfair integration
- 400MB container acceptable for "occasional usage"
- Phase 2 migration path to native XML addresses long-term optimization

**Dissenting Arguments Acknowledged:**
- DeepSeek's 400MB dependency concern → Addressed in Phase 2 via "Strangler Fig" migration
- GPT-4o-mini's edge case concern → LibreOffice handles all edge cases natively, no fallback needed

---

### ~~Question 2: Markdown Parser Selection~~

**RESOLVED:** ✅ **Option A - markdown-it** (Unanimous Round 1 consensus)

**Rationale:**
- Full CommonMark + GFM support for academic papers
- Plugin architecture perfect for Playfair integration
- Active community (14k stars)
- Comprehensive table/code block handling

**Plugins Selected:**
- `markdown-it-multimd-table` - Advanced tables
- `markdown-it-attrs` - Custom styling hooks
- `markdown-it-task-lists` - Checkbox support

---

### ~~Question 3: Concurrent Request Handling~~

**RESOLVED:** ✅ **Option A - FIFO queue** (Unanimous Round 1 consensus)

**Rationale:**
- Matches "occasional document generation" usage pattern
- Prevents resource exhaustion (LibreOffice is memory-intensive)
- Simple, predictable behavior
- Consistency with Playfair architecture
- Can evolve to worker pool in Phase 2 if needed

**Configuration:**
- Single worker (concurrency: 1)
- Queue depth: 10 requests
- Timeout: 120 seconds per document

---

### ~~Question 4: Diagram Embedding Format~~

**RESOLVED:** ✅ **Option A - PNG only** (Unanimous Round 1 consensus)

**Rationale:**
- Universal ODT viewer compatibility (LibreOffice, MS Word, OpenOffice)
- Predictable rendering across platforms (pixel-perfect)
- SVG support is "notoriously inconsistent" in office suites
- Academic papers require reliable diagram reproduction
- Phase 1 simplification (SVG deferred to Phase 2)

**Configuration:**
- Format: PNG at 300 DPI
- Size limit: 10MB per image
- Encoding: Base64 data URI or binary embedding

---

### ~~Question 5: Document Size Limits~~

**RESOLVED:** ✅ **Approve with adjustment** (Triplet consensus with DeepSeek recommendation)

**Final Limits:**
- Input Markdown: 10MB ✅ (250x buffer vs 40-60KB papers)
- Output ODT: 50MB ✅ (accounts for base64 + container overhead)
- Embedded Images: **10MB per image** (increased from 5MB)

**Rationale for 10MB Image Limit:**
- High-res diagrams may reach 8-9MB at 300 DPI
- Provides safety margin for complex architecture diagrams
- Still protects against runaway resource usage
- Memory headroom exists (200MB/request vs 1GB container)

---

## 10. Phase 2 Migration Path (Strangler Fig Pattern)

### 10.1 Overview

**Goal:** Incrementally replace LibreOffice with native XML generation to reduce container size and improve performance

**Pattern:** "Strangler Fig" - Build new system around old, gradually migrate traffic, eventually remove old system

**Trigger Criteria:**
- >95% of documents are "simple" (no nested tables, ≤2 level lists)
- Container costs become prohibitive
- Performance bottlenecks identified in production

### 10.2 Phase 1.5: Instrumentation (Post-Launch)

**Data Collection:**
```javascript
// Log every document generation
logger.info({
  documentId: uuid,
  complexity: {
    hasNestedTables: boolean,
    maxListDepth: number,
    maxTableDepth: number,
    hasComplexStyles: boolean,
    tableCount: number,
    imageCount: number,
    codeBlockCount: number
  },
  performance: {
    conversionTime: ms,
    libreOfficeMemory: bytes,
    libreOfficeCPU: percent
  }
});
```

**Metrics Dashboard:**
- Document complexity distribution (simple vs complex)
- LibreOffice resource usage trends
- Queue depth over time
- Error rate by category

**Review Cadence:** Monthly for first 3 months, then quarterly

### 10.3 Phase 2: Native XML Generator

**Week 1-2: Foundation**
- Implement XML generator for paragraphs and headings only
- Create routing logic: simple → native, complex → LibreOffice
- Deploy alongside existing LibreOffice path

**Week 3-6: Expansion**
- Add support for: lists, bold/italic, code blocks
- Target 40% coverage (route 40% of requests to native generator)

**Week 7-12: Complex Features**
- Add simple tables (no nesting), images (PNG embedding)
- Target 80% coverage

**Week 13+: Maturity**
- Add complex tables, nested lists
- Target 95%+ coverage (LibreOffice becomes 5% fallback)
- Optional: Remove LibreOffice if 100% coverage achieved

**Routing Logic:**
```javascript
async function routeConversion(markdown, parsed) {
  const complexity = analyzeComplexity(parsed);

  if (shouldUseNativeGenerator(complexity)) {
    logger.info({ complexity }, 'Routing to native XML generator');
    return await nativeXMLGenerator.convert(parsed);
  } else {
    logger.info({ complexity }, 'Routing to LibreOffice (complex document)');
    return await libreOfficeConverter.convert(markdown);
  }
}

function shouldUseNativeGenerator(complexity) {
  return !complexity.hasNestedTables
      && complexity.maxListDepth <= 2
      && !complexity.hasComplexStyles
      && complexity.tableCount <= 3;
}
```

### 10.4 Container Size Optimization Roadmap

| Phase | Approach | Container Size | Description |
|-------|----------|---------------|-------------|
| **Phase 1** | LibreOffice only | ~400MB | node:22 + full LibreOffice |
| **Phase 1.5** | Alpine optimization | ~260MB | node:22-alpine + minimal LibreOffice package (-35%) |
| **Phase 2A** | Native (40% traffic) | ~400MB | Both generators, 60% LibreOffice |
| **Phase 2B** | Native (80% traffic) | ~150MB | Conditional LibreOffice load (only when needed) |
| **Phase 2C** | Native (95% traffic) | ~100MB | LibreOffice rarely loaded |
| **Phase 3** | Native (100% traffic) | ~50MB | Pure Node.js + JSZip, LibreOffice removed |

### 10.5 Success Metrics

**Phase 2 is successful when:**
- ✅ 95%+ of documents routed to native generator
- ✅ Container size reduced by 50%+ (400MB → <200MB)
- ✅ Zero increase in ODT compliance errors
- ✅ Conversion time maintained or improved
- ✅ Memory usage reduced by 30%+

---

## 11. Security Considerations

### 11.1 Input Validation

**Markdown Sanitization:**
- Prevent script injection in HTML output
- Escape special characters in XML
- Validate image data URIs (no `javascript:` or `data:text/html`)

**Size Limits Enforcement:**
- Reject oversized inputs before processing
- Prevent resource exhaustion attacks

### 11.2 Process Isolation

**LibreOffice Sandboxing:**
- Run with minimal privileges
- Isolated temp directory per conversion
- No network access from LibreOffice process

**Container Security:**
- Read-only filesystem (except /tmp and /app/output)
- No root privileges
- Resource limits enforced (memory, CPU)

### 11.3 Dependency Security

**Npm Audit:**
- Run `npm audit` before each deployment
- No high/critical vulnerabilities in production
- Regular dependency updates

**Image Scanning:**
- Scan Docker image for CVEs
- Use official node:22-alpine base
- Keep Alpine packages updated

---

## 12. Deployment and Operations

### 12.1 Container Deployment

**Build:**
```bash
cd /mnt/projects/ICCM/gates
docker build -t gates-mcp:2.0 .
```

**Run:**
```bash
docker-compose up -d gates
```

**Verify:**
```bash
# Check logs
docker logs -f gates-mcp

# Test health endpoint
curl http://localhost:9050/health

# Test MCP connection
wscat -c ws://localhost:9050
```

### 12.2 Monitoring

**Metrics to Track:**
- Request rate (documents/hour)
- Queue depth over time
- Conversion time (p50, p95, p99)
- Error rate by category
- LibreOffice memory usage
- Container CPU usage

**Alerting:**
- Queue depth > 8 for >5 minutes (approaching saturation)
- Error rate > 10% over 15 minutes
- Memory usage > 900MB (approaching 1GB limit)
- Conversion time p95 > 90 seconds (approaching 120s timeout)

### 12.3 Logging

**Log Levels:**
- `ERROR`: Conversion failures, system errors
- `WARN`: Playfair failures (with fallback), timeouts
- `INFO`: Successful conversions, queue activity
- `DEBUG`: Detailed processing steps (disabled in production)

**Log Format (JSON):**
```json
{
  "timestamp": "2025-10-04T22:45:00.000Z",
  "level": "info",
  "message": "Document conversion completed",
  "documentId": "uuid",
  "duration": 4523,
  "markdownSize": 45678,
  "odtSize": 234567,
  "diagramCount": 3,
  "warnings": []
}
```

### 12.4 Backup and Recovery

**Output Files:**
- User responsible for archiving generated ODT files
- Gates does not persist output beyond temp directory
- Recommend: Copy to external storage after generation

**Configuration:**
- docker-compose.yml version controlled in git
- Environment variables documented in README.md
- No persistent state in container (stateless service)

---

## 13. Success Criteria (Phase 1 MVP)

**The Phase 1 MVP is successful when:**

✅ **Functional Requirements:**
- All 3 MCP tools operational (create, validate, capabilities)
- Converts ICCM papers (40-60KB) to valid ODT in <30 seconds
- Embeds Playfair diagrams as PNG images
- Handles Playfair failures gracefully (fallback to code blocks)

✅ **Performance Requirements:**
- Simple documents (1-5 pages): <5 seconds
- Medium documents (5-15 pages, 3-5 diagrams): <30 seconds
- Complex documents (15-40 pages, 5-10 diagrams): <120 seconds
- Queue handles 10 concurrent requests

✅ **Quality Requirements:**
- Generated ODT files open correctly in LibreOffice, MS Word, OpenOffice
- Academic paper styling applied consistently
- No crashes or OOM kills during testing
- Test suite passes with 80%+ coverage

✅ **Operational Requirements:**
- Container builds and runs successfully
- Integrated with MCP Relay on port 9050
- Health check passes
- Logs structured and queryable
- Documentation complete (README, API, ARCHITECTURE)

---

## 14. Timeline (Phase 1 MVP)

**Total Duration:** 4 weeks (Unanimous triplet consensus)

**Week 1: Foundation**
- Scaffold Node.js project
- Setup Docker with LibreOffice
- Implement WebSocket MCP server
- Basic gates_create_document tool (Markdown → HTML → ODT)

**Week 2: Playfair Integration**
- Develop markdown-it plugin for Playfair blocks
- Implement MCP client to call Playfair
- Error handling and fallback logic (code block rendering)
- Ensure all supported Markdown features render correctly

**Week 3: Tooling & Styling**
- Implement gates_validate_markdown tool
- Implement gates_list_capabilities tool
- Refine academic paper styling
- Comprehensive error handling for all failure modes

**Week 4: Testing & Documentation**
- Write unit and integration tests
- Golden master testing with ICCM papers
- Performance testing (load, stress, fuzz)
- Complete documentation (README, API, ARCHITECTURE, DEPLOYMENT)
- Bug fixing and final polish

**Deployment:** End of Week 4

---

## 15. Appendix

### 15.1 References

**OpenDocument Format:**
- ODF Specification 1.3: https://docs.oasis-open.org/office/OpenDocument/v1.3/
- LibreOffice Documentation: https://documentation.libreoffice.org/

**Markdown:**
- CommonMark Specification: https://spec.commonmark.org/
- GitHub Flavored Markdown: https://github.github.com/gfm/

**MCP Protocol:**
- Model Context Protocol: (ICCM internal documentation)

**ICCM Architecture:**
- General Architecture.PNG: /mnt/projects/ICCM/architecture/
- CURRENT_ARCHITECTURE_OVERVIEW.md: /mnt/projects/ICCM/architecture/

### 15.2 Triplet Review History

**Round 1 (2025-10-04 22:42 EDT):**
- Consultation ID: fbdfca05
- Models: gpt-4o-mini, gemini-2.5-pro, deepseek-ai/DeepSeek-R1
- Duration: 53.53 seconds
- Results: 4/5 unanimous, split on ODT generation approach

**Round 2 (2025-10-04 22:49 EDT):**
- Consultation ID: 6c89c11d
- Models: gpt-4o-mini, gemini-2.5-pro, deepseek-ai/DeepSeek-R1
- Duration: 44.84 seconds
- Results: ✅ **UNANIMOUS CONSENSUS** - All 3 models selected Option B (LibreOffice headless)

**Synthesis Document:** /mnt/projects/ICCM/gates/TRIPLET_REVIEW_SYNTHESIS.md

### 15.3 Related Documentation

- `/mnt/projects/ICCM/CURRENT_STATUS.md` - Current session status
- `/mnt/projects/ICCM/BUG_TRACKING.md` - Bug tracking and resolutions
- `/mnt/projects/ICCM/architecture/TRIPLET_CONSULTATION_PROCESS.md` - Standard triplet consultation process
- `/mnt/projects/ICCM/playfair/README.md` - Playfair diagram gateway documentation
- `/mnt/projects/ICCM/fiedler/README.md` - Fiedler LLM orchestra documentation

---

**Document Version:** 2.0
**Last Updated:** 2025-10-04 23:00 EDT
**Status:** ✅ APPROVED - Ready for Implementation
**Next Step:** Begin Phase 1 implementation (Week 1: Foundation)
