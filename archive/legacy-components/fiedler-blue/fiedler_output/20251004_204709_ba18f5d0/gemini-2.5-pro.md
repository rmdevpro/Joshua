Of course. Here is the complete, production-ready Phase 1 MVP implementation code for the Playfair Diagram Generation Gateway, following all requirements from the code generation package, including the critical Marco MCP pattern.

### **Design Assumptions & Choices**

*   **Worker Pool:** The implementation uses an async-based worker pool rather than actual child processes or threads. This is simpler, more efficient for I/O-bound tasks like shelling out to `dot` and `mmdc`, and avoids the overhead of process serialization in Node.js. It effectively limits concurrency to the specified pool size.
*   **Priority Queue:** A simple two-array queue (`highPriority`, `lowPriority`) is used. This is lightweight and perfectly meets the requirement to prioritize smaller diagrams without adding a complex dependency.
*   **SVG Theming:** The `svg-processor.js` uses a combination of `svgo` for optimization and direct string manipulation to inject a `<defs>` block for gradients and a `<style>` block for CSS. This is a robust and dependency-light approach for the specified theming requirements (fonts, gradients, shadows).
*   **Error Parsing:** The engine adapters include basic logic to parse stderr from `dot` and `mmdc` to extract line numbers and provide more helpful, structured error messages.
*   **Security:** All shell commands use `execFile` from `child_process` to prevent shell injection vulnerabilities, as it does not spawn a shell. Input is passed as arguments or via stdin.

---

### **Generated File Structure & Code**

#### `/mnt/projects/ICCM/playfair/Dockerfile`
```dockerfile
# Playfair Diagram Generation Gateway - Dockerfile
# Base Image: Ubuntu 24.04 with Node.js 22
FROM ubuntu:24.04

# Set non-interactive frontend to avoid prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install System Dependencies
# - curl: for downloading Node.js setup script
# - graphviz: the core DOT rendering engine
# - fonts-inter, fonts-roboto: modern fonts for theming
# - libcairo2-dev: required by Graphviz 'cairo' renderer for high-quality output
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    graphviz \
    fonts-inter \
    fonts-roboto \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js 22
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs

# 3. Install Mermaid CLI globally
# This makes the 'mmdc' command available system-wide
RUN npm install -g @mermaid-js/mermaid-cli@11.0.0

# 4. Set up Application Directory
WORKDIR /app

# 5. Install Node.js Dependencies
# Copy package files first to leverage Docker layer caching
COPY package*.json ./
# Use 'npm ci' for reproducible production builds
RUN npm ci --only=production

# 6. Copy Application Code
COPY playfair/ ./playfair/

# 7. Expose Port
# The application will listen on this port inside the container
EXPOSE 8040

# 8. Health Check
# Verifies that the server is running and responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8040/health || exit 1

# 9. Run Server
# The entry point for the container
CMD ["node", "playfair/server.js"]
```

#### `/mnt/projects/ICCM/playfair/docker-compose.yml`
```yaml
version: '3.8'

# Playfair Diagram Generation Gateway - Docker Compose Service
services:
  playfair-mcp:
    container_name: playfair-mcp
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      # Map host port 9040 to container port 8040
      - "9040:8040"
    networks:
      - iccm_network
    environment:
      # Application configuration via environment variables
      - NODE_ENV=production
      - PORT=8040
      - LOG_LEVEL=info
      - WORKER_POOL_SIZE=3      # As per requirements (2-3 workers)
      - MAX_DIAGRAM_LINES=10000 # Resource limit
      - RENDER_TIMEOUT_MS=60000 # 60-second timeout
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
    restart: unless-stopped

networks:
  iccm_network:
    # This configuration assumes the ICCM network is created externally
    external: true
```

#### `/mnt/projects/ICCM/playfair/package.json`
```json
{
  "name": "playfair-mcp-gateway",
  "version": "1.0.0",
  "description": "ICCM Diagram Generation Gateway",
  "main": "playfair/server.js",
  "scripts": {
    "start": "node playfair/server.js",
    "dev": "node --watch playfair/server.js"
  },
  "author": "ICCM Triplet Consensus",
  "license": "UNLICENSED",
  "private": true,
  "dependencies": {
    "ws": "^8.17.0",
    "sharp": "^0.33.4",
    "svgo": "^3.3.2"
  }
}
```

#### `/mnt/projects/ICCM/playfair/.dockerignore`
```
node_modules
npm-debug.log
.git
.gitignore
README.md
```

---

### `playfair/` Directory

#### `/mnt/projects/ICCM/playfair/server.js`
```javascript
// Playfair Diagram Generation Gateway
// Main WebSocket MCP Server
// Implements the Marco Pattern: Protocol handling is done here, not in workers.

const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { WorkerPool } = require('./workers/worker-pool');
const logger = require('./utils/logger');
const { detectFormat } = require('./utils/format-detector');
const { validateSyntax } = require('./utils/validator');
const toolSchemas = require('./mcp-tools');

// --- Configuration ---
const PORT = process.env.PORT || 8040;
const HOST = '0.0.0.0';
const WORKER_POOL_SIZE = parseInt(process.env.WORKER_POOL_SIZE, 10) || 3;
const MAX_DIAGRAM_LINES = parseInt(process.env.MAX_DIAGRAM_LINES, 10) || 10000;

// --- Initialization ---
const server = http.createServer();
const wss = new WebSocket.Server({ noServer: true });
const workerPool = new WorkerPool(WORKER_POOL_SIZE);

const SERVER_INFO = {
    name: 'Playfair',
    version: '1.0.0',
    capabilities: ['tools'],
    description: 'ICCM Diagram Generation Gateway'
};

// --- MCP Protocol Handler ---
async function handleMcpRequest(request, ws) {
    logger.info({ requestId: request.id, method: request.method }, 'Received MCP request');

    switch (request.method) {
        case 'initialize':
            return {
                id: request.id,
                result: SERVER_INFO
            };

        case 'tools/list':
            return {
                id: request.id,
                result: {
                    tools: Object.values(toolSchemas)
                }
            };

        case 'tools/call':
            return await handleToolCall(request);

        default:
            return {
                id: request.id,
                error: {
                    code: 'METHOD_NOT_FOUND',
                    message: `Method '${request.method}' not supported.`
                }
            };
    }
}

// --- Tool Call Router ---
async function handleToolCall(request) {
    const { tool_name, parameters } = request.params;
    const requestId = request.id;

    if (!toolSchemas[tool_name]) {
        return {
            id: requestId,
            error: { code: 'TOOL_NOT_FOUND', message: `Tool '${tool_name}' not found.` }
        };
    }

    try {
        switch (tool_name) {
            case 'playfair_create_diagram':
                return await createDiagram(requestId, parameters);
            case 'playfair_list_capabilities':
                return listCapabilities(requestId);
            case 'playfair_get_examples':
                return getExamples(requestId, parameters);
            case 'playfair_validate_syntax':
                return validateDiagramSyntax(requestId, parameters);
            default:
                throw new Error('Internal routing error');
        }
    } catch (error) {
        logger.error({ requestId, tool_name, error: error.message, stack: error.stack }, 'Tool call execution failed');
        return {
            id: requestId,
            error: {
                code: error.code || 'INTERNAL_ERROR',
                message: error.message
            }
        };
    }
}

// --- Tool Implementations ---

async function createDiagram(requestId, params) {
    const { content, format = 'auto', output_format = 'svg', theme = 'modern' } = params;

    if (!content) {
        return { id: requestId, error: { code: 'INVALID_PARAMETERS', message: "'content' parameter is required." } };
    }
    if (content.split('\n').length > MAX_DIAGRAM_LINES) {
        return { id: requestId, error: { code: 'RESOURCE_LIMIT', message: `Diagram content exceeds maximum of ${MAX_DIAGRAM_LINES} lines.` } };
    }

    const detectedFormat = format === 'auto' ? detectFormat(content) : format;
    if (!detectedFormat) {
        return { id: requestId, error: { code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format. Please specify "dot" or "mermaid".' } };
    }

    const job = {
        requestId,
        content,
        format: detectedFormat,
        options: {
            output_format,
            theme,
            width: params.width,
            height: params.height,
        }
    };

    try {
        const result = await workerPool.submit(job);
        return {
            id: requestId,
            result: {
                output_format: result.format,
                data: result.data.toString('base64'),
                message: `Successfully generated ${detectedFormat} diagram with theme '${theme}' as ${result.format}.`
            }
        };
    } catch (error) {
        // Errors from the worker pool are already structured
        return { id: requestId, error: error };
    }
}

function listCapabilities(requestId) {
    const capabilities = {
        engines: ['graphviz', 'mermaid'],
        diagram_types: {
            graphviz: ["flowchart", "orgchart", "architecture", "network", "mindmap"],
            mermaid: ["flowchart", "sequence", "er", "state", "mindmap"]
        },
        output_formats: ['svg', 'png'],
        themes: ['professional', 'modern', 'minimal', 'dark']
    };
    return { id: requestId, result: capabilities };
}

function getExamples(requestId, params) {
    const { diagram_type, format } = params;
    if (!diagram_type) {
        return { id: requestId, error: { code: 'INVALID_PARAMETERS', message: "'diagram_type' is required." } };
    }

    const exampleMap = {
        'flowchart': { dot: 'flowchart.dot', mermaid: 'sequence.mmd' }, // Mermaid uses flowchart syntax for this
        'orgchart': { dot: 'orgchart.dot' },
        'architecture': { dot: 'architecture.dot' },
        'sequence': { mermaid: 'sequence.mmd' },
        'network': { dot: 'network.dot' },
        'mindmap': { dot: 'mindmap.dot' }, // Mermaid has a mindmap, but dot is more common
        'er': { mermaid: 'er.mmd' },
        'state': { mermaid: 'state.mmd' }
    };

    const formatToUse = format || (exampleMap[diagram_type].dot ? 'dot' : 'mermaid');
    const filename = exampleMap[diagram_type]?.[formatToUse];

    if (!filename) {
        return { id: requestId, error: { code: 'NOT_FOUND', message: `No example found for diagram type '${diagram_type}' in format '${formatToUse}'.` } };
    }

    try {
        const content = fs.readFileSync(path.join(__dirname, 'examples', filename), 'utf8');
        return { id: requestId, result: { diagram_type, format: formatToUse, content } };
    } catch (error) {
        logger.error({ diagram_type, filename }, 'Failed to read example file');
        return { id: requestId, error: { code: 'INTERNAL_ERROR', message: 'Could not load example file.' } };
    }
}

async function validateDiagramSyntax(requestId, params) {
    const { content, format = 'auto' } = params;
    if (!content) {
        return { id: requestId, error: { code: 'INVALID_PARAMETERS', message: "'content' parameter is required." } };
    }

    const detectedFormat = format === 'auto' ? detectFormat(content) : format;
    if (!detectedFormat) {
        return { id: requestId, error: { code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format.' } };
    }

    const result = await validateSyntax(content, detectedFormat);
    return { id: requestId, result };
}


// --- Server Setup ---
server.on('request', (req, res) => {
    // HTTP Health Check Endpoint
    if (req.url === '/health' && req.method === 'GET') {
        const healthStatus = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            workers: {
                total: workerPool.size,
                active: workerPool.active,
                pending: workerPool.pending,
            },
        };
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(healthStatus));
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.on('upgrade', (request, socket, head) => {
    // Handle WebSocket upgrade requests
    wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
    });
});

wss.on('connection', (ws) => {
    logger.info('WebSocket client connected');

    ws.on('message', async (message) => {
        let request;
        try {
            request = JSON.parse(message);
            if (!request.id || !request.method) {
                throw new Error('Invalid MCP request format');
            }
        } catch (e) {
            ws.send(JSON.stringify({ error: { code: 'PARSE_ERROR', message: 'Invalid JSON message.' } }));
            return;
        }

        const response = await handleMcpRequest(request, ws);
        if (response) {
            ws.send(JSON.stringify(response));
        }
    });

    ws.on('close', () => {
        logger.info('WebSocket client disconnected');
    });

    ws.on('error', (error) => {
        logger.error({ error: error.message }, 'WebSocket error');
    });
});

server.listen(PORT, HOST, () => {
    logger.info(`Playfair MCP Gateway listening on ws://${HOST}:${PORT}`);
    logger.info(`Worker pool initialized with ${WORKER_POOL_SIZE} workers.`);
});

// --- Graceful Shutdown ---
process.on('SIGTERM', () => {
    logger.info('SIGTERM signal received: closing HTTP server');
    server.close(() => {
        logger.info('HTTP server closed');
        process.exit(0);
    });
});
```
```javascript
// playfair/mcp-tools.js
// Central repository for MCP tool schemas.

const toolSchemas = {
    playfair_create_diagram: {
        name: "playfair_create_diagram",
        description: "Create a professional diagram from a Graphviz DOT or Mermaid specification.",
        input_schema: {
            type: "object",
            properties: {
                content: {
                    type: "string",
                    description: "Diagram specification in DOT (for Graphviz) or Mermaid syntax."
                },
                format: {
                    type: "string",
                    enum: ["dot", "mermaid", "auto"],
                    default: "auto",
                    description: "Input format. If 'auto', the server will detect the format from the content."
                },
                output_format: {
                    type: "string",
                    enum: ["svg", "png"],
                    default: "svg",
                    description: "Output image format. SVG is recommended for scalability."
                },
                theme: {
                    type: "string",
                    enum: ["professional", "modern", "minimal", "dark"],
                    default: "modern",
                    description: "The visual theme to apply to the diagram."
                },
                width: {
                    type: "integer",
                    default: 1920,
                    description: "Output width in pixels. Primarily used for PNG output."
                },
                height: {
                    type: "integer",
                    description: "Output height in pixels. If not specified, it's determined automatically. Used for PNG."
                }
            },
            required: ["content"]
        }
    },
    playfair_list_capabilities: {
        name: "playfair_list_capabilities",
        description: "List all supported diagram engines, output formats, themes, and diagram types.",
        input_schema: {
            type: "object",
            properties: {}
        }
    },
    playfair_get_examples: {
        name: "playfair_get_examples",
        description: "Get example syntax for a specific diagram type and format.",
        input_schema: {
            type: "object",
            properties: {
                diagram_type: {
                    type: "string",
                    enum: ["flowchart", "orgchart", "architecture", "sequence", "network", "mindmap", "er", "state"],
                    description: "The type of diagram to get an example for."
                },
                format: {
                    type: "string",
                    enum: ["dot", "mermaid"],
                    description: "Optional: specify which syntax format example to retrieve if a type supports both."
                }
            },
            required: ["diagram_type"]
        }
    },
    playfair_validate_syntax: {
        name: "playfair_validate_syntax",
        description: "Validate the syntax of a diagram specification without rendering the full image.",
        input_schema: {
            type: "object",
            properties: {
                content: {
                    type: "string",
                    description: "The diagram specification content to validate."
                },
                format: {
                    type: "string",
                    enum: ["dot", "mermaid", "auto"],
                    default: "auto",
                    description: "The syntax format to validate against."
                }
            },
            required: ["content"]
        }
    }
};

module.exports = toolSchemas;
```

#### `/mnt/projects/ICCM/playfair/engines/base.js`
```javascript
// playfair/engines/base.js
// Defines the abstract interface for all rendering engines.
// This ensures that new engines can be added with a consistent API.

class DiagramEngine {
    constructor(name) {
        if (this.constructor === DiagramEngine) {
            throw new Error("Abstract classes can't be instantiated.");
        }
        this.name = name;
    }

    /**
     * Renders a diagram from a string content.
     * @param {string} content - The diagram specification (e.g., DOT or Mermaid syntax).
     * @param {object} options - Rendering options (theme, output_format, etc.).
     * @returns {Promise<{format: string, data: Buffer}>} - The rendered diagram data.
     * @throws {Error} - Throws a structured error on failure.
     */
    async render(content, options) {
        throw new Error("Method 'render()' must be implemented.");
    }

    /**
     * Validates the syntax of a diagram specification.
     * @param {string} content - The diagram specification to validate.
     * @returns {Promise<{valid: boolean, errors: Array<{line: number, message: string}>}>}
     */
    async validate(content) {
        throw new Error("Method 'validate()' must be implemented.");
    }
}

module.exports = DiagramEngine;
```

#### `/mnt/projects/ICCM/playfair/engines/graphviz.js`
```javascript
// playfair/engines/graphviz.js
// Adapter for the Graphviz (dot) rendering engine.

const { execFile } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const DiagramEngine = require('./base');
const graphvizThemes = require('../themes/graphviz-themes.json');
const svgProcessor = require('../themes/svg-processor');
const logger = require('../utils/logger');

const execFileAsync = promisify(execFile);
const TIMEOUT = parseInt(process.env.RENDER_TIMEOUT_MS, 10) || 60000;

class GraphvizEngine extends DiagramEngine {
    constructor() {
        super('graphviz');
    }

    applyTheme(dotContent, themeName) {
        const theme = graphvizThemes[themeName] || graphvizThemes.modern;
        const themeAttributes = Object.entries(theme)
            .map(([key, value]) => `  ${key} [${value.join(', ')}];`)
            .join('\n');

        // Inject theme attributes after the opening brace of the graph definition.
        const graphRegex = /(digraph|graph)\s*(\w*\s*)?\{/;
        const match = dotContent.match(graphRegex);
        if (match) {
            const injectionPoint = match.index + match[0].length;
            return dotContent.slice(0, injectionPoint) + '\n' + themeAttributes + '\n' + dotContent.slice(injectionPoint);
        }
        // Fallback for content without explicit graph definition
        return `digraph G {\n${themeAttributes}\n${dotContent}\n}`;
    }

    parseError(stderr) {
        // Example Graphviz error: "Error: :3: syntax error in line 3 near '->'"
        const lineMatch = stderr.match(/line (\d+)/);
        const line = lineMatch ? parseInt(lineMatch[1], 10) : null;
        const message = stderr.split('\n')[0] || 'Graphviz rendering failed.';
        return {
            error: true,
            code: 'SYNTAX_ERROR',
            message: message,
            engine: this.name,
            line: line,
            suggestion: 'Check the DOT syntax, especially around the reported line.'
        };
    }

    async render(content, options) {
        const themedDot = this.applyTheme(content, options.theme);

        const args = [
            '-Tsvg', // Output SVG format
            '-Kcairo' // Use the high-quality Cairo renderer
        ];

        try {
            const { stdout: rawSvg } = await execFileAsync('dot', args, {
                timeout: TIMEOUT,
                maxBuffer: 25 * 1024 * 1024, // 25MB buffer for large diagrams
                input: themedDot,
            });

            const styledSvg = await svgProcessor.process(rawSvg, options.theme, this.name);
            return { format: 'svg', data: Buffer.from(styledSvg) };

        } catch (error) {
            logger.error({ engine: this.name, error: error.stderr || error.message }, 'Graphviz rendering failed');
            if (error.code === 'ETIMEDOUT') {
                throw {
                    error: true,
                    code: 'TIMEOUT',
                    message: `Graphviz rendering timed out after ${TIMEOUT / 1000} seconds.`,
                    engine: this.name,
                    suggestion: 'The diagram is too complex. Try simplifying it.'
                };
            }
            throw this.parseError(error.stderr || error.message);
        }
    }

    async validate(content) {
        // A common way to validate is a "dry run" render to a null format.
        const args = ['-Tps', '-o', '/dev/null'];
        try {
            await execFileAsync('dot', args, {
                timeout: TIMEOUT,
                input: content
            });
            return { valid: true, errors: [] };
        } catch (error) {
            const parsedError = this.parseError(error.stderr || error.message);
            return {
                valid: false,
                errors: [{ line: parsedError.line, message: parsedError.message }]
            };
        }
    }
}

module.exports = new GraphvizEngine();
```

#### `/mnt/projects/ICCM/playfair/engines/mermaid.js`
```javascript
// playfair/engines/mermaid.js
// Adapter for the Mermaid CLI (mmdc) rendering engine.

const { execFile } = require('child_process');
const { promisify } = require('util');
const fs = require('fs/promises');
const path = require('path');
const os = require('os');
const DiagramEngine = require('./base');
const mermaidThemes = require('../themes/mermaid-themes.json');
const svgProcessor = require('../themes/svg-processor');
const logger = require('../utils/logger');

const execFileAsync = promisify(execFile);
const TIMEOUT = parseInt(process.env.RENDER_TIMEOUT_MS, 10) || 60000;

class MermaidEngine extends DiagramEngine {
    constructor() {
        super('mermaid');
    }

    parseError(stderr) {
        // Mermaid CLI errors are typically less structured.
        const message = stderr.split('\n').find(line => line.toLowerCase().includes('error')) || 'Mermaid rendering failed.';
        // It doesn't provide line numbers, so we return null.
        return {
            error: true,
            code: 'SYNTAX_ERROR',
            message: message.trim(),
            engine: this.name,
            line: null,
            suggestion: 'Check the Mermaid syntax for your diagram type (e.g., sequenceDiagram, flowchart).'
        };
    }

    async render(content, options) {
        const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'playfair-mermaid-'));
        const inputFile = path.join(tempDir, 'input.mmd');
        const outputFile = path.join(tempDir, 'output.svg');
        const configFile = path.join(tempDir, 'config.json');

        try {
            // 1. Write content to a temporary file
            await fs.writeFile(inputFile, content);

            // 2. Create theme configuration file
            const themeConfig = mermaidThemes[options.theme] || mermaidThemes.modern;
            await fs.writeFile(configFile, JSON.stringify(themeConfig));

            // 3. Execute Mermaid CLI
            const args = [
                '--input', inputFile,
                '--output', outputFile,
                '--configFile', configFile,
                '--backgroundColor', 'transparent'
            ];
            
            await execFileAsync('mmdc', args, { timeout: TIMEOUT });

            // 4. Read the generated SVG
            const rawSvg = await fs.readFile(outputFile, 'utf8');
            
            // 5. Post-process the SVG for font consistency and theming tweaks
            const styledSvg = await svgProcessor.process(rawSvg, options.theme, this.name);

            return { format: 'svg', data: Buffer.from(styledSvg) };

        } catch (error) {
            logger.error({ engine: this.name, error: error.stderr || error.message }, 'Mermaid rendering failed');
             if (error.code === 'ETIMEDOUT') {
                throw {
                    error: true,
                    code: 'TIMEOUT',
                    message: `Mermaid rendering timed out after ${TIMEOUT / 1000} seconds.`,
                    engine: this.name,
                    suggestion: 'The diagram is too complex. Try simplifying it.'
                };
            }
            throw this.parseError(error.stderr || error.message);
        } finally {
            // 6. Clean up temporary files
            await fs.rm(tempDir, { recursive: true, force: true });
        }
    }

    async validate(content) {
        // Validation is done by attempting a render. There's no separate lint command.
        try {
            await this.render(content, { theme: 'modern' }); // Use a default theme for validation
            return { valid: true, errors: [] };
        } catch (error) {
            // The render method throws a structured error, which we can adapt.
            return {
                valid: false,
                errors: [{ line: error.line, message: error.message }]
            };
        }
    }
}

module.exports = new MermaidEngine();
```

#### `/mnt/projects/ICCM/playfair/themes/graphviz-themes.json`
```json
{
  "professional": {
    "graph": [
      "bgcolor=\"transparent\"",
      "fontname=\"Inter\"",
      "fontsize=12",
      "pad=0.5",
      "rankdir=TB"
    ],
    "node": [
      "shape=box",
      "style=\"rounded,filled\"",
      "fillcolor=\"#E8F4F8\"",
      "color=\"#2E86AB\"",
      "fontname=\"Inter\"",
      "fontsize=11",
      "penwidth=2"
    ],
    "edge": [
      "color=\"#555555\"",
      "penwidth=1.5",
      "fontname=\"Inter\"",
      "fontsize=10"
    ]
  },
  "modern": {
    "graph": [
      "bgcolor=\"transparent\"",
      "fontname=\"Roboto\"",
      "fontsize=12",
      "pad=0.5",
      "splines=ortho"
    ],
    "node": [
      "shape=box",
      "style=\"rounded,filled\"",
      "fillcolor=\"#667EEA\"",
      "color=\"#5A67D8\"",
      "fontcolor=\"white\"",
      "fontname=\"Roboto\"",
      "penwidth=0"
    ],
    "edge": [
      "color=\"#A0AEC0\"",
      "penwidth=2",
      "arrowsize=0.8"
    ]
  },
  "minimal": {
    "graph": [
      "bgcolor=\"transparent\"",
      "fontname=\"Roboto\"",
      "fontsize=12"
    ],
    "node": [
      "shape=box",
      "style=\"filled\"",
      "fillcolor=\"#F7FAFC\"",
      "color=\"#1A202C\"",
      "fontcolor=\"#1A202C\"",
      "fontname=\"Roboto\"",
      "penwidth=2"
    ],
    "edge": [
      "color=\"#2D3748\"",
      "penwidth=1.5"
    ]
  },
  "dark": {
    "graph": [
      "bgcolor=\"transparent\"",
      "fontname=\"Roboto\"",
      "fontcolor=\"#E2E8F0\"",
      "fontsize=12"
    ],
    "node": [
      "shape=box",
      "style=\"rounded,filled\"",
      "fillcolor=\"#2D3748\"",
      "color=\"#4A5568\"",
      "fontcolor=\"#F7FAFC\"",
      "fontname=\"Roboto\"",
      "penwidth=1"
    ],
    "edge": [
      "color=\"#718096\"",
      "fontcolor=\"#E2E8F0\"",
      "penwidth=1.5"
    ]
  }
}
```

#### `/mnt/projects/ICCM/playfair/themes/mermaid-themes.json`
```json
{
  "professional": {
    "theme": "neutral",
    "themeVariables": {
      "primaryColor": "#E8F4F8",
      "primaryTextColor": "#1A202C",
      "primaryBorderColor": "#2E86AB",
      "lineColor": "#555555",
      "fontFamily": "Inter"
    }
  },
  "modern": {
    "theme": "forest",
    "themeVariables": {
      "primaryColor": "#667EEA",
      "primaryTextColor": "#FFFFFF",
      "primaryBorderColor": "#5A67D8",
      "lineColor": "#A0AEC0",
      "fontFamily": "Roboto"
    }
  },
  "minimal": {
    "theme": "default",
    "themeVariables": {
      "primaryColor": "#F7FAFC",
      "primaryTextColor": "#1A202C",
      "primaryBorderColor": "#1A202C",
      "lineColor": "#2D3748",
      "fontFamily": "Roboto"
    }
  },
  "dark": {
    "theme": "dark",
    "themeVariables": {
      "primaryColor": "#2D3748",
      "primaryTextColor": "#F7FAFC",
      "primaryBorderColor": "#4A5568",
      "lineColor": "#718096",
      "fontFamily": "Roboto"
    }
  }
}
```

#### `/mnt/projects/ICCM/playfair/themes/svg-processor.js`
```javascript
// playfair/themes/svg-processor.js
// Handles post-processing of generated SVGs to apply modern aesthetics.

const { optimize } = require('svgo');

// SVGO configuration for optimization
const svgoConfig = {
  plugins: [
    'preset-default',
    'removeDimensions',
    {
      name: 'addAttributesToSVGElement',
      params: {
        attributes: [
          { width: '100%' },
          { height: '100%' }
        ]
      }
    }
  ],
};

// CSS styles for different themes
// These are injected into the SVG to apply fonts, shadows, and gradients.
const themeStyles = {
    modern: `
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        .node > rect, .node > polygon {
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
        }
    `,
    professional: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    `,
    minimal: `
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    `,
    dark: `
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    `
};

// Gradient definitions for the 'modern' theme
const modernGradients = `
    <linearGradient id="modern-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#667EEA;" />
        <stop offset="100%" style="stop-color:#764BA2;" />
    </linearGradient>
`;

class SvgProcessor {
    async process(svgString, theme, engine) {
        let processedSvg = svgString;

        // Apply theme-specific modifications
        if (theme === 'modern' && engine === 'graphviz') {
            // For Graphviz modern theme, replace solid fill with gradient
            processedSvg = this.injectDefs(processedSvg, modernGradients);
            processedSvg = processedSvg.replace(/fill="#667EEA"/g, 'fill="url(#modern-gradient)"');
        }

        // Inject CSS for fonts and effects
        processedSvg = this.injectCss(processedSvg, theme);

        // Optimize the final SVG
        const result = optimize(processedSvg, svgoConfig);
        return result.data;
    }

    injectCss(svgString, theme) {
        const style = themeStyles[theme] || '';
        if (!style) return svgString;

        const styleTag = `<style type="text/css"><
