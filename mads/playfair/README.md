# Playfair - Diagram Generation Gateway

**Version:** 1.0
**Status:** Requirements Complete - Ready for Implementation
**Component Type:** WebSocket MCP Server
**Port:** 9040 (host) / 8040 (container)

---

## Overview

Playfair is the ICCM Diagram Generation Gateway that transforms LLM diagram descriptions into professional, presentation-quality visual diagrams. While LLMs excel at generating text, they struggle with creating beautiful diagrams. Playfair bridges this gap by accepting structured diagram specifications and rendering them with modern aesthetics using proven open-source engines.

**Problem Solved:**
- LLMs can only output text-based diagram formats (Mermaid, Graphviz DOT)
- Default rendering produces mediocre visual quality
- Users need professional diagrams for business presentations and technical documentation

**Solution:**
- Battle-tested rendering engines (Graphviz, Mermaid)
- Modern visual themes via SVG post-processing
- Multiple output formats (SVG, PNG, PDF)
- WebSocket MCP protocol for seamless LLM integration

---

## Quick Start

### Prerequisites
- Docker & docker-compose
- ICCM network (`iccm_network`)
- MCP Relay configured

### Launch Playfair

```bash
cd /mnt/projects/ICCM/playfair
docker-compose up -d
```

### Check Health

```bash
curl http://localhost:9040/health
# Expected: {"status":"healthy","engines":["graphviz","mermaid"],"queue_depth":0}
```

### Use from LLM (via MCP Relay)

```javascript
// Available tools:
playfair_create_diagram({
  content: "digraph { A -> B -> C; }",
  format: "dot",
  output_format: "svg",
  theme: "modern"
})

playfair_list_capabilities()
playfair_get_examples({diagram_type: "flowchart", format: "dot"})
playfair_validate_syntax({content: "...", format: "mermaid"})
```

---

## Supported Diagram Types

### All 8 Core Types Covered

1. **Flowcharts** - Process flows, decision trees
   - Engines: Graphviz (DOT), Mermaid
2. **Organizational Charts** - Hierarchies, reporting structures
   - Engine: Graphviz (DOT)
3. **Architecture Diagrams** - System components, services
   - Engine: Graphviz (DOT)
4. **Sequence Diagrams** - Interactions, message flows
   - Engine: Mermaid
5. **Network Diagrams** - Topology, infrastructure
   - Engine: Graphviz (DOT)
6. **Mind Maps** - Concept relationships
   - Engines: Graphviz (twopi), Mermaid
7. **ER Diagrams** - Database schema
   - Engine: Mermaid
8. **State Diagrams** - State machines
   - Engine: Mermaid

---

## Rendering Engines

### Graphviz (EPL-1.0)
- **Strengths:** Professional graph layouts, hierarchies, networks
- **Syntax:** DOT language
- **Themes:** Professional, modern, minimal, dark
- **Examples:** Flowcharts, org charts, architecture diagrams

### Mermaid (MIT)
- **Strengths:** UML-style diagrams, concise syntax
- **Syntax:** Mermaid markup
- **Themes:** Built-in (forest, dark, neutral) + custom CSS
- **Examples:** Sequence diagrams, ER diagrams, state machines

---

## Themes

### Professional
- Clean corporate look
- Blue/gray color palette
- Rounded corners
- Sans-serif fonts (Inter)

### Modern
- Vibrant gradients
- Bold colors
- Drop shadows
- Contemporary fonts (Roboto)

### Minimal
- Monochrome
- Thin lines
- Maximum clarity
- Simple shapes

### Dark
- Dark background
- High contrast
- Tech aesthetic
- Monospace fonts

---

## Output Formats

### SVG (Default)
- Vector scalable
- Web-friendly
- Editable
- Base64-encoded for immediate use

### PNG (Phase 1)
- High resolution (1920px @ 2x DPI)
- Presentation-ready
- PowerPoint/Google Slides compatible
- Base64-encoded

### PDF (Phase 2)
- Print-quality
- Vector-based
- Document embedding

---

## Example Usage

### Create a Flowchart (Graphviz)

```javascript
await playfair_create_diagram({
  content: `
    digraph flowchart {
      rankdir=TB;

      start [label="Start", shape=circle];
      process [label="Process Data"];
      decision [label="Valid?", shape=diamond];
      success [label="Success"];
      error [label="Error"];
      end [label="End", shape=circle];

      start -> process;
      process -> decision;
      decision -> success [label="Yes"];
      decision -> error [label="No"];
      success -> end;
      error -> end;
    }
  `,
  format: "dot",
  output_format: "svg",
  theme: "modern",
  title: "User Authentication Flow"
})
```

### Create a Sequence Diagram (Mermaid)

```javascript
await playfair_create_diagram({
  content: `
    sequenceDiagram
      participant User
      participant API
      participant Database

      User->>API: POST /login
      API->>Database: Query user
      Database-->>API: User data
      API-->>User: Auth token
  `,
  format: "mermaid",
  output_format: "png",
  theme: "dark"
})
```

### Auto-Detect Format

```javascript
await playfair_create_diagram({
  content: "digraph { A -> B; }",  // Detected as DOT
  format: "auto",
  output_format: "svg",
  theme: "professional"
})
```

---

## Architecture Integration

```
┌────────────────────────────────────────┐
│  LLM (via Fiedler)                     │
│  - Generates diagram specifications    │
│  - Calls playfair_create_diagram       │
└────────────┬───────────────────────────┘
             │
             │ MCP WebSocket
             ↓
┌────────────────────────────────────────┐
│  MCP Relay                              │
│  - Routes to Playfair backend           │
│  - ws://localhost:9040                  │
└────────────┬───────────────────────────┘
             │
             │ WebSocket
             ↓
┌────────────────────────────────────────┐
│  Playfair Container                     │
│  ┌──────────────────────────────────┐  │
│  │ Worker Pool (2-3 workers)        │  │
│  │ - Graphviz renderer              │  │
│  │ - Mermaid renderer               │  │
│  │ - SVG post-processor             │  │
│  │ - Theme engine                   │  │
│  └──────────────────────────────────┘  │
└────────────┬───────────────────────────┘
             │
             ↓
    SVG/PNG Diagram (base64)
```

**Optional Integration:**
- KGB → Logging of diagram requests
- Dewey → Storage of generated diagrams
- Winni → Persistent database

---

## Performance

**Rendering Speed:**
- Simple diagrams (<20 elements): <2 seconds
- Medium diagrams (20-100 elements): <5 seconds
- Complex diagrams (100-500 elements): <15 seconds
- Timeout: 60 seconds maximum

**Concurrency:**
- Worker pool: 2-3 parallel workers
- Priority queue: Small diagrams jump ahead
- Resource limits: 2GB memory, 2 CPU cores

**Input Limits:**
- Max diagram size: 10,000 lines
- Max output dimensions: 10,000 x 10,000 pixels
- Max complexity: 1000 nodes, 2000 edges

---

## Configuration

### Environment Variables

```yaml
NODE_ENV: production
PORT: 8040
LOG_LEVEL: info
WORKER_POOL_SIZE: 3
MAX_QUEUE_SIZE: 50
```

### MCP Relay Integration

Add to `/mnt/projects/ICCM/mcp-relay/backends.yaml`:

```yaml
backends:
  - name: playfair
    url: ws://localhost:9040
```

---

## Development Roadmap

### ✅ Phase 1: Core Functionality (1-2 weeks)
- WebSocket MCP server
- Graphviz + Mermaid integration
- All 8 diagram types
- SVG + PNG output
- Modern theming via post-processing
- Worker pool (2-3 workers)
- Structured error responses
- Health check endpoint

### Phase 2: Enhanced Features (1-2 weeks)
- PDF output format
- Additional themes (hand-drawn, blueprint)
- Diagram storage in Dewey
- Diagram retrieval by ID
- Performance optimization
- Comprehensive test suite

### Phase 3: Natural Language (1-2 weeks)
- Integration with Fiedler for NLP parsing
- Natural language → diagram conversion
- Confidence scoring
- Iterative refinement

---

## License Compliance

**All Components - 100% Permissive:**

| Component   | License    | Type       |
|-------------|------------|------------|
| Graphviz    | EPL-1.0    | Permissive |
| Mermaid     | MIT        | Permissive |
| ws          | MIT        | Permissive |
| sharp       | Apache-2.0 | Permissive |
| svgo        | MIT        | Permissive |
| svg2pdf     | MIT        | Permissive |

✅ **No copyleft dependencies**
✅ **Commercial use allowed**
✅ **Redistribution allowed**

---

## Troubleshooting

### Container won't start
```bash
docker logs playfair-mcp
# Check for missing dependencies or port conflicts
```

### Rendering timeout
- Simplify diagram (reduce nodes/edges)
- Check complexity limits
- Verify worker pool not exhausted

### Invalid syntax errors
```bash
# Use validation tool first
playfair_validate_syntax({
  content: "your diagram here",
  format: "dot"
})
```

### Theme not applied
- Verify theme name (professional, modern, minimal, dark)
- Check SVG post-processing logs
- Ensure web fonts are embedded

---

## Support & Documentation

- **Requirements:** `/mnt/projects/ICCM/playfair/REQUIREMENTS.md`
- **Examples:** `/mnt/projects/ICCM/playfair/examples/`
- **Architecture:** `/mnt/projects/ICCM/architecture/General Architecture.PNG`
- **MCP Protocol:** MCP Specification 2024-11-05

---

## Credits

**Development:** Triplet-driven (Gemini 2.5 Pro, GPT-4o-mini, DeepSeek-R1)
**Rendering Engines:** Graphviz, Mermaid
**Protocol:** Model Context Protocol (MCP)
**Part of:** ICCM (Integrated Cognitive Capabilities Module)

---

**Status:** ✅ Requirements approved by unanimous triplet consensus
**Next Step:** Phase 1 implementation
