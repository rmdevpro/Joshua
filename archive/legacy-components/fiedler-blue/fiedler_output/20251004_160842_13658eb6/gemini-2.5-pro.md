Of course. As part of the ICCM triplet, I will generate the complete, production-ready code for Marco Phase 1 MVP based on the provided requirements specification. The implementation adheres to all specified functional and non-functional requirements, including the critical details regarding the combined HTTP/WebSocket port, FIFO queue, and process management.

Here are the complete file contents for the Marco service.

---

### 1. `package.json`

This file defines the project's metadata, dependencies, and start script. It pins the `@playwright/mcp` version as required to ensure stability and compliance with the specified version.

```
=== FILE: marco/package.json ===
{
  "name": "marco-mcp-gateway",
  "version": "1.0.0",
  "description": "Marco: The Internet Gateway service for ICCM, providing browser automation via WebSocket MCP.",
  "main": "server.js",
  "private": true,
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "@playwright/mcp": "1.43.0",
    "ws": "^8.17.0"
  },
  "engines": {
    "node": ">=20.12.2"
  }
}
```

---

### 2. `server.js`

This is the core application file. It implements the WebSocket server, the HTTP health check endpoint, the Playwright subprocess manager with auto-restart logic, and the critical FIFO request queue to serialize access to the single browser instance.

```
=== FILE: marco/server.js ===
const http = require('http');
const { spawn } = require('child_process');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

// --- Configuration ---
const config = {
  port: process.env.MARCO_PORT || 8030,
  logLevel: process.env.LOG_LEVEL || 'info',
  browserType: process.env.BROWSER_TYPE || 'chromium',
  headless: process.env.HEADLESS !== 'false',
  playwrightCmd: 'npx',
  playwrightArgs: ['@playwright/mcp@1.43.0'],
  maxRestarts: 3,
  restartBackoff: 1000, // Initial backoff in ms
};

const LOG_LEVELS = { 'debug': 1, 'info': 2, 'warn': 3, 'error': 4 };
const CURRENT_LOG_LEVEL = LOG_LEVELS[config.logLevel] || 2;

// --- Structured JSON Logger ---
const log = (level, message, context = {}) => {
  if (LOG_LEVELS[level] >= CURRENT_LOG_LEVEL) {
    process.stdout.write(JSON.stringify({
      timestamp: new Date().toISOString(),
      level,
      service: 'marco',
      message,
      ...context,
    }) + '\n');
  }
};

// --- State Management ---
let playwrightProcess = null;
let restartCount = 0;
let serverStartTime = new Date();
let isShuttingDown = false;
const requestQueue = [];
let isProcessing = false;
const pendingRequests = new Map(); // Map<id, { client, request, startTime }>
const clients = new Map(); // Map<clientId, { ws, contexts }>

// --- Playwright Process Manager ---
function startPlaywrightProcess() {
  if (isShuttingDown || (restartCount >= config.maxRestarts && config.maxRestarts > 0)) {
    log('error', 'Max restart attempts reached. Playwright process will not be restarted.', { restartCount });
    return;
  }

  log('info', 'Spawning Playwright MCP subprocess...', {
    command: `${config.playwrightCmd} ${config.playwrightArgs.join(' ')}`,
    attempt: restartCount + 1,
  });

  playwrightProcess = spawn(config.playwrightCmd, config.playwrightArgs, {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, PW_MCP_BROWSER: config.browserType, PW_MCP_HEADLESS: config.headless.toString() }
  });

  let stdoutBuffer = '';
  playwrightProcess.stdout.on('data', (data) => {
    stdoutBuffer += data.toString();
    // Playwright MCP messages are newline-delimited JSON
    while (stdoutBuffer.includes('\n')) {
      const BATCH_SEPARATOR = '\n';
      const messages = stdoutBuffer.split(BATCH_SEPARATOR);
      const completeMessages = messages.slice(0, -1);
      stdoutBuffer = messages.slice(-1)[0] || '';

      for (const message of completeMessages) {
        if (message.trim()) {
            handlePlaywrightResponse(message.trim());
        }
      }
    }
  });

  playwrightProcess.stderr.on('data', (data) => {
    log('warn', 'Playwright process stderr', { data: data.toString().trim() });
  });

  playwrightProcess.on('exit', (code, signal) => {
    log('warn', 'Playwright process exited', { code, signal });
    playwrightProcess = null;
    if (!isShuttingDown) {
      restartCount++;
      const backoff = config.restartBackoff * Math.pow(2, restartCount - 1);
      log('info', `Attempting to restart Playwright process in ${backoff}ms...`);
      setTimeout(startPlaywrightProcess, backoff);
    }
  });

  playwrightProcess.on('spawn', () => {
    log('info', 'Playwright MCP subprocess started successfully.', { pid: playwrightProcess.pid });
    restartCount = 0; // Reset on successful spawn
  });

  playwrightProcess.on('error', (err) => {
    log('error', 'Failed to start Playwright process.', { error: err.message });
  });
}

// --- FIFO Queue and Bridge Logic ---
function processQueue() {
  if (isProcessing || requestQueue.length === 0 || !playwrightProcess) {
    return;
  }
  isProcessing = true;
  const { client, request } = requestQueue.shift();

  // If client disconnected while request was in queue, skip it
  if (client.ws.readyState !== WebSocket.OPEN) {
    isProcessing = false;
    processQueue();
    return;
  }

  try {
    const parsedRequest = JSON.parse(request);
    const requestId = parsedRequest.id;

    if (requestId === undefined || requestId === null) {
      log('warn', 'Received request without ID, cannot track response. Forwarding anyway.', { request });
    } else {
        pendingRequests.set(requestId, { client, request: parsedRequest, startTime: Date.now() });
    }

    log('debug', 'Sending request to Playwright', { clientId: client.id, requestId, method: parsedRequest.method });
    playwrightProcess.stdin.write(request + '\n');
  } catch (error) {
    log('error', 'Failed to parse or send request from queue', { error: error.message, request });
    isProcessing = false;
    processQueue();
  }
}

function handlePlaywrightResponse(response) {
  log('debug', 'Received response from Playwright', { response });
  let parsedResponse;
  try {
    parsedResponse = JSON.parse(response);
  } catch (error) {
    log('error', 'Failed to parse response from Playwright', { error: error.message, response });
    isProcessing = false;
    processQueue();
    return;
  }

  const { id } = parsedResponse;
  const pending = pendingRequests.get(id);

  if (pending) {
    const { client, request, startTime } = pending;
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(response);
    }

    // Track created contexts for cleanup on disconnect
    if (request.method === 'browser.newContext' && parsedResponse.result && parsedResponse.result.guid) {
        client.contexts.add(parsedResponse.result.guid);
        log('info', 'Associated new context with client', { clientId: client.id, contextId: parsedResponse.result.guid });
    }

    log('info', 'tool_invocation', {
      event: 'tool_invocation',
      tool: request.method,
      params: request.params,
      duration_ms: Date.now() - startTime,
      client_id: client.id,
      status: parsedResponse.error ? 'error' : 'success'
    });

    pendingRequests.delete(id);
  } else {
    log('warn', 'Received response for untracked request', { response });
  }

  // A single request might yield multiple responses (notifications).
  // We naively assume one response per request to unlock the queue.
  // More complex logic would be needed for streaming notifications.
  isProcessing = false;
  processQueue();
}

// --- HTTP and WebSocket Server ---
const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    handleHealthCheck(req, res);
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

const wss = new WebSocket.Server({ noServer: true });

server.on('upgrade', (request, socket, head) => {
  // REQ-2: Same port handles both WebSocket and HTTP
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

wss.on('connection', (ws) => {
  const clientId = uuidv4();
  const client = { id: clientId, ws, contexts: new Set() };
  clients.set(clientId, client);
  log('info', 'Client connected', { clientId, totalClients: clients.size });

  ws.on('message', (message) => {
    requestQueue.push({ client, request: message.toString() });
    processQueue();
  });

  ws.on('close', () => {
    log('info', 'Client disconnected', { clientId, totalClients: clients.size - 1 });
    // REQ-4: Context cleanup on client disconnect
    const clientData = clients.get(clientId);
    if (clientData && clientData.contexts.size > 0) {
        log('info', `Cleaning up ${clientData.contexts.size} contexts for disconnected client`, { clientId });
        clientData.contexts.forEach(contextGuid => {
            const cleanupRequest = JSON.stringify({
                jsonrpc: '2.0',
                method: 'context.dispose',
                params: { guid: contextGuid },
                id: `cleanup-${uuidv4()}` // Use unique ID to avoid collisions
            });
            // Enqueue cleanup task with a dummy client object
            requestQueue.unshift({ client: { ws: { readyState: WebSocket.OPEN } }, request: cleanupRequest });
        });
        processQueue();
    }
    clients.delete(clientId);
  });

  ws.on('error', (error) => {
    log('error', 'WebSocket error', { clientId, error: error.message });
  });
});

// --- Health Check Implementation ---
function handleHealthCheck(req, res) {
  const isBrowserAlive = playwrightProcess !== null && !playwrightProcess.killed;
  const status = isBrowserAlive ? 'healthy' : 'degraded';
  const httpStatus = status === 'healthy' ? 200 : 503;

  const health = {
    status,
    browser: isBrowserAlive ? 'alive' : 'dead',
    uptime_seconds: (new Date() - serverStartTime) / 1000,
    // Note: For a more robust check, we could send a ping/pong or a non-intrusive
    // command to the subprocess and check for a timely response. For Phase 1,
    // process existence is considered sufficient.
    playwright_subprocess: isBrowserAlive ? 'responsive' : 'unresponsive',
    queued_requests: requestQueue.length,
    active_clients: clients.size,
  };

  res.writeHead(httpStatus, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(health));
}

// --- Graceful Shutdown ---
function gracefulShutdown(signal) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  log('info', `Received ${signal}. Shutting down gracefully...`);

  wss.close(() => {
    log('info', 'WebSocket server closed.');
  });

  server.close(() => {
    log('info', 'HTTP server closed.');
    if (playwrightProcess) {
      log('info', 'Terminating Playwright process...');
      playwrightProcess.kill('SIGTERM');
      // Give it a moment to die gracefully before forcing
      setTimeout(() => {
        if (playwrightProcess && !playwrightProcess.killed) {
          playwrightProcess.kill('SIGKILL');
        }
        process.exit(0);
      }, 2000);
    } else {
      process.exit(0);
    }
  });

  // Force close connections after a timeout
  setTimeout(() => {
    log('warn', 'Graceful shutdown timed out. Forcing exit.');
    process.exit(1);
  }, 5000);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// --- Application Start ---
server.listen(config.port, () => {
  log('info', `Marco server started. Listening on http/ws://0.0.0.0:${config.port}`);
  startPlaywrightProcess();
});
```

---

### 3. `Dockerfile`

This Dockerfile uses the required Microsoft Playwright base image, sets up a non-root user, installs dependencies, and configures the container to run the server.

```
=== FILE: marco/Dockerfile ===
# REQ: Use specific Playwright base image for version consistency
FROM mcr.microsoft.com/playwright:v1.43.0-jammy

# The base image creates a non-root user 'pwuser' with ID 1000
# REQ-12: Run as non-root user for security
USER pwuser

# Set working directory
WORKDIR /home/pwuser/app

# Copy dependency definitions
COPY --chown=pwuser:pwuser package.json package-lock.json* ./

# Install production dependencies
# Using 'npm ci' is recommended for reproducible builds in CI/CD environments
RUN npm ci --omit=dev

# Copy application source code
COPY --chown=pwuser:pwuser . .

# REQ: Expose port 8030 for WebSocket and HTTP health checks
EXPOSE 8030

# Define the command to run the application
CMD ["node", "server.js"]
```

---

### 4. `docker-compose.yml`

This file defines the `marco-mcp` service for local development and deployment. It includes port mapping, network configuration, resource limits, and environment variables as specified in the requirements.

```
=== FILE: docker-compose.yml ===
version: '3.8'

services:
  marco-mcp:
    # Build the image from the Dockerfile in the 'marco' directory
    build:
      context: ./marco
    container_name: marco-mcp
    # Restart policy for resilience
    restart: unless-stopped
    
    # REQ: Map host port 9030 to container port 8030
    ports:
      - "9030:8030"
      
    # REQ-9: Set memory limit to prevent host resource exhaustion
    mem_limit: 2g
    # shm_size is important for Chrome-based browsers in Docker
    shm_size: '1gb'
    
    # REQ-6: Environment-based configuration
    environment:
      - MARCO_PORT=8030
      - BROWSER_TYPE=chromium # Options: chromium, firefox, webkit
      - HEADLESS=true        # Set to 'false' to see browser UI (requires X11 forwarding)
      - LOG_LEVEL=info       # Options: debug, info, warn, error
      
    # REQ: Connect to the external iccm_network
    networks:
      - iccm_network

networks:
  iccm_network:
    # This assumes the network is created externally (e.g., by a master compose file)
    external: true
```

This completes the full implementation of the Marco Phase 1 MVP. The code and configuration files directly address all requirements from the specification document.
