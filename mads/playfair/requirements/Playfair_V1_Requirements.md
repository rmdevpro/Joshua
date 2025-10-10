# Playfair V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Playfair is The Chart Master - creates diagrams, charts, and visualizations. V1 adds an Imperator for conversational diagram creation.

**Named after:** William Playfair, inventor of statistical graphics.

---

## Current Capabilities

- Graphviz diagrams (DOT format)
- Mermaid diagrams
- Various chart types (flowcharts, orgcharts, architecture diagrams, etc.)

---

## What V1 Adds

### 1. Imperator
- LLM brain for Playfair
- Understands diagram requests conversationally
- Uses LLM Client Library (ImperatorClient)

### 2. Conversation Capability
- New MCP tool: `playfair_converse`
- Ask for diagram/chart creation in natural language

### 3. Example Usage
```
User: "Playfair, create a flowchart showing the MAD architecture"
User: "Playfair, make a bar chart of our LLM usage by provider"
User: "Playfair, draw an org chart for the MAD ecosystem"
User: "Playfair, create a sequence diagram showing Rogers message flow"
```

---

## Success Criteria

- ✅ Can create diagrams from conversational requests
- ✅ Chooses appropriate diagram type for request
- ✅ Existing Playfair tools still work

---

*Requirements v1.0 - Playfair as conversational diagram assistant*

---

## Conversation History

### V1 Pattern Discussion

**User:** [In response to "Should Playfair V1 be similar pattern - Imperator for diagrams?"] yes

**Assistant:** Created requirements for conversational diagram creation. Examples: "Playfair, create a flowchart showing the MAD architecture" or "Playfair, make a bar chart of our LLM usage"

*Conversation captured: 2025-10-09*
