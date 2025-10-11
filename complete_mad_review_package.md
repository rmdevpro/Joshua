# MAD Connection Failures - Diagnostic Package

## Problem Statement
Three MADs are failing to connect to MCP Relay:
- **Playfair** (port 9040) - Connection refused
- **Gates** (port 9050) - Connection refused
- **Sergey** (172.29.0.13:8095) - Connection refused

## Diagnostic Findings

### 1. Playfair (Port 9040) - NOT RUNNING

**Relay Configuration:**
- Expected: `ws://localhost:9040`
- Status: Connection refused [Errno 111]

**Container Status:**
```
NO CONTAINER RUNNING
```

**Docker Compose Configuration:**
- File: `/mnt/projects/Joshua/mads/playfair/docker-compose.yml`
- Container: `playfair-mcp-blue`
- Port mapping: `9041:8040` (HOST:CONTAINER)
- Status: Not started

**Issue:** Blue/green deployment - BLUE container configured for port 9041, but relay expects 9040

---

### 2. Gates (Port 9050) - WRONG PORT

**Relay Configuration:**
- Expected: `ws://localhost:9050`
- Status: Connection refused [Errno 111]

**Container Status:**
```
gates-mcp-blue    Up 5 days (healthy)    0.0.0.0:9051->8050/tcp
gates-mcp         Exited (137) 8 hours ago
```

**Docker Compose Configuration:**
- File: `/mnt/projects/Joshua/mads/gates/docker-compose.yml`
- Container: `gates-mcp-blue`
- Port mapping: `9051:8050` (HOST:CONTAINER)
- Status: Healthy, running on 9051

**Issues:**
1. Blue/green deployment - BLUE container on port 9051, relay expects 9050
2. Dead container `gates-mcp` needs cleanup (exited 8 hours ago)

---

### 3. Sergey (172.29.0.13:8095) - WRONG IP

**Relay Configuration:**
- Expected: `ws://172.29.0.13:8095`
- Status: Connection refused [Errno 113]

**Container Status:**
```
sergey-mcp    Up 5 hours (healthy)    0.0.0.0:8095->8095/tcp
```

**Docker Compose Configuration:**
- File: `/mnt/projects/Joshua/mads/sergey/docker-compose.yml`
- Container: `sergey-mcp`
- Port mapping: `8095:8095` (HOST:CONTAINER)
- Network: `iccm_network` (external)
- Status: Healthy, running

**Issue:** Relay has hardcoded IP 172.29.0.13:8095, but container IP in iccm_network is different. Should use `ws://sergey-mcp:8095` (DNS name) or `ws://localhost:8095` (host port).

---

## Root Cause Analysis

**Pattern Identified:** Blue/Green Deployment Port Mismatches

All three MADs have deployment configuration issues:

1. **Blue/Green Strategy Not Coordinated with Relay**
   - Playfair: BLUE on 9041, relay expects 9040
   - Gates: BLUE on 9051, relay expects 9050
   - Pattern suggests GREEN should be on original ports (9040, 9050)

2. **Network Configuration Inconsistency**
   - Sergey: Relay using static IP instead of DNS or localhost
   - Should use container DNS names within Docker network
   - Or use host-side localhost with mapped ports

3. **Container Cleanup Not Performed**
   - Old `gates-mcp` container (exited) still exists
   - Indicates checkpoint cleanup process not followed

---

## Code Files for Review

### Playfair (Node.js)
**Main files:**
- `/mnt/projects/Joshua/mads/playfair/server.js`
- `/mnt/projects/Joshua/mads/playfair/mcp-tools.js`
- `/mnt/projects/Joshua/mads/playfair/workers/worker-pool.js`
- `/mnt/projects/Joshua/mads/playfair/engines/mermaid.js`
- `/mnt/projects/Joshua/mads/playfair/engines/graphviz.js`
- `/mnt/projects/Joshua/mads/playfair/utils/logger.js`
- `/mnt/projects/Joshua/mads/playfair/playfair/godot/mcp_logger.py`
- `/mnt/projects/Joshua/mads/playfair/Dockerfile`
- `/mnt/projects/Joshua/mads/playfair/docker-compose.yml`

**Technology:** Node.js 22, Puppeteer, Mermaid CLI, Graphviz
**Logging:** Custom logger.js + Python mcp_logger (not migrated to joshua_logger)

### Gates (Node.js)
**Main files:**
- `/mnt/projects/Joshua/mads/gates/server.js`
- `/mnt/projects/Joshua/mads/gates/loglib.js`
- `/mnt/projects/Joshua/mads/gates/Dockerfile`
- `/mnt/projects/Joshua/mads/gates/docker-compose.yml`

**Technology:** Node.js, WebSocket MCP server
**Logging:** Custom loglib.js (not migrated to joshua-libs)

### Sergey (Python)
**Main files:**
- `/mnt/projects/Joshua/mads/sergey/sergey_server.py` (ALREADY MIGRATED to joshua_logger)
- `/mnt/projects/Joshua/mads/sergey/Dockerfile`
- `/mnt/projects/Joshua/mads/sergey/docker-compose.yml`

**Technology:** Python, WebSocket MCP server
**Logging:** ✅ Migrated to joshua_logger (5/7 MADs complete)
**Status:** Code is correct, only relay configuration issue

---

## MCP Relay Configuration

**Current Relay Config Issues:**

```
Playfair: ws://localhost:9040  ❌ (should be 9041 for BLUE or start GREEN on 9040)
Gates: ws://localhost:9050     ❌ (should be 9051 for BLUE or start GREEN on 9050)
Sergey: ws://172.29.0.13:8095  ❌ (should be ws://localhost:8095 or ws://sergey-mcp:8095)
```

**Working MAD Examples:**
```
Dewey: ws://localhost:9022     ✅
Godot: ws://localhost:9060     ✅
Horace: ws://localhost:9070    ✅
Marco: ws://localhost:9031     ✅
Fiedler: ws://localhost:9010   ✅
```

---

## Joshua Libraries (for reference)

### joshua_network (Python)
**Location:** `/mnt/projects/Joshua/lib/joshua_network/`
**Files:**
- `server.py` - WebSocket MCP server base class
- `client.py` - WebSocket MCP client
- `exceptions.py` - Error handling
- `__init__.py` - Package exports

**Usage:** Python MADs use `joshua_network.Server` for MCP protocol

### joshua_logger (Python)
**Location:** `/mnt/projects/Joshua/lib/joshua_logger/`
**Files:**
- `logger.py` - Centralized logging via Godot MCP
- `__init__.py` - Package exports

**Usage:** All Python MADs log via `joshua_logger.Logger(component="name")`

### joshua_network_js (DOES NOT EXIST YET)
**Status:** NOT IMPLEMENTED
**Need:** Node.js equivalent of joshua_network for Playfair, Gates, Marco
**See:** GitHub Issue #16 - Polo v1: Rebuild Marco with joshua_network_js

---

## Migration Status

**Python MADs (joshua-libs):**
- ✅ Dewey - Migrated
- ✅ Fiedler - Migrated
- ✅ Horace - Migrated
- ✅ Godot - Migrated
- ✅ Sergey - Migrated

**Node.js MADs (custom):**
- ❌ Marco - Custom MCP + custom logger
- ❌ Playfair - Custom MCP + custom logger
- ❌ Gates - Custom MCP + custom logger

**Recommendation:** Migrate Node.js MADs to joshua_network_js (when created) OR fix relay config + start containers correctly

---

## Questions for Triplet Analysis

1. **Immediate Fix Strategy:**
   - Should we update relay config to match BLUE ports (9041, 9051)?
   - Or deploy GREEN containers on original ports (9040, 9050)?
   - Or switch all to localhost with correct port mappings?

2. **Sergey Network Fix:**
   - Use `ws://localhost:8095` (host network)?
   - Or `ws://sergey-mcp:8095` (container DNS)?
   - Why was static IP 172.29.0.13 used initially?

3. **Playfair Deployment:**
   - Why is playfair-mcp-blue not running?
   - Should we start it or create GREEN deployment?

4. **Container Cleanup:**
   - Process for identifying and removing dead containers?
   - How to prevent accumulation?

5. **Long-term Strategy:**
   - Migrate all Node.js MADs to joshua_network_js?
   - Or maintain custom MCP implementations?
   - Standardize deployment strategy (always use localhost + port mapping)?

---

## Expected Deliverable from Triplet

Please provide:

1. **Root cause analysis** - Why are these specific connection failures happening?
2. **Immediate fixes** - Commands/config changes to restore connectivity
3. **Deployment strategy** - Should we standardize on:
   - localhost + port mapping (ws://localhost:PORT)
   - Container DNS names (ws://container-name:PORT)
   - Static IPs (current broken approach)
4. **Code fixes** - Any changes needed to MAD implementations
5. **Relay config updates** - Correct URL patterns for each MAD
6. **Container management** - How to handle blue/green, cleanup, etc.

**Goal:** All 8 MADs healthy and connected to relay with standardized, maintainable configuration.
# MAD Code Package - Complete Source for Triplet Review

Generated: Fri Oct 10 10:40:25 PM EDT 2025

## PLAYFAIR (Node.js MCP Server)

### File: /mnt/projects/Joshua/mads/playfair/server.js
```
const http = require('http');
const { WebSocketServer } = require('ws');
const { WebSocket: WebSocketClient } = require('ws');
const { v4: uuidv4 } = require('uuid');
const logger = require('./utils/logger');
const McpTools = require('./mcp-tools');

const PORT = process.env.PORT || 8040;
const GODOT_URL = process.env.GODOT_URL || 'ws://godot-mcp:9060';
const LOGGING_ENABLED = true;

/**
 * Send log to Godot via MCP logger_log tool
 */
async function logToGodot(level, message, data = null, traceId = null) {
  if (!LOGGING_ENABLED) return;

  try {
    const ws = new WebSocketClient(GODOT_URL, { handshakeTimeout: 1000 });

    await new Promise((resolve, reject) => {
      ws.on('open', () => resolve());
      ws.on('error', reject);
      setTimeout(() => reject(new Error('Connection timeout')), 1000);
    });

    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: 'logger_log',
        arguments: {
          level,
          message,
          component: 'playfair',
          data,
          trace_id: traceId
        }
      },
      id: 1
    };

    ws.send(JSON.stringify(request));

    // Wait for response or timeout
    await Promise.race([
      new Promise(resolve => ws.on('message', resolve)),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Response timeout')), 1000))
    ]);

    ws.close();
  } catch (err) {
    // Silently fail - logging should never break the application
    logger.debug(`Godot logging failed: ${err.message}`);
  }
}

// --- Main Application Setup ---

const server = http.createServer();
const wss = new WebSocketServer({ noServer: true });

const mcpTools = new McpTools();

// --- WebSocket Connection Handling ---

wss.on('connection', (ws, request) => {
    const clientId = uuidv4();
    ws.clientId = clientId;
    logger.info({ clientId, ip: request.socket.remoteAddress }, 'Client connected');
    logToGodot('INFO', 'Client connected', { client_id: clientId, ip: request.socket.remoteAddress });

    ws.on('message', async (message) => {
        let request;
        try {
            request = JSON.parse(message);
            logger.debug({ clientId, request }, 'Received request');
            logToGodot('TRACE', 'MCP request received', { client_id: clientId, method: request.method, id: request.id });
        } catch (error) {
            logger.error({ clientId, error: error.message }, 'Invalid JSON message received');
            logToGodot('ERROR', 'Invalid JSON message received', { client_id: clientId, error: error.message });
            ws.send(JSON.stringify({ error: true, code: 'INVALID_JSON', message: 'Message must be valid JSON.' }));
            return;
        }

        const response = await handleClientRequest(request, clientId);

        try {
            ws.send(JSON.stringify(response));
            logger.debug({ clientId, response }, 'Sent response');
            logToGodot('TRACE', 'MCP response sent', { client_id: clientId, method: request.method, id: request.id });
        } catch (error) {
            logger.error({ clientId, error: error.message }, 'Failed to send response');
            logToGodot('ERROR', 'Failed to send response', { client_id: clientId, error: error.message });
        }
    });

    ws.on('close', () => {
        logger.info({ clientId }, 'Client disconnected');
    });

    ws.on('error', (error) => {
        logger.error({ clientId, error: error.message }, 'WebSocket error');
    });
});

// --- MCP Protocol Handler ---

async function handleClientRequest(request, clientId) {
    const { method, params, id } = request;

    switch (method) {
        case 'initialize':
            return {
                jsonrpc: '2.0',
                result: {
                    protocolVersion: '2024-11-05',
                    serverInfo: {
                        name: 'playfair',
                        version: '1.0.0'
                    },
                    capabilities: {
                        tools: {}
                    }
                },
                id
            };

        case 'tools/list':
            return {
                jsonrpc: '2.0',
                result: {
                    tools: mcpTools.listTools()
                },
                id
            };

        case 'tools/call':
            if (!params || !params.name) {
                return {
                    jsonrpc: '2.0',
                    error: {
                        code: -32602,
                        message: 'Missing tool name in params.'
                    },
                    id
                };
            }

            logToGodot('TRACE', 'Tool call started', { client_id: clientId, tool_name: params.name, has_args: !!params.arguments });
            const toolResult = await mcpTools.callTool(params.name, params.arguments, clientId);
            logToGodot('TRACE', 'Tool call completed', { client_id: clientId, tool_name: params.name, success: !toolResult.error });

            // Wrap tool result in MCP protocol format
            return {
                jsonrpc: '2.0',
                result: {
                    content: [{
                        type: 'text',
                        text: JSON.stringify(toolResult, null, 2)
                    }]
                },
                id
            };

        default:
            return {
                jsonrpc: '2.0',
                error: {
                    code: -32601,
                    message: `Method '${method}' is not supported.`
                },
                id
            };
    }
}

// --- HTTP Server for Health Checks ---

server.on('request', (req, res) => {
    if (req.url === '/health') {
        const healthStatus = mcpTools.getHealthStatus();
        if (healthStatus.status === 'healthy') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(healthStatus));
        } else {
            res.writeHead(503, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(healthStatus));
        }
    } else {
        // For non-WebSocket requests, respond with an error
        res.writeHead(426); // Upgrade Required
        res.end('This is a WebSocket server. Please connect using a WebSocket client.');
    }
});


// --- Server Startup ---

server.on('upgrade', (request, socket, head) => {
    // Handle WebSocket upgrade requests
    wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
    });
});

server.listen(PORT, () => {
    logger.info(`Playfair MCP Server listening on ws://localhost:${PORT}`);
    logger.info(`Health check available at http://localhost:${PORT}/health`);
});

process.on('SIGTERM', () => {
    logger.info('SIGTERM signal received. Shutting down gracefully.');
    server.close(() => {
        logger.info('HTTP server closed.');
        process.exit(0);
    });
});```

### File: /mnt/projects/Joshua/mads/playfair/mcp-tools.js
```
const fs = require('fs/promises');
const path = require('path');
const logger = require('./utils/logger');
const WorkerPool = require('./workers/worker-pool');
const Validator = require('./utils/validator');
const formatDetector = require('./utils/format-detector');

const EXAMPLES_DIR = path.join(__dirname, 'examples');

class McpTools {
    constructor() {
        this.workerPool = new WorkerPool();
        this.validator = new Validator();
        this.tools = [
            {
                name: 'playfair_create_diagram',
                description: 'Create a professional diagram from Graphviz DOT or Mermaid specification.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        content: { type: 'string', description: 'Diagram specification (DOT or Mermaid syntax).' },
                        format: { type: 'string', enum: ['dot', 'mermaid', 'auto'], default: 'auto', description: 'Input format.' },
                        output_format: { type: 'string', enum: ['svg', 'png'], default: 'svg', description: 'Output image format.' },
                        theme: { type: 'string', enum: ['professional', 'modern', 'minimal', 'dark'], default: 'modern', description: 'Visual theme.' },
                        width: { type: 'integer', default: 1920, description: 'Output width in pixels for PNG.' },
                        height: { type: 'integer', description: 'Output height in pixels (auto if not specified).' },
                        output_path: { type: 'string', description: 'Optional: file path for output. If not specified, returns base64 data.' },
                    },
                    required: ['content'],
                },
            },
            {
                name: 'playfair_list_capabilities',
                description: 'List all supported diagram formats, themes, and capabilities.',
                inputSchema: { type: 'object', properties: {} },
            },
            {
                name: 'playfair_get_examples',
                description: 'Get example syntax for a specific diagram type.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        diagram_type: { type: 'string', enum: ['flowchart', 'orgchart', 'architecture', 'sequence', 'network', 'mindmap', 'er', 'state'] },
                    },
                    required: ['diagram_type'],
                },
            },
            {
                name: 'playfair_validate_syntax',
                description: 'Validate diagram syntax without rendering.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        content: { type: 'string', description: 'Diagram specification to validate.' },
                        format: { type: 'string', enum: ['dot', 'mermaid', 'auto'], default: 'auto' },
                    },
                    required: ['content'],
                },
            },
        ];
    }

    listTools() {
        return this.tools;
    }

    async callTool(name, input, clientId) {
        logger.info({ clientId, tool: name, input: { ...input, content: '...' } }, 'Tool call initiated');
        try {
            switch (name) {
                case 'playfair_create_diagram':
                    return await this.createDiagram(input);
                case 'playfair_list_capabilities':
                    return this.listCapabilities();
                case 'playfair_get_examples':
                    return await this.getExamples(input);
                case 'playfair_validate_syntax':
                    return await this.validateSyntax(input);
                default:
                    return { error: true, code: 'TOOL_NOT_FOUND', message: `Tool '${name}' not found.` };
            }
        } catch (error) {
            logger.error({ clientId, tool: name, error: error.message, stack: error.stack }, 'Tool call failed');
            return {
                error: true,
                code: error.code || 'INTERNAL_ERROR',
                message: error.message || 'An unexpected error occurred.',
            };
        }
    }

    async createDiagram(input) {
        const { content, format: specifiedFormat = 'auto', width, height, output_path, ...options } = input;

        if (!content) {
            return { error: true, code: 'MISSING_CONTENT', message: 'Input "content" is required.' };
        }

        // Resource limit: Enforce maximum PNG dimensions to prevent DoS
        const MAX_PNG_WIDTH = parseInt(process.env.MAX_PNG_WIDTH, 10) || 8192;
        const MAX_PNG_HEIGHT = parseInt(process.env.MAX_PNG_HEIGHT, 10) || 8192;

        if (width && width > MAX_PNG_WIDTH) {
            return { error: true, code: 'INVALID_DIMENSION', message: `Width exceeds maximum allowed (${MAX_PNG_WIDTH}px).` };
        }
        if (height && height > MAX_PNG_HEIGHT) {
            return { error: true, code: 'INVALID_DIMENSION', message: `Height exceeds maximum allowed (${MAX_PNG_HEIGHT}px).` };
        }
        if (width && width < 1) {
            return { error: true, code: 'INVALID_DIMENSION', message: 'Width must be a positive integer.' };
        }
        if (height && height < 1) {
            return { error: true, code: 'INVALID_DIMENSION', message: 'Height must be a positive integer.' };
        }

        const format = specifiedFormat === 'auto' ? formatDetector.detect(content) : specifiedFormat;
        if (!format) {
            return { error: true, code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format. Please specify "dot" or "mermaid".' };
        }

        const job = { format, content, options: { ...options, width, height } };
        const result = await this.workerPool.submit(job);

        // Result contains { data: Buffer, error: null } or { data: null, error: {...} }
        if (result.error) {
            return result.error;
        }

        // If output_path is specified, save to file instead of returning base64
        if (output_path) {
            try {
                await fs.writeFile(output_path, result.data);
                logger.info({ output_path, size: result.data.length }, 'Diagram saved to file');
                return {
                    result: {
                        format: options.output_format || 'svg',
                        output_path: output_path,
                        size: result.data.length,
                    },
                };
            } catch (error) {
                logger.error({ output_path, error: error.message }, 'Failed to write diagram to file');
                return { error: true, code: 'FILE_WRITE_ERROR', message: `Failed to write file: ${error.message}` };
            }
        }

        // Default: return base64 data
        return {
            result: {
                format: options.output_format || 'svg',
                encoding: 'base64',
                data: result.data.toString('base64'),
            },
        };
    }

    listCapabilities() {
        return {
            result: {
                engines: ['graphviz', 'mermaid'],
                input_formats: ['dot', 'mermaid'],
                output_formats: ['svg', 'png'],
                themes: ['professional', 'modern', 'minimal', 'dark'],
                diagram_types: {
                    graphviz: ['flowchart', 'orgchart', 'architecture', 'network', 'mindmap'],
                    mermaid: ['sequence', 'er', 'state', 'flowchart', 'mindmap'],
                },
            },
        };
    }

    async getExamples(input) {
        const { diagram_type } = input;
        const exampleMap = {
            flowchart: 'flowchart.dot',
            orgchart: 'orgchart.dot',
            architecture: 'architecture.dot',
            network: 'network.dot',
            mindmap: 'mindmap.dot',
            sequence: 'sequence.mmd',
            er: 'er.mmd',
            state: 'state.mmd',
        };
        const filename = exampleMap[diagram_type];
        if (!filename) {
            return { error: true, code: 'INVALID_DIAGRAM_TYPE', message: `Unknown diagram_type: ${diagram_type}` };
        }

        try {
            const content = await fs.readFile(path.join(EXAMPLES_DIR, filename), 'utf-8');
            return { result: { diagram_type, content } };
        } catch (error) {
            logger.error({ diagram_type, error: error.message }, 'Failed to read example file');
            return { error: true, code: 'EXAMPLE_NOT_FOUND', message: 'Could not load example file.' };
        }
    }

    async validateSyntax(input) {
        const { content, format: specifiedFormat = 'auto' } = input;
        if (!content) {
            return { error: true, code: 'MISSING_CONTENT', message: 'Input "content" is required.' };
        }

        const format = specifiedFormat === 'auto' ? formatDetector.detect(content) : specifiedFormat;
        if (!format) {
            return { error: true, code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format.' };
        }

        const result = await this.validator.validate(content, format);
        return { result };
    }
    
    getHealthStatus() {
        return {
            status: 'healthy',
            engines: ['graphviz', 'mermaid'],
            ...this.workerPool.getStatus(),
        };
    }
}

module.exports = McpTools;```

### File: /mnt/projects/Joshua/mads/playfair/Dockerfile
```
# Phase 1: Build Environment
# Use official Node.js 22 image on Debian Bookworm for build stability
FROM node:22-bookworm-slim as builder

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package.json ./
# Use npm install (package-lock.json not yet generated)
RUN npm install --omit=dev

# Copy application code
COPY *.js ./playfair/
COPY utils/ ./playfair/utils/
COPY config/ ./playfair/config/
COPY themes/ ./playfair/themes/
COPY engines/ ./playfair/engines/
COPY examples/ ./playfair/examples/
COPY workers/ ./playfair/workers/

# Phase 2: Production Environment
# Use Ubuntu 24.04 as requested for the final image
FROM ubuntu:24.04

# Set non-interactive frontend to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for Playfair
# - graphviz: For DOT rendering
# - fonts-inter, fonts-roboto: For modern theming
# - curl: For health checks
# - ca-certificates: For secure connections if needed later
# - libcairo2: Required by graphviz for high-quality rendering
# - nodejs & npm: For running the application
# - Chromium dependencies: For Mermaid CLI rendering via Puppeteer
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    fonts-inter \
    fonts-roboto \
    curl \
    ca-certificates \
    libcairo2 \
    nodejs \
    npm \
    libgbm1 \
    libasound2t64 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgtk-3-0 \
    libpango-1.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Mermaid CLI globally using the installed npm
# This ensures it's available in the PATH for the application
RUN npm install -g @mermaid-js/mermaid-cli@11

# Create a non-root user for security (before installing chrome-headless-shell)
RUN useradd --system --create-home --shell /bin/false appuser

# Switch to appuser to install chrome-headless-shell in their home directory
USER appuser

# Install chrome-headless-shell for Mermaid rendering
# License: BSD-3-Clause (Chromium) - ICCM compliant, no proprietary codecs used for diagram rendering
# Triplet consensus: DeepSeek-R1, Gemini 2.5 Pro, GPT-4o-mini all approved this approach
RUN npx -y @puppeteer/browsers install chrome-headless-shell@latest --path /home/appuser/.cache/puppeteer

# Create symlink to stable path (version-agnostic) for PUPPETEER_EXECUTABLE_PATH
RUN ln -s $(find /home/appuser/.cache/puppeteer -name chrome-headless-shell -type f) /home/appuser/chrome-headless-shell

# Set Puppeteer to use the symlinked chrome-headless-shell
ENV PUPPETEER_EXECUTABLE_PATH=/home/appuser/chrome-headless-shell

# Configure Puppeteer to run with --no-sandbox in Docker container
# This is safe in containerized environments where isolation is provided by Docker
ENV PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox"

# Switch back to root for remaining setup
USER root

# Create app directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Switch to non-root user before copying files
USER appuser

# Copy built dependencies and application code from the builder stage with correct ownership
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/playfair ./playfair
COPY --chown=appuser:appuser package.json .

# Expose the application port (container-side)
EXPOSE 8040

# Health check to ensure the service is running correctly
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8040/health || exit 1

# Command to run the application
CMD ["node", "playfair/server.js"]```

### File: /mnt/projects/Joshua/mads/playfair/docker-compose.yml
```
services:
  playfair-mcp-blue:
    container_name: playfair-mcp-blue
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      # Map host port 9041 to container port 8040 for MCP and health checks
      - "9041:8040"
    networks:
      # Connect to the external ICCM network
      - iccm_network
    environment:
      # Application Configuration
      - NODE_ENV=production
      - PORT=8040
      - LOG_LEVEL=info
      # Godot Logging Integration
      - GODOT_URL=ws://godot-mcp:9060
      # Worker Pool Configuration
      - WORKER_POOL_SIZE=3
      - MAX_QUEUE_SIZE=50
      # Resource Limits
      - RENDER_TIMEOUT_MS=60000
      - MAX_CONTENT_LINES=10000
      - MAX_PNG_WIDTH=8192
      - MAX_PNG_HEIGHT=8192
    deploy:
      # Enforce resource limits at the container level
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
    restart: unless-stopped
    user: "1000:1000"  # Run as host user (aristotle9) for file write permissions
    volumes:
      # Persist temporary files if needed for debugging, though the app should clean up
      - playfair-temp-blue:/tmp/playfair
      # Read-write access to host filesystem for saving diagrams
      - /mnt/projects:/host/mnt/projects

networks:
  iccm_network:
    # This configuration assumes the 'iccm_network' is created by another compose file or manually.
    external: true

volumes:
  playfair-temp-blue:
    # Define the named volume for temporary data
```

### File: /mnt/projects/Joshua/mads/playfair/package.json
```
{
  "name": "playfair",
  "version": "1.0.0",
  "description": "ICCM Diagram Generation Gateway",
  "main": "playfair/server.js",
  "scripts": {
    "start": "node playfair/server.js",
    "dev": "LOG_LEVEL=debug nodemon playfair/server.js"
  },
  "author": "ICCM",
  "license": "UNLICENSED",
  "private": true,
  "dependencies": {
    "sharp": "^0.33.4",
    "svgo": "^3.3.2",
    "ws": "^8.17.0"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}```

## GATES (Node.js MCP Server)

### File: /mnt/projects/Joshua/mads/gates/server.js
```
#!/usr/bin/env node

/**
 * Gates Document Generation Gateway
 * WebSocket MCP Server - Markdown to ODT Conversion
 * Version: 1.0.0
 */

import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import markdownIt from 'markdown-it';
import markdownItMultimdTable from 'markdown-it-multimd-table';
import markdownItAttrs from 'markdown-it-attrs';
import markdownItTaskLists from 'markdown-it-task-lists';
import { execa } from 'execa';
import PQueue from 'p-queue';
import pino from 'pino';
import { writeFile, readFile, unlink, mkdir } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';
import { randomUUID } from 'crypto';
import { existsSync } from 'fs';
import { WebSocket as WebSocketClient } from 'ws';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info'
});

// Godot logging configuration (via MCP tool, not direct Redis)
const GODOT_URL = process.env.GODOT_URL || 'ws://godot-mcp:9060';
const LOGGING_ENABLED = true;

/**
 * Send log to Godot via MCP logger_log tool
 */
async function logToGodot(level, message, data = null, traceId = null) {
  if (!LOGGING_ENABLED) return;

  try {
    const ws = new WebSocketClient(GODOT_URL, { handshakeTimeout: 1000 });

    await new Promise((resolve, reject) => {
      ws.on('open', () => resolve());
      ws.on('error', reject);
      setTimeout(() => reject(new Error('Connection timeout')), 1000);
    });

    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: 'logger_log',
        arguments: {
          level,
          message,
          component: 'gates',
          data,
          trace_id: traceId
        }
      },
      id: 1
    };

    ws.send(JSON.stringify(request));

    // Wait for response or timeout
    await Promise.race([
      new Promise(resolve => ws.on('message', resolve)),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Response timeout')), 1000))
    ]);

    ws.close();
  } catch (err) {
    // Silently fail - logging should never break the application
    logger.debug(`Godot logging failed: ${err.message}`);
  }
}

// Configuration
const PORT = process.env.GATES_PORT || 8050;
const HOST = process.env.GATES_HOST || '0.0.0.0';
const PLAYFAIR_URL = process.env.PLAYFAIR_URL || 'ws://playfair-mcp:8040';
const MAX_QUEUE_DEPTH = 10;
const CONVERSION_TIMEOUT = 120000; // 120 seconds
const DIAGRAM_TIMEOUT = 10000; // 10 seconds
const MAX_MARKDOWN_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_ODT_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

// Conversion queue (FIFO, single worker)
const conversionQueue = new PQueue({
  concurrency: 1,
  timeout: CONVERSION_TIMEOUT,
  throwOnTimeout: true
});

// Playfair connection state
let playfairClient = null;
let playfairConnected = false;
let playfairReconnectTimer = null;

// Tool definitions
const TOOLS = [
  {
    name: 'gates_create_document',
    description: 'Convert Markdown to ODT document with embedded diagrams',
    inputSchema: {
      type: 'object',
      properties: {
        markdown: {
          type: 'string',
          description: 'Markdown content to convert'
        },
        metadata: {
          type: 'object',
          properties: {
            title: { type: 'string' },
            author: { type: 'string' },
            date: { type: 'string' },
            keywords: { type: 'array', items: { type: 'string' } }
          }
        },
        output_path: {
          type: 'string',
          description: 'Optional: file path for output (default: temp file)'
        }
      },
      required: ['markdown']
    }
  },
  {
    name: 'gates_validate_markdown',
    description: 'Validate Markdown syntax and check for potential ODT conversion issues',
    inputSchema: {
      type: 'object',
      properties: {
        markdown: { type: 'string' }
      },
      required: ['markdown']
    }
  },
  {
    name: 'gates_list_capabilities',
    description: 'List supported Markdown features and current configuration',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
];

/**
 * Connect to Playfair MCP server
 */
async function connectPlayfair() {
  return new Promise((resolve) => {
    try {
      playfairClient = new WebSocketClient(PLAYFAIR_URL);

      playfairClient.on('open', () => {
        logger.info('Connected to Playfair MCP server');
        playfairConnected = true;
        resolve(true);
      });

      playfairClient.on('error', (error) => {
        logger.warn({ error: error.message }, 'Playfair connection error');
        playfairConnected = false;
        schedulePlayfairReconnect();
        resolve(false);
      });

      playfairClient.on('close', () => {
        logger.info('Playfair connection closed');
        playfairConnected = false;
        schedulePlayfairReconnect();
      });
    } catch (error) {
      logger.warn({ error: error.message }, 'Failed to connect to Playfair');
      playfairConnected = false;
      resolve(false);
    }
  });
}

/**
 * Schedule Playfair reconnection
 */
function schedulePlayfairReconnect() {
  if (playfairReconnectTimer) return;

  playfairReconnectTimer = setTimeout(async () => {
    playfairReconnectTimer = null;
    logger.info('Attempting to reconnect to Playfair...');
    await connectPlayfair();
  }, 5000);
}

/**
 * Call Playfair MCP tool
 */
async function callPlayfair(toolName, args) {
  if (!playfairConnected || !playfairClient) {
    throw new Error('Playfair not connected');
  }

  return new Promise((resolve, reject) => {
    const requestId = randomUUID();
    const timeout = setTimeout(() => {
      reject(new Error('Playfair request timeout'));
    }, DIAGRAM_TIMEOUT);

    const messageHandler = (data) => {
      try {
        const response = JSON.parse(data.toString());
        if (response.id === requestId) {
          clearTimeout(timeout);
          playfairClient.off('message', messageHandler);

          if (response.error) {
            reject(new Error(response.error.message || 'Playfair error'));
          } else {
            resolve(response.result);
          }
        }
      } catch (error) {
        // Ignore parse errors for other messages
      }
    };

    playfairClient.on('message', messageHandler);

    const request = {
      jsonrpc: '2.0',
      id: requestId,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    };

    playfairClient.send(JSON.stringify(request));
  });
}

/**
 * Create Playfair plugin for markdown-it
 */
function createPlayfairPlugin() {
  return (md) => {
    const defaultFenceRenderer = md.renderer.rules.fence || function(tokens, idx, options, env, slf) {
      return slf.renderToken(tokens, idx, options);
    };

    md.renderer.rules.fence = function(tokens, idx, options, env, slf) {
      const token = tokens[idx];
      const info = token.info.trim();

      // Check for playfair-* fence types
      if (info.startsWith('playfair-')) {
        const format = info.replace('playfair-', '');
        const content = token.content;

        // Store for async processing
        const placeholderId = `PLAYFAIR_${randomUUID()}`;
        env.playfairDiagrams = env.playfairDiagrams || [];
        env.playfairDiagrams.push({
          id: placeholderId,
          format,
          content
        });

        // Return placeholder
        return `<img id="${placeholderId}" alt="Playfair diagram" />`;
      }

      return defaultFenceRenderer(tokens, idx, options, env, slf);
    };
  };
}

/**
 * Process Playfair diagrams in HTML
 */
async function processPlayfairDiagrams(html, diagrams) {
  if (!diagrams || diagrams.length === 0) {
    return { html, warnings: [] };
  }

  const warnings = [];
  let processedHtml = html;

  for (const diagram of diagrams) {
    try {
      const result = await callPlayfair('playfair_create_diagram', {
        content: diagram.content,
        format: diagram.format,
        output_format: 'png',
        theme: 'professional'
      });

      // Extract base64 image from result - Option B (Triplet Consensus)
      const imageData = result?.content?.[0]?.text;
      let base64Data = null;

      if (imageData) {
        try {
          const jsonData = JSON.parse(imageData);
          // Primary correct path based on actual Playfair response
          base64Data = jsonData?.result?.data;

          if (!base64Data) {
            // Log when parsing succeeds but the key is missing
            logger.warn({ playfairResponse: jsonData, diagramId: diagram.id }, 'Playfair response parsed successfully but is missing "result.data" key');
          }
        } catch (e) {
          logger.error({ error: e.message, rawResponse: imageData, diagramId: diagram.id }, 'Failed to parse JSON from Playfair response');
        }
      } else {
        logger.warn({ playfairResponse: result, diagramId: diagram.id }, 'Invalid Playfair response structure: content[0].text is missing');
      }

      if (base64Data) {
        // Replace placeholder with actual image
        const imgTag = `<img src="data:image/png;base64,${base64Data}" alt="Diagram" />`;
        processedHtml = processedHtml.replace(
          `<img id="${diagram.id}" alt="Playfair diagram" />`,
          imgTag
        );
      } else {
        // Fallback: Render original diagram source as code block
        logger.warn({ diagramId: diagram.id }, 'Rendering fallback diagram due to missing base64 data');

        const fallback = `<pre><code><!-- WARNING: Playfair diagram generation failed -->
<!-- Diagram specification below: -->

${diagram.content}</code></pre>`;

        processedHtml = processedHtml.replace(
          `<img id="${diagram.id}" alt="Playfair diagram" />`,
          fallback
        );

        warnings.push(`Diagram ${diagram.id} failed to generate: No base64 data`);
      }
    } catch (error) {
      logger.error({ error: error.message, diagram: diagram.id }, 'Playfair diagram generation failed');

      // Replace with fallback code block
      const fallback = `<pre><code><!-- WARNING: Playfair diagram generation failed -->
<!-- Error: ${error.message} -->
<!-- Original diagram specification below: -->

${diagram.content}</code></pre>`;

      processedHtml = processedHtml.replace(
        `<img id="${diagram.id}" alt="Playfair diagram" />`,
        fallback
      );

      warnings.push(`Diagram failed to generate: ${error.message}`);
    }
  }

  return { html: processedHtml, warnings };
}

/**
 * Convert Markdown to HTML
 */
async function markdownToHTML(markdown) {
  const md = markdownIt({
    html: true,
    linkify: true,
    typographer: true
  })
    .use(markdownItMultimdTable, {
      multiline: true,
      rowspan: true,
      headerless: true
    })
    .use(markdownItAttrs)
    .use(markdownItTaskLists)
    .use(createPlayfairPlugin());

  const env = {};
  const html = md.render(markdown, env);

  // Process Playfair diagrams
  const { html: processedHtml, warnings } = await processPlayfairDiagrams(html, env.playfairDiagrams);

  return { html: processedHtml, warnings };
}

/**
 * Convert HTML to ODT using LibreOffice
 */
async function htmlToODT(html, outputPath, metadata = {}) {
  const workDir = join(tmpdir(), `gates-${randomUUID()}`);
  await mkdir(workDir, { recursive: true });

  try {
    // Create HTML file with metadata
    const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${metadata.title || 'Document'}</title>
  <meta name="author" content="${metadata.author || ''}" />
  <meta name="date" content="${metadata.date || new Date().toISOString()}" />
  <style>
    body {
      font-family: 'Liberation Serif', serif;
      font-size: 12pt;
      line-height: 1.5;
      margin: 2.54cm;
    }
    h1 { font-size: 18pt; font-weight: bold; }
    h2 { font-size: 16pt; font-weight: bold; }
    h3 { font-size: 14pt; font-weight: bold; }
    h4, h5, h6 { font-size: 12pt; font-weight: bold; }
    code, pre {
      font-family: 'Liberation Mono', monospace;
      font-size: 10pt;
      background-color: #f5f5f5;
      padding: 0.2em;
    }
    pre {
      padding: 1em;
      line-height: 1.0;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 1em 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
      font-weight: bold;
    }
  </style>
</head>
<body>
${html}
</body>
</html>`;

    const htmlPath = join(workDir, 'input.html');
    await writeFile(htmlPath, htmlContent, 'utf-8');

    // Convert to ODT using LibreOffice
    logger.info({ workDir }, 'Converting HTML to ODT with LibreOffice');

    const result = await execa('libreoffice', [
      '--headless',
      '--convert-to', 'odt',
      '--outdir', workDir,
      htmlPath
    ], {
      timeout: CONVERSION_TIMEOUT,
      cleanup: true,
      killSignal: 'SIGTERM',
      env: {
        HOME: workDir // Prevent LibreOffice config conflicts
      }
    });

    logger.info({ stdout: result.stdout }, 'LibreOffice conversion completed');

    // Move ODT to output path
    const generatedODT = join(workDir, 'input.odt');
    if (!existsSync(generatedODT)) {
      throw new Error('LibreOffice did not generate ODT file');
    }

    // Read and write to final location
    const odtContent = await readFile(generatedODT);
    await writeFile(outputPath, odtContent);

    logger.info({ outputPath, size: odtContent.length }, 'ODT file created successfully');

    return {
      success: true,
      size: odtContent.length
    };
  } finally {
    // Cleanup temp directory
    try {
      await unlink(join(workDir, 'input.html')).catch(() => {});
      await unlink(join(workDir, 'input.odt')).catch(() => {});
    } catch (error) {
      logger.warn({ error: error.message }, 'Failed to cleanup temp files');
    }
  }
}

/**
 * Main document creation function
 */
async function createDocument(args) {
  const { markdown, metadata = {}, output_path } = args;

  // Validate markdown size
  if (markdown.length > MAX_MARKDOWN_SIZE) {
    throw new Error(`Markdown exceeds maximum size of ${MAX_MARKDOWN_SIZE / 1024 / 1024}MB`);
  }

  const startTime = Date.now();

  // Generate output path
  const outputPath = output_path || join('/tmp', `document-${randomUUID()}.odt`);

  // Convert Markdown to HTML
  const { html, warnings } = await markdownToHTML(markdown);

  // Convert HTML to ODT
  const { size } = await htmlToODT(html, outputPath, metadata);

  if (size > MAX_ODT_SIZE) {
    await unlink(outputPath);
    throw new Error(`Generated ODT exceeds maximum size of ${MAX_ODT_SIZE / 1024 / 1024}MB`);
  }

  const conversionTime = Date.now() - startTime;

  return {
    success: true,
    odt_file: outputPath,
    size_bytes: size,
    metadata: {
      title: metadata.title || 'Document',
      author: metadata.author || '',
      conversion_time_ms: conversionTime
    },
    warnings
  };
}

/**
 * Validate Markdown
 */
async function validateMarkdown(args) {
  const { markdown } = args;

  const warnings = [];
  const statistics = {
    heading_count: 0,
    paragraph_count: 0,
    code_block_count: 0,
    table_count: 0,
    diagram_count: 0,
    estimated_page_count: 0
  };

  // Parse with markdown-it
  const md = markdownIt();
  const env = {};
  const tokens = md.parse(markdown, env);

  // Analyze tokens
  for (const token of tokens) {
    if (token.type === 'heading_open') {
      statistics.heading_count++;
    } else if (token.type === 'paragraph_open') {
      statistics.paragraph_count++;
    } else if (token.type === 'fence') {
      if (token.info.startsWith('playfair-')) {
        statistics.diagram_count++;
      } else {
        statistics.code_block_count++;
      }
    } else if (token.type === 'table_open') {
      statistics.table_count++;
    }
  }

  // Estimate page count (rough: 500 words per page)
  const wordCount = markdown.split(/\s+/).length;
  statistics.estimated_page_count = Math.ceil(wordCount / 500);

  return {
    valid: true,
    warnings,
    statistics
  };
}

/**
 * List capabilities
 */
async function listCapabilities() {
  return {
    version: '1.0',
    markdown_features: [
      'CommonMark',
      'GFM tables',
      'Task lists',
      'Nested lists (4 levels)',
      'Fenced code blocks',
      'Playfair diagrams (dot, mermaid)'
    ],
    diagram_formats: ['playfair-dot', 'playfair-mermaid'],
    output_formats: ['odt'],
    size_limits: {
      max_markdown_size_mb: MAX_MARKDOWN_SIZE / 1024 / 1024,
      max_odt_size_mb: MAX_ODT_SIZE / 1024 / 1024,
      max_image_size_mb: MAX_IMAGE_SIZE / 1024 / 1024
    },
    playfair_status: playfairConnected ? 'operational' : 'unavailable',
    queue_status: {
      current_depth: conversionQueue.size,
      max_depth: MAX_QUEUE_DEPTH,
      processing: conversionQueue.pending > 0
    }
  };
}

/**
 * Handle tool calls
 */
async function handleToolCall(toolName, args) {
  const traceId = randomUUID();
  logger.info({ toolName, args }, 'Handling tool call');

  // Log to Godot for debugging
  logToGodot('TRACE', 'Tool call received', {
    tool_name: toolName,
    arguments: args,
    queue_size: conversionQueue.size
  }, traceId);

  try {
    let result;
    switch (toolName) {
      case 'gates_create_document':
        if (conversionQueue.size >= MAX_QUEUE_DEPTH) {
          logToGodot('WARN', 'Queue full - rejecting request', { queue_size: conversionQueue.size }, traceId);
          throw new Error('SERVER_BUSY: Queue full (10 requests)');
        }
        logToGodot('TRACE', 'Adding document creation to queue', {}, traceId);
        result = await conversionQueue.add(() => createDocument(args));
        break;

      case 'gates_validate_markdown':
        logToGodot('TRACE', 'Validating markdown', {}, traceId);
        result = await validateMarkdown(args);
        break;

      case 'gates_list_capabilities':
        logToGodot('TRACE', 'Listing capabilities', {}, traceId);
        result = await listCapabilities();
        break;

      default:
        logToGodot('ERROR', 'Unknown tool requested', { tool_name: toolName }, traceId);
        throw new Error(`Unknown tool: ${toolName}`);
    }

    logToGodot('TRACE', 'Tool call completed successfully', {
      tool_name: toolName,
      result_size: JSON.stringify(result).length
    }, traceId);

    return result;
  } catch (error) {
    logToGodot('ERROR', 'Tool call failed', {
      tool_name: toolName,
      error: error.message,
      error_type: error.name
    }, traceId);
    throw error;
  }
}

/**
 * Handle MCP request
 */
async function handleMCPRequest(request) {
  const { id, method, params } = request;
  const traceId = randomUUID();

  logToGodot('TRACE', 'MCP request received', {
    method,
    params,
    request_id: id
  }, traceId);

  try {
    let response;
    switch (method) {
      case 'initialize':
        logToGodot('TRACE', 'Handling initialize request', {}, traceId);
        response = {
          jsonrpc: '2.0',
          id,
          result: {
            protocolVersion: '2024-11-05',
            capabilities: {
              tools: {}
            },
            serverInfo: {
              name: 'gates-mcp-server',
              version: '1.0.0'
            }
          }
        };
        break;

      case 'tools/list':
        logger.info({ tools: TOOLS }, 'Returning tools list');
        logToGodot('TRACE', 'Handling tools/list request', { tool_count: TOOLS.length }, traceId);
        response = {
          jsonrpc: '2.0',
          id,
          result: {
            tools: TOOLS
          }
        };
        break;

      case 'tools/call':
        logToGodot('TRACE', 'Handling tools/call request', {
          tool_name: params.name,
          has_arguments: !!params['arguments']
        }, traceId);
        const result = await handleToolCall(params.name, params['arguments'] || {});
        response = {
          jsonrpc: '2.0',
          id,
          result: {
            content: [{
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }]
          }
        };
        break;

      default:
        logToGodot('ERROR', 'Unknown MCP method', { method }, traceId);
        throw new Error(`Unknown method: ${method}`);
    }

    logToGodot('TRACE', 'MCP request completed', {
      method,
      response_size: JSON.stringify(response).length,
      has_error: !!response.error
    }, traceId);

    return response;
  } catch (error) {
    logger.error({ error: error.message, request }, 'MCP request failed');
    logToGodot('ERROR', 'MCP request failed', {
      method,
      error: error.message,
      error_type: error.name
    }, traceId);

    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32603,
        message: error.message
      }
    };
  }
}

/**
 * Start WebSocket MCP server
 */
async function startServer() {
  // Connect to Playfair
  await connectPlayfair();

  // Create HTTP server for health checks
  const httpServer = createServer((req, res) => {
    if (req.url === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'healthy',
        playfair: playfairConnected ? 'connected' : 'disconnected',
        queue_depth: conversionQueue.size,
        queue_processing: conversionQueue.pending > 0
      }));
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  // Create WebSocket server
  const wss = new WebSocketServer({ server: httpServer });

  wss.on('connection', (ws) => {
    logger.info('Client connected');

    ws.on('message', async (data) => {
      try {
        const request = JSON.parse(data.toString());
        const response = await handleMCPRequest(request);
        ws.send(JSON.stringify(response));
      } catch (error) {
        logger.error({ error: error.message }, 'Failed to handle message');
        ws.send(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: {
            code: -32700,
            message: 'Parse error'
          }
        }));
      }
    });

    ws.on('close', () => {
      logger.info('Client disconnected');
    });

    ws.on('error', (error) => {
      logger.error({ error: error.message }, 'WebSocket error');
    });
  });

  httpServer.listen(PORT, HOST, () => {
    logger.info({ port: PORT, host: HOST }, 'Gates MCP server started');
  });

  // Graceful shutdown
  process.on('SIGTERM', () => {
    logger.info('SIGTERM received, shutting down gracefully');
    wss.close(() => {
      httpServer.close(() => {
        process.exit(0);
      });
    });
  });
}

// Start server
startServer().catch((error) => {
  logger.error({ error: error.message }, 'Failed to start server');
  process.exit(1);
});
```

### File: /mnt/projects/Joshua/mads/gates/loglib.js
```
import redis from 'redis';

const LEVELS = { "TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40 };
const DEFAULT_REDACT_FIELDS = new Set(['password', 'token', 'api_key', 'authorization', 'secret']);
const REDACTED_VALUE = "[REDACTED]";

export class ICCMLogger {
    /**
     * Non-blocking logger that sends logs to Godot via Redis (REQ-LIB-003)
     * @param {object} options
     * @param {string} options.component - Component name
     * @param {string} [options.redisUrl='redis://localhost:6379']
     * @param {string} [options.defaultLevel='INFO']
     * @param {string[]} [options.redactFields=[]]
     * @param {number} [options.maxQueueSize=100000]
     * @param {string} [options.logQueueName='logs:queue']
     */
    constructor({ component, redisUrl = 'redis://localhost:6379', defaultLevel = 'INFO', redactFields = [], maxQueueSize = 100000, logQueueName = 'logs:queue' }) {
        if (!component) {
            throw new Error('ICCMLogger requires a "component" name.');
        }
        this.component = component;
        this.level = LEVELS[defaultLevel.toUpperCase()] || LEVELS.INFO;
        this.redactFields = new Set([...DEFAULT_REDACT_FIELDS, ...redactFields]);
        this.maxQueueSize = maxQueueSize;
        this.logQueueName = logQueueName;
        this._redisAvailable = false;

        this.redisClient = redis.createClient({
            url: redisUrl,
            socket: { connectTimeout: 1000 }
        });

        // REQ-GOD-005: Lua script for atomic FIFO queue management
        this.luaScript = `
            local queue = KEYS[1]
            local max_size = tonumber(ARGV[1])
            local log_entry = ARGV[2]

            local current_size = redis.call('LLEN', queue)
            if current_size >= max_size then
                redis.call('RPOP', queue)
            end
            redis.call('LPUSH', queue, log_entry)
            return current_size + 1
        `;

        this.redisClient.on('error', (err) => {
            if (this._redisAvailable) {
                this._logFallbackWarning(`Redis connection error: ${err.message}. Falling back to local logging.`);
            }
            this._redisAvailable = false;
        });

        this.redisClient.on('ready', () => {
            if (!this._redisAvailable) {
                console.log(`[ICCMLogger INFO] ${this.component}: Successfully connected to Redis.`);
            }
            this._redisAvailable = true;
        });

        // Fire-and-forget connection attempt
        this.redisClient.connect().catch(err => {
            this._logFallbackWarning(`Could not connect to Redis at ${redisUrl}. Reason: ${err.message}. Falling back to local logging.`);
        });
    }

    /** REQ-LIB-005: Dynamically change the log level */
    setLevel(level) {
        const newLevel = LEVELS[level.toUpperCase()];
        if (newLevel !== undefined) {
            this.level = newLevel;
        } else {
            this._logFallbackWarning(`Invalid log level '${level}'. Level not changed.`);
        }
    }

    /** REQ-SEC-001/002/003: Recursively redact sensitive fields */
    _redact(data) {
        if (data === null || typeof data !== 'object') {
            return data;
        }

        if (Array.isArray(data)) {
            return data.map(item => this._redact(item));
        }

        const cleanData = {};
        for (const key in data) {
            if (Object.prototype.hasOwnProperty.call(data, key)) {
                if (this.redactFields.has(key.toLowerCase())) {
                    cleanData[key] = REDACTED_VALUE;
                } else {
                    cleanData[key] = this._redact(data[key]);
                }
            }
        }
        return cleanData;
    }

    /** Internal log method */
    async _log(levelName, message, data, traceId) {
        const levelNum = LEVELS[levelName];
        if (levelNum < this.level) {
            return; // REQ-LIB-006: Filter logs below current level
        }

        const logEntry = {
            component: this.component,
            level: levelName,
            message: message,
            trace_id: traceId || null, // REQ-COR-004, REQ-COR-005
            data: data ? this._redact(data) : null,
            created_at: new Date().toISOString()
        };

        // REQ-LIB-003: Non-blocking push with local fallback
        if (!this._redisAvailable) {
            this._logLocal(logEntry);
            return;
        }

        try {
            // REQ-LIB-004: Atomic FIFO queue management
            await this.redisClient.eval(
                this.luaScript,
                {
                    keys: [this.logQueueName],
                    arguments: [String(this.maxQueueSize), JSON.stringify(logEntry)]
                }
            );
        } catch (err) {
            this._redisAvailable = false;
            this._logFallbackWarning(`Redis command failed. Reason: ${err.message}. Falling back to local logging.`);
            this._logLocal(logEntry);
        }
    }

    /** REQ-LIB-007: Log a warning indicating fallback mode */
    _logFallbackWarning(message) {
        console.warn(`[ICCMLogger WARNING] ${this.component}: ${message}`);
    }

    /** Logs to stdout as a fallback */
    _logLocal(logEntry) {
        console.log(JSON.stringify(logEntry));
    }

    // REQ-LIB-001: Public log methods
    trace(message, data, traceId) { this._log('TRACE', message, data, traceId); }
    debug(message, data, traceId) { this._log('DEBUG', message, data, traceId); }
    info(message, data, traceId) { this._log('INFO', message, data, traceId); }
    warn(message, data, traceId) { this._log('WARN', message, data, traceId); }
    error(message, data, traceId) { this._log('ERROR', message, data, traceId); }

    /** Gracefully close the Redis connection */
    async close() {
        if (this.redisClient && this.redisClient.isOpen) {
            await this.redisClient.quit();
        }
    }
}
```

### File: /mnt/projects/Joshua/mads/gates/Dockerfile
```
FROM node:22-alpine

# Install LibreOffice and dependencies
RUN apk add --no-cache \
    libreoffice \
    libreoffice-writer \
    ttf-liberation \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install --omit=dev

# Copy application files
COPY server.js ./

# Create output directory
RUN mkdir -p /app/output && chmod 777 /app/output

# Expose WebSocket port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8050/health || exit 1

# Start server
CMD ["node", "server.js"]
```

### File: /mnt/projects/Joshua/mads/gates/docker-compose.yml
```
services:
  gates-mcp-blue:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: gates-mcp-blue
    image: iccm/gates:blue
    ports:
      - "9051:8050"
    environment:
      - GATES_PORT=8050
      - GATES_HOST=0.0.0.0
      - PLAYFAIR_URL=ws://playfair-mcp:8040
      - LOG_LEVEL=info
      - NODE_ENV=production
    volumes:
      - gates-output:/app/output
    networks:
      - iccm_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2'
        reservations:
          memory: 512M
          cpus: '1'
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  gates-output:
    driver: local

networks:
  iccm_network:
    external: true
```

### File: /mnt/projects/Joshua/mads/gates/package.json
```
{
  "name": "gates-mcp-server",
  "version": "1.0.0",
  "description": "Gates Document Generation Gateway - Markdown to ODT conversion with Playfair diagram integration",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "jest",
    "dev": "node --watch server.js"
  },
  "keywords": [
    "mcp",
    "websocket",
    "markdown",
    "odt",
    "document-generation",
    "playfair"
  ],
  "author": "ICCM Project",
  "license": "MIT",
  "dependencies": {
    "ws": "^8.17.0",
    "markdown-it": "^14.0.0",
    "markdown-it-multimd-table": "^4.2.3",
    "markdown-it-attrs": "^4.1.6",
    "markdown-it-task-lists": "^2.1.1",
    "execa": "^8.0.1",
    "p-queue": "^8.0.1",
    "pino": "^8.19.0",
    "websocket": "^1.0.34"
  },
  "devDependencies": {
    "jest": "^29.7.0"
  }
}
```

## SERGEY (Python MCP Server - Already Migrated)

### File: /mnt/projects/Joshua/mads/sergey/sergey_server.py
```
#!/usr/bin/env python3
"""
Sergey - Google Workspace MAD
Named after Sergey Brin, co-founder of Google

Provides comprehensive Google Workspace integration via MCP tools.
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import io
import mimetypes
from datetime import datetime, timedelta

# Google API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ICCM standard libraries
from joshua_network import Server as MCPServer, ToolError as MCPToolError
from joshua_logger import Logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize joshua_logger
jlogger = Logger()

class SergeyWorkspace:
    """Google Workspace integration manager"""

    def __init__(self, service_account_path: str):
        """Initialize Google services with service account"""
        self.service_account_path = service_account_path
        self.google_drive_service = None
        self.google_sheets_service = None
        self.google_docs_service = None
        self.google_slides_service = None
        self.google_calendar_service = None

    async def initialize(self):
        """Initialize all Google services"""
        try:
            await jlogger.log("INFO", "Initializing Sergey Google Workspace MAD", "sergey")

            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/presentations',
                    'https://www.googleapis.com/auth/calendar'
                ]
            )

            self.google_drive_service = build('drive', 'v3', credentials=credentials)
            self.google_sheets_service = build('sheets', 'v4', credentials=credentials)
            self.google_docs_service = build('docs', 'v1', credentials=credentials)
            self.google_slides_service = build('slides', 'v1', credentials=credentials)
            self.google_calendar_service = build('calendar', 'v3', credentials=credentials)

            await jlogger.log("INFO", "Google services initialized successfully", "sergey", data={"services": ["drive", "sheets", "docs", "slides", "calendar"]})
            logger.info("Sergey Google Workspace MAD initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize Google services: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await jlogger.log("ERROR", error_msg, "sergey", data={"error": str(e)})
            raise

    # ============ GOOGLE SHEETS OPERATIONS ============

    def _sheets_read_sync(self, sheet_id: str, range_name: str) -> dict:
        return self.google_sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name
        ).execute()

    async def sheets_read(self, sheet_id: str, range_name: str = "A1:Z1000") -> dict:
        """Read data from a Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading sheet {sheet_id}", "sergey", data={"sheet_id": sheet_id, "range": range_name})

            result = await asyncio.to_thread(self._sheets_read_sync, sheet_id, range_name)

            values = result.get("values", [])
            await jlogger.log("INFO", f"Successfully read {len(values)} rows from sheet", "sergey")
            return {"sheet_id": sheet_id, "range": range_name, "values": values, "row_count": len(values)}
        except HttpError as e:
            error_msg = f"Google Sheets read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"sheet_id": sheet_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _sheets_write_sync(self, sheet_id: str, range_name: str, values: list) -> dict:
        body = {"values": values}
        return self.google_sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name, valueInputOption="RAW", body=body
        ).execute()

    async def sheets_write(self, sheet_id: str, range_name: str, values: list) -> dict:
        """Write data to a Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Writing to sheet {sheet_id}", "sergey", data={"sheet_id": sheet_id, "range": range_name, "rows": len(values)})

            result = await asyncio.to_thread(self._sheets_write_sync, sheet_id, range_name, values)

            await jlogger.log("INFO", f"Successfully wrote {result.get('updatedCells')} cells", "sergey")
            return {"sheet_id": sheet_id, "updated_cells": result.get("updatedCells"), "updated_range": result.get("updatedRange")}
        except HttpError as e:
            error_msg = f"Google Sheets write error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"sheet_id": sheet_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _sheets_create_sync(self, title: str) -> dict:
        body = {"properties": {"title": title}}
        return self.google_sheets_service.spreadsheets().create(body=body).execute()

    async def sheets_create(self, title: str) -> dict:
        """Create a new Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new sheet: {title}", "sergey")

            result = await asyncio.to_thread(self._sheets_create_sync, title)

            await jlogger.log("INFO", "Successfully created sheet", "sergey", data={"sheet_id": result.get("spreadsheetId"), "title": title})
            return {"sheet_id": result.get("spreadsheetId"), "title": title, "url": result.get("spreadsheetUrl")}
        except HttpError as e:
            error_msg = f"Google Sheets create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE DOCS OPERATIONS ============

    def _docs_create_sync(self, title: str, content: Optional[str]) -> dict:
        doc_metadata = {'name': title, 'mimeType': 'application/vnd.google-apps.document'}
        doc = self.google_drive_service.files().create(body=doc_metadata, fields='id,name,webViewLink').execute()
        if content:
            requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
            self.google_docs_service.documents().batchUpdate(documentId=doc['id'], body={'requests': requests}).execute()
        return doc

    async def docs_create(self, title: str, content: Optional[str] = None) -> dict:
        """Create a new Google Document in a non-blocking way."""
        if not self.google_docs_service or not self.google_drive_service:
            raise MCPToolError("Google Docs/Drive services not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new document: {title}", "sergey")

            doc = await asyncio.to_thread(self._docs_create_sync, title, content)

            await jlogger.log("INFO", "Successfully created document", "sergey", data={"doc_id": doc['id'], "title": title})
            return {"doc_id": doc['id'], "title": doc['name'], "url": doc['webViewLink']}
        except HttpError as e:
            error_msg = f"Google Docs create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _docs_read_sync(self, doc_id: str) -> dict:
        return self.google_docs_service.documents().get(documentId=doc_id).execute()

    async def docs_read(self, doc_id: str) -> dict:
        """Read content from a Google Document in a non-blocking way."""
        if not self.google_docs_service:
            raise MCPToolError("Google Docs service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading document {doc_id}", "sergey")

            document = await asyncio.to_thread(self._docs_read_sync, doc_id)

            content_parts = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for para_elem in element.get('paragraph', {}).get('elements', []):
                        if 'textRun' in para_elem:
                            content_parts.append(para_elem['textRun'].get('content', ''))
            text_content = ''.join(content_parts)

            await jlogger.log("INFO", "Successfully read document", "sergey", data={"doc_id": doc_id, "length": len(text_content)})
            return {"doc_id": doc_id, "title": document.get('title'), "content": text_content, "revision_id": document.get('revisionId')}
        except HttpError as e:
            error_msg = f"Google Docs read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"doc_id": doc_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _docs_get_end_index_sync(self, doc_id: str) -> int:
        doc = self.google_docs_service.documents().get(documentId=doc_id, fields='body(content(endIndex))').execute()
        body = doc.get('body', {})
        content = body.get('content', [])
        return content[-1].get('endIndex', 1) if content else 1

    def _docs_batch_update_sync(self, doc_id: str, requests: list) -> dict:
        return self.google_docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

    async def docs_update(self, doc_id: str, content: str, update_mode: str = 'APPEND') -> dict:
        """Appends or replaces content in a Google Doc."""
        if not self.google_docs_service:
            raise MCPToolError("Google Docs service not initialized", code=-32603)
        try:
            end_index = await asyncio.to_thread(self._docs_get_end_index_sync, doc_id)
            requests = []
            if update_mode.upper() == 'REPLACE':
                if end_index > 1:
                    requests.append({'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}})
                requests.append({'insertText': {'location': {'index': 1}, 'text': content}})
            else: # APPEND
                # Ensure content starts on a new line if doc is not empty
                insert_text = content
                if end_index > 1:
                     insert_text = '\n' + content
                requests.append({'insertText': {'location': {'index': end_index - 1}, 'text': insert_text}})

            result = await asyncio.to_thread(self._docs_batch_update_sync, doc_id, requests)
            return {"doc_id": doc_id, "replies": len(result.get('replies', [])), "status": "success"}
        except HttpError as e:
            error_msg = f"Google Docs update error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"doc_id": doc_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    async def docs_create_from_markdown(self, title: str, markdown_content: str) -> dict:
        """Creates a new Google Doc from Markdown content."""
        if not self.google_docs_service or not self.google_drive_service:
            raise MCPToolError("Google Docs/Drive services not initialized", code=-32603)
        try:
            # 1. Create a blank document first
            doc_info = await self.docs_create(title)
            doc_id = doc_info['doc_id']

            # 2. Build a list of requests from markdown
            requests = []
            current_index = 1
            lines = markdown_content.split('\n')

            for line in lines:
                line_with_newline = line + '\n'
                line_len = len(line_with_newline)

                # Insert the text of the current line
                requests.append({'insertText': {'location': {'index': current_index}, 'text': line_with_newline}})

                # Apply formatting based on markdown syntax
                range_to_format = {'startIndex': current_index, 'endIndex': current_index + line_len -1}

                if line.startswith('# '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_1'}, 'fields': 'namedStyleType'}})
                elif line.startswith('## '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_2'}, 'fields': 'namedStyleType'}})
                elif line.startswith('### '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_3'}, 'fields': 'namedStyleType'}})
                elif line.strip().startswith(('* ', '- ')):
                    requests.append({'createParagraphBullets': {'range': range_to_format, 'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'}})

                current_index += line_len

            # 3. Send all requests in a single batch update
            if requests:
                await asyncio.to_thread(self._docs_batch_update_sync, doc_id, requests)

            return doc_info
        except HttpError as e:
            error_msg = f"Google Docs markdown creation error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE SLIDES OPERATIONS ============

    def _slides_create_sync(self, title: str) -> dict:
        body = {"title": title}
        return self.google_slides_service.presentations().create(body=body).execute()

    async def slides_create(self, title: str) -> dict:
        """Create a new Google Slides presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new presentation: {title}", "sergey")

            presentation = await asyncio.to_thread(self._slides_create_sync, title)

            await jlogger.log("INFO", "Successfully created presentation", "sergey", data={"presentation_id": presentation.get("presentationId"), "title": title})
            return {"presentation_id": presentation.get("presentationId"), "title": title, "url": f"https://docs.google.com/presentation/d/{presentation.get('presentationId')}/edit"}
        except HttpError as e:
            error_msg = f"Google Slides create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _slides_add_slide_sync(self, presentation_id: str, title_text: str, body_text: Optional[str]) -> dict:
        slide_id = f"slide_{int(datetime.now().timestamp() * 1000)}"
        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}
                }
            }
        ]

        # Add title text
        if title_text:
            requests.append({
                "insertText": {
                    "objectId": f"{slide_id}.title",
                    "text": title_text
                }
            })

        # Add body text
        if body_text:
            requests.append({
                "insertText": {
                    "objectId": f"{slide_id}.body",
                    "text": body_text
                }
            })

        body = {"requests": requests}
        return self.google_slides_service.presentations().batchUpdate(
            presentationId=presentation_id, body=body
        ).execute()

    async def slides_add_slide(self, presentation_id: str, title: str, body: Optional[str] = None) -> dict:
        """Add a new slide to a presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Adding slide to presentation {presentation_id}", "sergey")

            result = await asyncio.to_thread(self._slides_add_slide_sync, presentation_id, title, body)

            await jlogger.log("INFO", "Successfully added slide", "sergey")
            return {"presentation_id": presentation_id, "status": "success", "replies_count": len(result.get('replies', []))}
        except HttpError as e:
            error_msg = f"Google Slides add slide error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"presentation_id": presentation_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _slides_read_sync(self, presentation_id: str) -> dict:
        return self.google_slides_service.presentations().get(presentationId=presentation_id).execute()

    async def slides_read(self, presentation_id: str) -> dict:
        """Read information about a presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading presentation {presentation_id}", "sergey")

            presentation = await asyncio.to_thread(self._slides_read_sync, presentation_id)

            slides = presentation.get('slides', [])
            slide_info = []
            for slide in slides:
                slide_data = {"slide_id": slide.get('objectId')}
                # Extract title if exists
                for element in slide.get('pageElements', []):
                    if element.get('shape', {}).get('shapeType') == 'TEXT_BOX':
                        if 'text' in element.get('shape', {}):
                            text_elements = element['shape']['text'].get('textElements', [])
                            text_content = ''.join([t.get('textRun', {}).get('content', '') for t in text_elements if 'textRun' in t])
                            slide_data['content'] = text_content[:100]  # First 100 chars
                slide_info.append(slide_data)

            await jlogger.log("INFO", "Successfully read presentation", "sergey")
            return {
                "presentation_id": presentation_id,
                "title": presentation.get('title'),
                "slide_count": len(slides),
                "slides": slide_info
            }
        except HttpError as e:
            error_msg = f"Google Slides read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"presentation_id": presentation_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE CALENDAR OPERATIONS ============

    def _calendar_list_sync(self, time_min: Optional[str], time_max: Optional[str], max_results: int) -> dict:
        params = {
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        if time_min:
            params['timeMin'] = time_min
        if time_max:
            params['timeMax'] = time_max

        return self.google_calendar_service.events().list(
            calendarId='primary', **params
        ).execute()

    async def calendar_list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> dict:
        """List calendar events."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", "Listing calendar events", "sergey")

            # Default to next 7 days if no time range specified
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

            result = await asyncio.to_thread(self._calendar_list_sync, time_min, time_max, max_results)

            events = result.get('items', [])
            event_list = []
            for event in events:
                event_data = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No title'),
                    'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                    'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')[:200] if event.get('description') else ''
                }
                event_list.append(event_data)

            await jlogger.log("INFO", f"Found {len(events)} events", "sergey")
            return {"events": event_list, "count": len(events)}
        except HttpError as e:
            error_msg = f"Google Calendar list error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _calendar_create_sync(self, summary: str, start_time: str, end_time: str, description: Optional[str], location: Optional[str], attendees: Optional[List[str]]) -> dict:
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        return self.google_calendar_service.events().insert(
            calendarId='primary', body=event
        ).execute()

    async def calendar_create_event(self, summary: str, start_time: str, end_time: str,
                                   description: Optional[str] = None, location: Optional[str] = None,
                                   attendees: Optional[List[str]] = None) -> dict:
        """Create a calendar event."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating calendar event: {summary}", "sergey")

            event = await asyncio.to_thread(self._calendar_create_sync, summary, start_time, end_time, description, location, attendees)

            await jlogger.log("INFO", "Successfully created event", "sergey", data={"event_id": event.get('id'), "summary": summary})
            return {
                "event_id": event.get('id'),
                "summary": summary,
                "link": event.get('htmlLink'),
                "status": "created"
            }
        except HttpError as e:
            error_msg = f"Google Calendar create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"summary": summary, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _calendar_delete_sync(self, event_id: str) -> None:
        self.google_calendar_service.events().delete(
            calendarId='primary', eventId=event_id
        ).execute()

    async def calendar_delete_event(self, event_id: str) -> dict:
        """Delete a calendar event."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Deleting calendar event: {event_id}", "sergey")

            await asyncio.to_thread(self._calendar_delete_sync, event_id)

            await jlogger.log("INFO", "Successfully deleted event", "sergey", data={"event_id": event_id})
            return {"event_id": event_id, "status": "deleted"}
        except HttpError as e:
            error_msg = f"Google Calendar delete error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"event_id": event_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE DRIVE OPERATIONS ============

    def _drive_list_sync(self, query: Optional[str], page_size: int) -> dict:
        params = {'pageSize': page_size, 'fields': "nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)"}
        if query:
            params['q'] = query
        return self.google_drive_service.files().list(**params).execute()

    async def drive_list(self, query: Optional[str] = None, page_size: int = 20) -> dict:
        """List files in Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", "Listing Drive files", "sergey", data={"query": query})

            results = await asyncio.to_thread(self._drive_list_sync, query, page_size)

            files = results.get('files', [])
            await jlogger.log("INFO", f"Found {len(files)} files", "sergey")
            return {"files": files, "count": len(files), "next_page_token": results.get('nextPageToken')}
        except HttpError as e:
            error_msg = f"Google Drive list error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"query": query, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _drive_upload_sync(self, file_path: str, folder_id: Optional[str]) -> dict:
        file_name = os.path.basename(file_path)
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        mime_type, _ = mimetypes.guess_type(file_path)
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        return self.google_drive_service.files().create(
            body=file_metadata, media_body=media, fields='id, name, webViewLink'
        ).execute()

    async def drive_upload(self, file_path: str, folder_id: Optional[str] = None) -> dict:
        """Upload a file to Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        if not os.path.exists(file_path):
            raise MCPToolError(f"File not found: {file_path}", code=-32602, data={"file_path": file_path})
        try:
            file_name = os.path.basename(file_path)
            await jlogger.log("INFO", f"Uploading file: {file_name}", "sergey")

            file = await asyncio.to_thread(self._drive_upload_sync, file_path, folder_id)

            await jlogger.log("INFO", "Successfully uploaded file", "sergey", data={"file_id": file['id'], "name": file_name})
            return {"file_id": file['id'], "name": file['name'], "url": file.get('webViewLink')}
        except HttpError as e:
            error_msg = f"Google Drive upload error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"file": file_path, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _drive_create_folder_sync(self, folder_name: str, parent_folder_id: Optional[str]) -> dict:
        file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        return self.google_drive_service.files().create(
            body=file_metadata, fields='id, name, webViewLink'
        ).execute()

    async def drive_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> dict:
        """Create a folder in Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating folder: {folder_name}", "sergey")

            folder = await asyncio.to_thread(self._drive_create_folder_sync, folder_name, parent_folder_id)

            await jlogger.log("INFO", "Successfully created folder", "sergey", data={"folder_id": folder['id'], "name": folder_name})
            return {"folder_id": folder['id'], "name": folder['name'], "url": folder.get('webViewLink')}
        except HttpError as e:
            error_msg = f"Google Drive folder creation error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"folder": folder_name, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

# Global workspace instance
workspace: Optional[SergeyWorkspace] = None

# ============ MCP TOOL HANDLERS ============
async def sheets_read_handler(sheet_id: str, range: str = "A1:Z1000") -> dict:
    return await workspace.sheets_read(sheet_id, range)

async def sheets_write_handler(sheet_id: str, range: str, values: list) -> dict:
    return await workspace.sheets_write(sheet_id, range, values)

async def sheets_create_handler(title: str) -> dict:
    return await workspace.sheets_create(title)

async def docs_create_handler(title: str, content: Optional[str] = None) -> dict:
    return await workspace.docs_create(title, content)

async def docs_read_handler(doc_id: str) -> dict:
    return await workspace.docs_read(doc_id)

async def docs_update_handler(doc_id: str, content: str, update_mode: str = 'APPEND') -> dict:
    return await workspace.docs_update(doc_id, content, update_mode)

async def docs_create_from_markdown_handler(title: str, markdown_content: str) -> dict:
    return await workspace.docs_create_from_markdown(title, markdown_content)

async def slides_create_handler(title: str) -> dict:
    return await workspace.slides_create(title)

async def slides_add_slide_handler(presentation_id: str, title: str, body: Optional[str] = None) -> dict:
    return await workspace.slides_add_slide(presentation_id, title, body)

async def slides_read_handler(presentation_id: str) -> dict:
    return await workspace.slides_read(presentation_id)

async def calendar_list_events_handler(time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> dict:
    return await workspace.calendar_list_events(time_min, time_max, max_results)

async def calendar_create_event_handler(summary: str, start_time: str, end_time: str,
                                       description: Optional[str] = None, location: Optional[str] = None,
                                       attendees: Optional[List[str]] = None) -> dict:
    return await workspace.calendar_create_event(summary, start_time, end_time, description, location, attendees)

async def calendar_delete_event_handler(event_id: str) -> dict:
    return await workspace.calendar_delete_event(event_id)

async def drive_list_handler(query: Optional[str] = None, page_size: int = 20) -> dict:
    return await workspace.drive_list(query, page_size)

async def drive_upload_handler(file_path: str, folder_id: Optional[str] = None) -> dict:
    return await workspace.drive_upload(file_path, folder_id)

async def drive_create_folder_handler(name: str, parent_id: Optional[str] = None) -> dict:
    return await workspace.drive_create_folder(name, parent_id)

# ============ MCP TOOL DEFINITIONS ============
TOOLS = {
    # Sheets
    "sergey_sheets_read": {"description": "Read data from a Google Sheet.", "inputSchema": {"type": "object", "properties": {"sheet_id": {"type": "string", "description": "Google Sheet ID"}, "range": {"type": "string", "description": "Range to read (e.g., 'Sheet1!A1:B10')", "default": "A1:Z1000"}}, "required": ["sheet_id"]}},
    "sergey_sheets_write": {"description": "Write data to a Google Sheet.", "inputSchema": {"type": "object", "properties": {"sheet_id": {"type": "string", "description": "Google Sheet ID"}, "range": {"type": "string", "description": "Range to write (e.g., 'Sheet1!A1')"}, "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "2D array of values to write."}}, "required": ["sheet_id", "range", "values"]}},
    "sergey_sheets_create": {"description": "Create a new Google Sheet.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new sheet."}}, "required": ["title"]}},
    # Docs
    "sergey_docs_create": {"description": "Create a new Google Document.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new document."}, "content": {"type": "string", "description": "Initial plain text content for the document."}}, "required": ["title"]}},
    "sergey_docs_read": {"description": "Read all text content from a Google Document.", "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string", "description": "Google Document ID"}}, "required": ["doc_id"]}},
    "sergey_docs_update": {"description": "Append or replace content in an existing Google Document.", "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string", "description": "ID of the document to update."}, "content": {"type": "string", "description": "The text content to add."}, "update_mode": {"type": "string", "description": "How to update: 'APPEND' or 'REPLACE'.", "enum": ["APPEND", "REPLACE"], "default": "APPEND"}}, "required": ["doc_id", "content"]}},
    "sergey_docs_create_from_markdown": {"description": "Create a new Google Document from Markdown content, preserving basic formatting.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new document."}, "markdown_content": {"type": "string", "description": "The document content in Markdown format. Supports headings (#, ##) and bullet points (* or -)."}}, "required": ["title", "markdown_content"]}},
    # Slides
    "sergey_slides_create": {"description": "Create a new Google Slides presentation.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new presentation."}}, "required": ["title"]}},
    "sergey_slides_add_slide": {"description": "Add a new slide to an existing presentation.", "inputSchema": {"type": "object", "properties": {"presentation_id": {"type": "string", "description": "ID of the presentation."}, "title": {"type": "string", "description": "Title text for the slide."}, "body": {"type": "string", "description": "Body text for the slide (optional)."}}, "required": ["presentation_id", "title"]}},
    "sergey_slides_read": {"description": "Get information about a Google Slides presentation.", "inputSchema": {"type": "object", "properties": {"presentation_id": {"type": "string", "description": "ID of the presentation to read."}}, "required": ["presentation_id"]}},
    # Calendar
    "sergey_calendar_list_events": {"description": "List calendar events within a time range.", "inputSchema": {"type": "object", "properties": {"time_min": {"type": "string", "description": "Start time in ISO format (e.g., '2024-01-01T00:00:00Z')."}, "time_max": {"type": "string", "description": "End time in ISO format."}, "max_results": {"type": "integer", "description": "Maximum number of events to return.", "default": 10}}}},
    "sergey_calendar_create_event": {"description": "Create a new calendar event.", "inputSchema": {"type": "object", "properties": {"summary": {"type": "string", "description": "Event title/summary."}, "start_time": {"type": "string", "description": "Start time in ISO format (e.g., '2024-01-01T10:00:00Z')."}, "end_time": {"type": "string", "description": "End time in ISO format."}, "description": {"type": "string", "description": "Event description (optional)."}, "location": {"type": "string", "description": "Event location (optional)."}, "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses (optional)."}}, "required": ["summary", "start_time", "end_time"]}},
    "sergey_calendar_delete_event": {"description": "Delete a calendar event.", "inputSchema": {"type": "object", "properties": {"event_id": {"type": "string", "description": "ID of the event to delete."}}, "required": ["event_id"]}},
    # Drive
    "sergey_drive_list": {"description": "List files in Google Drive, optionally with a search query.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query in Drive API format (e.g., \"name contains 'report' and mimeType='application/vnd.google-apps.spreadsheet'\")."}, "page_size": {"type": "integer", "description": "Number of results to return.", "default": 20}}}},
    "sergey_drive_upload": {"description": "Upload a local file to Google Drive.", "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Absolute path to the local file to upload."}, "folder_id": {"type": "string", "description": "ID of the parent folder in Google Drive (optional)."}}, "required": ["file_path"]}},
    "sergey_drive_create_folder": {"description": "Create a new folder in Google Drive.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "Name for the new folder."}, "parent_id": {"type": "string", "description": "ID of the parent folder (optional)."}}, "required": ["name"]}},
}

# ============ MCP TOOL HANDLERS MAPPING ============
HANDLERS = {
    "sergey_sheets_read": sheets_read_handler,
    "sergey_sheets_write": sheets_write_handler,
    "sergey_sheets_create": sheets_create_handler,
    "sergey_docs_create": docs_create_handler,
    "sergey_docs_read": docs_read_handler,
    "sergey_docs_update": docs_update_handler,
    "sergey_docs_create_from_markdown": docs_create_from_markdown_handler,
    "sergey_slides_create": slides_create_handler,
    "sergey_slides_add_slide": slides_add_slide_handler,
    "sergey_slides_read": slides_read_handler,
    "sergey_calendar_list_events": calendar_list_events_handler,
    "sergey_calendar_create_event": calendar_create_event_handler,
    "sergey_calendar_delete_event": calendar_delete_event_handler,
    "sergey_drive_list": drive_list_handler,
    "sergey_drive_upload": drive_upload_handler,
    "sergey_drive_create_folder": drive_create_folder_handler,
}

# ============ MAIN ENTRY POINT ============
async def main():
    """Main entry point for Sergey MAD"""
    global workspace

    port = int(os.getenv("SERGEY_PORT", "8095"))
    service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "/config/google-service-account-credentials.json")

    if not os.path.exists(service_account_path):
        msg = f"FATAL: Google service account file not found at {service_account_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    workspace = SergeyWorkspace(service_account_path)
    await workspace.initialize()

    server = MCPServer(
        name="sergey",
        version="2.0.0", # Version bumped to reflect full Google Workspace suite
        port=port,
        tool_definitions=TOOLS,
        tool_handlers=HANDLERS
    )

    logger.info(f"Starting Sergey MAD on port {port} with {len(TOOLS)} tools registered.")
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (FileNotFoundError, KeyboardInterrupt) as e:
        logger.info(f"Sergey server shutting down: {e}")
    except Exception as e:
        logger.critical("An unhandled exception occurred in Sergey MAD", exc_info=True)```

### File: /mnt/projects/Joshua/mads/sergey/Dockerfile
```
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install joshua-libs (joshua_network + joshua_logger)
COPY lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Copy requirements first for better caching
COPY mads/sergey/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY mads/sergey/sergey_server.py .

# Create config and data directories
RUN mkdir -p /config /data

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV SERGEY_PORT=8095
ENV GOOGLE_SERVICE_ACCOUNT_PATH=/config/google-service-account-credentials.json
ENV GODOT_URL=ws://godot-mcp:9060
ENV LOGGING_ENABLED=true

# Run the server
CMD ["python", "sergey_server.py"]```

### File: /mnt/projects/Joshua/mads/sergey/docker-compose.yml
```
version: '3.8'

services:
  sergey-mcp:
    build:
      context: ../..
      dockerfile: mads/sergey/Dockerfile
    container_name: sergey-mcp
    restart: unless-stopped
    ports:
      - "8095:8095"
    volumes:
      # Mount Google service account credentials
      - ./config:/config:ro
      # Working directory for uploads/downloads
      - /mnt/irina_storage/sergey:/data
    environment:
      - SERGEY_PORT=8095
      - GOOGLE_SERVICE_ACCOUNT_PATH=/config/google-service-account-credentials.json
      - GODOT_URL=ws://godot-mcp:9060
      - LOGGING_ENABLED=true
      - PYTHONPATH=/app
      - LOG_LEVEL=info
    networks:
      - iccm_network
    healthcheck:
      test: ["CMD", "python", "-c", "import websocket; ws = websocket.create_connection('ws://localhost:8095'); ws.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  iccm_network:
    external: true```

### File: /mnt/projects/Joshua/mads/sergey/requirements.txt
```
# Sergey MAD Requirements

# Core Google API dependencies
google-auth==2.41.1
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.183.0
googleapis-common-protos==1.70.0

# WebSocket and async dependencies
websocket-client==1.7.0
websockets==12.0
aiohttp==3.9.5
pydantic==2.5.0

# Note: iccm-network and mcp_logger are mounted via docker-compose volumes```

## JOSHUA LIBRARIES (Reference)

### joshua_network/server.py
```python
"""
joshua_network: Standard Server Implementation

This module provides a standardized WebSocket server that binds to 0.0.0.0
to ensure reliable container-to-container communication. It handles the
JSON-RPC 2.0 protocol, connection keep-alives, and a health check endpoint.
"""
import asyncio
import json
import logging
import traceback
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets
from websockets.datastructures import Headers
from websockets.server import WebSocketServerProtocol

from .errors import ToolError


class Server:
    """
    A standardized WebSocket server for JSON-RPC 2.0 communication.

    This server handles all WebSocket connection logic, JSON-RPC protocol
    details, and tool routing. Users only need to provide service metadata,
    tool definitions, and their corresponding async handlers.

    The server always binds to '0.0.0.0' to be accessible from other
    containers and exposes a '/healthz' endpoint for health checks.

    Args:
        name: The name of the service (e.g., "horace").
        version: The semantic version of the service (e.g., "1.0.0").
        port: The network port to listen on.
        tool_definitions: A dictionary mapping tool names to their schemas.
        tool_handlers: A dictionary mapping tool names to their async handlers.
        logger: An optional custom logger instance. If None, a default
                logger is created.
    """

    def __init__(
        self,
        name: str = "joshua_network_server",
        version: str = "1.0.0",
        port: int = 9000,
        tool_definitions: Optional[Dict[str, Any]] = None,
        tool_handlers: Optional[Dict[str, Callable[..., Awaitable[Any]]]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.version = version
        self.port = port
        self.tool_definitions = tool_definitions or {}
        self.tool_handlers = tool_handlers or {}
        self.host = "0.0.0.0"  # CRITICAL: Always bind to 0.0.0.0
        self.logger = logger or self._create_default_logger()
        self._server: Optional[websockets.WebSocketServer] = None
        self._tool_handlers = tool_handlers or {}

    def _create_default_logger(self) -> logging.Logger:
        """Creates and configures a default logger for the server."""
        logger = logging.getLogger(f"joshua_network.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"%(asctime)s - {self.name} - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def is_serving(self) -> bool:
        """Returns True if the server is currently serving."""
        return self._server is not None

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the 'initialize' method, returning server capabilities."""
        self.logger.info(f"Initialize request from client: {params.get('clientInfo', {})}")
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self.name, "version": self.version},
        }

    async def _handle_tools_list(self) -> Dict[str, Any]:
        """Handles the 'tools/list' method, returning available tools."""
        tools = [{"name": name, **definition} for name, definition in self.tool_definitions.items()]
        self.logger.info(f"Tools list requested: {len(tools)} tools available.")
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handles 'tools/call', routing to the appropriate tool handler."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tool_handlers:
            raise ToolError(f"Tool '{tool_name}' not found", code=-32601)

        self.logger.info(f"Calling tool: {tool_name}")
        try:
            handler = self.tool_handlers[tool_name]
            result = await handler(**arguments)
            return result
        except ToolError:
            raise  # Re-raise user-defined errors
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}\n{traceback.format_exc()}")
            raise ToolError(f"Tool execution failed: {str(e)}", code=-32000)

    async def _process_message(self, message_str: str) -> Optional[str]:
        """Parses a JSON-RPC message, routes it, and formats the response."""
        try:
            message = json.loads(message_str)
            msg_id = message.get("id")
            method = message.get("method")
            params = message.get("params", {})
        except json.JSONDecodeError as e:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Invalid JSON: {str(e)}"}, "id": None})

        is_notification = "id" not in message

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "notifications/initialized":
                # MCP protocol notification - acknowledge silently
                self.logger.debug("Received notifications/initialized")
                return None
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            else:
                raise ToolError(f"Method '{method}' not supported", code=-32601)

            if is_notification:
                return None
            return json.dumps({"jsonrpc": "2.0", "result": result, "id": msg_id})

        except ToolError as e:
            if is_notification:
                self.logger.error(f"Error in notification '{method}': {e.message}")
                return None
            return json.dumps({"jsonrpc": "2.0", "error": {"code": e.code, "message": e.message}, "id": msg_id})
        except Exception as e:
            self.logger.error(f"Unexpected error handling '{method}': {e}\n{traceback.format_exc()}")
            if is_notification:
                return None
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal server error"}, "id": msg_id})

    async def _health_check_handler(self, path: str, request_headers: Headers) -> Optional[tuple]:
        """Responds to HTTP health checks at '/healthz'."""
        if path == "/healthz":
            self.logger.debug("Health check request received")
            return (HTTPStatus.OK, [("Content-Type", "text/plain")], b"OK\n")
        return None  # Let `websockets` handle the WebSocket upgrade

    async def _connection_handler(self, websocket: WebSocketServerProtocol) -> None:
        """Manages the lifecycle of a single client WebSocket connection."""
        remote_addr = websocket.remote_address
        self.logger.info(f"Client connected: {remote_addr}")
        try:
            async for message in websocket:
                response = await self._process_message(str(message))
                if response is not None:
                    await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {remote_addr}")
        except Exception as e:
            self.logger.error(f"Connection error with {remote_addr}: {e}")
        finally:
            self.logger.info(f"Client session ended: {remote_addr}")

    async def start(self) -> None:
        """Starts the server and runs it indefinitely."""
        self.logger.info(f"Starting {self.name} server v{self.version} on {self.host}:{self.port}")
        self.logger.info(f"Tools available: {list(self.tool_definitions.keys())}")

        self._server = await websockets.serve(
            self._connection_handler,
            self.host,
            self.port,
            process_request=self._health_check_handler,
            ping_interval=20,
            ping_timeout=20,
            max_size=200 * 1024 * 1024,  # 200MB
        )
        self.logger.info(f"✓ Server listening at ws://{self.host}:{self.port}")
        self.logger.info(f"✓ Health check available at http://{self.host}:{self.port}/healthz")
        await asyncio.Future()  # Run forever

    async def stop(self) -> None:
        """Gracefully stops the server."""
        if self._server:
            self.logger.info(f"Stopping {self.name} server...")
            self._server.close()
            await self._server.wait_closed()
            self.logger.info(f"✓ Server stopped.")
```

### joshua_logger/logger.py
```python
"""
Core implementation of the asynchronous, fault-tolerant logger.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from joshua_network.client import Client

# Internal logger for the library itself, not for application logs
internal_logger = logging.getLogger(__name__)


class Logger:
    """
    Manages a persistent WebSocket connection to send logs to Godot.

    Uses joshua_network.Client for robust connection management and
    JSON-RPC communication. Designed to fail silently to ensure logging
    issues never crash the application.

    Args:
        url: The WebSocket URL for the Godot logging service. Defaults to
             the `JOSHUA_LOGGER_URL` env var or 'ws://godot-mcp:9060'.
        timeout: The timeout in seconds for sending a log message. Defaults
                 to `JOSHUA_LOGGER_TIMEOUT` env var or 2.0.
    """

    def __init__(self, url: Optional[str] = None, timeout: Optional[float] = None, backup_dir: Optional[str] = None):
        self.url = url or os.environ.get("JOSHUA_LOGGER_URL", "ws://godot-mcp:9060")
        self.timeout = timeout or float(os.environ.get("JOSHUA_LOGGER_TIMEOUT", 2.0))
        self.backup_dir = Path(backup_dir or os.environ.get("JOSHUA_LOGGER_BACKUP_DIR", "/tmp/joshua_logs"))
        self._client = Client(self.url, timeout=int(self.timeout))

        # Ensure backup directory exists
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            internal_logger.warning(f"Failed to create backup directory {self.backup_dir}: {e}")

        internal_logger.info(f"Logger initialized: url={self.url}, timeout={self.timeout}, backup_dir={self.backup_dir}")

    def _write_backup_log(self, level: str, message: str, component: str, data: Optional[Dict[str, Any]], trace_id: Optional[str]) -> None:
        """Write log to local filesystem as backup when Godot is unreachable."""
        try:
            # Create component-specific subdirectory
            component_dir = self.backup_dir / component
            component_dir.mkdir(parents=True, exist_ok=True)

            # Use date-based log file (one per day per component)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = component_dir / f"{today}.jsonl"

            # Create structured log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": level.upper(),
                "component": component,
                "message": message,
                "data": data,
                "trace_id": trace_id
            }

            # Append to log file (JSONL format - one JSON object per line)
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            # Ultimate fallback - log to stderr only
            internal_logger.error(f"Failed to write backup log: {e}", exc_info=True)

    async def log(
        self,
        level: str,
        message: str,
        component: str,
        data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Sends a structured log message to the Godot service.

        If Godot is unreachable, writes to local backup logs at:
        {backup_dir}/{component}/{YYYY-MM-DD}.jsonl

        This method is fire-and-forget. It will not raise exceptions on
        failure.

        Args:
            level: The log level (e.g., 'INFO', 'ERROR').
            message: The primary log message string.
            component: The name of the component generating the log.
            data: Optional dictionary of structured data.
            trace_id: Optional ID for request tracing.
        """
        try:
            # Try to send to Godot first
            await self._client.call_tool(
                tool_name="godot_logger_log",
                arguments={
                    "level": level.upper(),
                    "message": message,
                    "component": component,
                    "data": data,
                    "trace_id": trace_id,
                }
            )
        except Exception as e:
            # Godot failed - write to local backup
            internal_logger.error(f"Failed to send log to Godot, writing to backup: {e}")
            self._write_backup_log(level, message, component, data, trace_id)

    async def close(self) -> None:
        """Gracefully closes the logger connection."""
        await self._client.disconnect()
        internal_logger.info("Logger connection closed.")
```

