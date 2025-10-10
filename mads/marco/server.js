#!/usr/bin/env node
/**
 * Marco - Internet Gateway Service for ICCM
 *
 * WebSocket MCP server that bridges Playwright browser automation
 * to multiple clients via a FIFO queue to a single browser instance.
 *
 * Architecture: WebSocket Server → stdio Bridge → Playwright MCP → Chromium
 */

const http = require('http');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const crypto = require('crypto');

// ============================================================================
// Configuration from Environment Variables
// ============================================================================

const CONFIG = {
  port: parseInt(process.env.MARCO_PORT || '8030', 10),
  browserType: process.env.BROWSER_TYPE || 'chromium',
  headless: process.env.HEADLESS !== 'false',
  logLevel: process.env.LOG_LEVEL || 'info',
  maxRestarts: 3,
  restartBackoffMs: 1000,
  healthCheckTimeoutMs: 5000,
  stableRuntimeMs: 10000,
  godotUrl: process.env.GODOT_URL || 'ws://godot-mcp:9060',
  loggingEnabled: true,
};

const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const CURRENT_LOG_LEVEL = LOG_LEVELS[CONFIG.logLevel] || 1;

// ============================================================================
// Godot Logging Integration
// ============================================================================

/**
 * Send log to Godot via MCP logger_log tool
 */
async function logToGodot(level, message, data = null, traceId = null) {
  if (!CONFIG.loggingEnabled) return;

  try {
    const ws = new WebSocket(CONFIG.godotUrl, { handshakeTimeout: 1000 });

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
          component: 'marco',
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
    log('debug', `Godot logging failed: ${err.message}`);
  }
}

// ============================================================================
// Global State
// ============================================================================

let server;
let wss;
let playwrightProcess = null;
let restartAttempts = 0;
let isShuttingDown = false;

const serverStartTime = Date.now();
let lastSubprocessActivity = Date.now();

// Request queue (FIFO)
const requestQueue = [];
let isProcessingQueue = false;

// Pending requests waiting for responses: requestId -> { clientId, resolve, reject, startTime }
const pendingRequests = new Map();

// Connected clients: clientId -> { ws, contexts: Set<contextId> }
const clients = new Map();

// MCP Protocol Layer State
let playwrightToolSchema = [];
let isPlaywrightInitialized = false;

// ============================================================================
// Structured JSON Logger
// ============================================================================

function log(level, message, context = {}) {
  const levelNum = LOG_LEVELS[level] || 0;
  if (levelNum >= CURRENT_LOG_LEVEL) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      service: 'marco',
      message,
      ...context,
    };
    console.log(JSON.stringify(entry));
  }
}

// ============================================================================
// Playwright Subprocess Management
// ============================================================================

function startPlaywrightSubprocess() {
  if (isShuttingDown) {
    return;
  }

  // Reset MCP state on restart
  isPlaywrightInitialized = false;
  playwrightToolSchema = [];

  if (restartAttempts >= CONFIG.maxRestarts) {
    log('error', 'Max restart attempts reached, Playwright subprocess will not restart', {
      restartAttempts,
      maxRestarts: CONFIG.maxRestarts,
    });
    return;
  }

  log('info', 'Starting Playwright MCP subprocess', {
    command: 'npx',
    args: ['@playwright/mcp@0.0.41'],
    attempt: restartAttempts + 1,
    maxAttempts: CONFIG.maxRestarts,
  });

  playwrightProcess = spawn('npx', ['@playwright/mcp@0.0.41'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {
      ...process.env,
      PW_BROWSER_TYPE: CONFIG.browserType,
      PW_HEADLESS: CONFIG.headless ? '1' : '0',
    },
  });

  let stdoutBuffer = '';

  // Handle stdout: parse newline-delimited JSON-RPC messages
  playwrightProcess.stdout.on('data', (data) => {
    lastSubprocessActivity = Date.now();
    stdoutBuffer += data.toString();

    // Process complete messages (newline-delimited)
    let newlineIndex;
    while ((newlineIndex = stdoutBuffer.indexOf('\n')) !== -1) {
      const messageLine = stdoutBuffer.slice(0, newlineIndex).trim();
      stdoutBuffer = stdoutBuffer.slice(newlineIndex + 1);

      if (messageLine) {
        handlePlaywrightMessage(messageLine);
      }
    }
  });

  // Handle stderr
  playwrightProcess.stderr.on('data', (data) => {
    log('warn', 'Playwright subprocess stderr', { data: data.toString().trim() });
  });

  // Initialize Playwright MCP and capture tool schema
  setTimeout(() => {
    if (playwrightProcess && !playwrightProcess.killed) {
      // Send tools/list to capture available tools
      const toolsListRequest = {
        jsonrpc: '2.0',
        id: 'marco_init_tools_list',
        method: 'tools/list',
        params: {},
      };
      playwrightProcess.stdin.write(JSON.stringify(toolsListRequest) + '\n');
      log('debug', 'Sent tools/list to Playwright subprocess for initialization');
    }
  }, 1000); // Wait 1s for subprocess to be ready

  // Handle process exit
  playwrightProcess.on('exit', (code, signal) => {
    log('warn', 'Playwright subprocess exited', { code, signal, restartAttempts });
    playwrightProcess = null;

    // Reject all pending requests
    pendingRequests.forEach(({ reject, clientId }) => {
      reject(new Error('Playwright subprocess terminated'));
    });
    pendingRequests.clear();

    // Attempt restart with exponential backoff
    if (!isShuttingDown && restartAttempts < CONFIG.maxRestarts) {
      restartAttempts++;
      const delay = CONFIG.restartBackoffMs * Math.pow(2, restartAttempts - 1);
      log('info', 'Scheduling Playwright subprocess restart', { delay, attempt: restartAttempts });
      setTimeout(startPlaywrightSubprocess, delay);
    }
  });

  playwrightProcess.on('error', (err) => {
    log('error', 'Failed to spawn Playwright subprocess', { error: err.message });
  });

  // Reset restart attempts after stable operation
  setTimeout(() => {
    if (playwrightProcess && !playwrightProcess.killed) {
      log('info', 'Playwright subprocess stable, resetting restart counter');
      restartAttempts = 0;
    }
  }, CONFIG.stableRuntimeMs);
}

// ============================================================================
// Playwright Message Handling
// ============================================================================

function handlePlaywrightMessage(messageLine) {
  let message;
  try {
    message = JSON.parse(messageLine);
  } catch (err) {
    log('error', 'Failed to parse Playwright message', { messageLine, error: err.message });
    return;
  }

  log('debug', 'Received message from Playwright subprocess', { message });

  // Handle initialization tools/list response
  if (message.id === 'marco_init_tools_list') {
    if (message.result && message.result.tools) {
      playwrightToolSchema = message.result.tools;
      isPlaywrightInitialized = true;
      log('info', 'Playwright MCP initialized and tools schema captured', { toolCount: playwrightToolSchema.length });
    } else if (message.error) {
      log('error', 'Failed to get tools from Playwright', { error: message.error });
    }
    return;
  }

  // Handle responses (have an id)
  if (message.id !== undefined && message.id !== null) {
    const pending = pendingRequests.get(message.id);
    if (pending) {
      const { clientId, resolve, startTime, method } = pending;
      pendingRequests.delete(message.id);

      // Get client object
      const client = clients.get(clientId);

      // Track context creation (CRITICAL FIX: Gemini/DeepSeek/GPT-4o-mini consensus)
      if (client && method === 'browser.newContext' && message.result && message.result.guid) {
        client.contexts.add(message.result.guid);
        log('debug', 'Tracking new context for client', { clientId, contextId: message.result.guid });
      }

      // Send response to client
      if (client && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify(message));

        // Log tool invocation completion (with tool name)
        const duration = Date.now() - startTime;
        log('info', 'Tool invocation completed', {
          event: 'tool_invocation',
          tool_name: method,
          client_id: clientId,
          duration_ms: duration,
          status: message.error ? 'error' : 'success',
        });
        logToGodot('TRACE', 'Tool call completed', {
          client_id: clientId,
          tool_name: method,
          success: !message.error,
          duration_ms: duration
        });
      }

      resolve();
      processNextRequest(); // Process next queued request
    } else {
      log('debug', 'Received response for unknown request ID (possibly cleanup request)', { id: message.id });
    }
  }
  // Handle requests from subprocess (not expected in Phase 1)
  else if (message.method) {
    log('warn', 'Received unexpected request from subprocess', { message });
    const errorResponse = {
      jsonrpc: '2.0',
      id: message.id,
      error: {
        code: -32601,
        message: 'Method not supported in multiplexed mode',
      },
    };
    if (playwrightProcess && !playwrightProcess.killed) {
      playwrightProcess.stdin.write(JSON.stringify(errorResponse) + '\n');
    }
  }
  // Handle notifications (no id)
  else {
    // Intercept initialization notification from Playwright to capture tool schema
    if (message.method === 'notifications/initialized' && message.params && message.params.tools) {
      playwrightToolSchema = message.params.tools;
      isPlaywrightInitialized = true;
      log('info', 'Playwright MCP initialized and tools schema captured', { toolCount: playwrightToolSchema.length });
      // Do not broadcast this internal notification to clients
      return;
    }

    log('debug', 'Broadcasting notification to all clients', { notification: message });
    wss.clients.forEach((ws) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
      }
    });
  }
}

// ============================================================================
// FIFO Request Queue Processing
// ============================================================================

function processNextRequest() {
  if (isProcessingQueue || requestQueue.length === 0 || !playwrightProcess || playwrightProcess.killed) {
    isProcessingQueue = false;
    return;
  }

  isProcessingQueue = true;
  const { clientId, request } = requestQueue.shift();

  // Check if client is still connected
  const client = clients.get(clientId);
  if (!client || client.ws.readyState !== WebSocket.OPEN) {
    log('debug', 'Skipping request from disconnected client', { clientId, requestId: request.id });
    isProcessingQueue = false;
    processNextRequest();
    return;
  }

  try {
    const requestId = request.id;
    const startTime = Date.now();

    // Track context creation: wrap resolve to capture context ID
    let resolve = () => {};
    let reject = (err) => {
      log('error', 'Request failed', { clientId, requestId, error: err.message });
      if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify({
          jsonrpc: '2.0',
          id: requestId,
          error: {
            code: -32603,
            message: 'Internal error',
            data: { originalError: err.message },
          },
        }));
      }
    };

    // Intercept browser.newContext to track created contexts
    if (request.method === 'browser.newContext') {
      const originalResolve = resolve;
      resolve = () => {
        // Context ID will be in the response, handled when we receive it
        originalResolve();
      };
    }

    // Store pending request with method for context tracking
    if (requestId !== undefined && requestId !== null) {
      pendingRequests.set(requestId, { clientId, resolve, reject, startTime, method: request.method });
    }

    // Send to Playwright subprocess
    const requestStr = JSON.stringify(request);
    log('debug', 'Sending request to Playwright subprocess', {
      clientId,
      requestId,
      method: request.method,
    });

    playwrightProcess.stdin.write(requestStr + '\n');
  } catch (err) {
    log('error', 'Failed to process request', { error: err.message, request });
    isProcessingQueue = false;
    processNextRequest();
  }
}

function enqueueRequest(clientId, request) {
  requestQueue.push({ clientId, request });
  log('debug', 'Request enqueued', {
    clientId,
    requestId: request.id,
    method: request.method,
    queueLength: requestQueue.length,
  });

  if (!isProcessingQueue) {
    processNextRequest();
  }
}

// ============================================================================
// MCP Protocol Layer
// ============================================================================

function handleClientRequest(clientId, ws, request) {
  const { method, params, id } = request;

  log('debug', 'Processing client request via MCP layer', { clientId, method });
  logToGodot('TRACE', 'MCP request received', { client_id: clientId, method, id });

  // 1. Handle MCP 'initialize'
  if (method === 'initialize') {
    const response = {
      jsonrpc: '2.0',
      id,
      result: {
        protocolVersion: '2024-11-05',
        serverInfo: { name: 'marco', version: '1.0.0' },
        capabilities: { tools: {} },
      },
    };
    ws.send(JSON.stringify(response));
    // NOTE: Server does NOT send notifications/initialized - that's sent BY the client TO the server
    // The server only responds to the initialize request
    return;
  }

  // 2. Handle MCP 'tools/list'
  if (method === 'tools/list') {
    if (!isPlaywrightInitialized) {
      ws.send(JSON.stringify({
        jsonrpc: '2.0',
        id,
        error: { code: -32000, message: 'Server not ready: Playwright tools not yet available.' },
      }));
      return;
    }
    const response = {
      jsonrpc: '2.0',
      id,
      result: {
        tools: playwrightToolSchema,
      },
    };
    ws.send(JSON.stringify(response));
    return;
  }

  // 3. Handle MCP 'tools/call'
  if (method === 'tools/call') {
    const { name, arguments: args } = params || {};
    if (!name) {
      ws.send(JSON.stringify({
        jsonrpc: '2.0',
        id,
        error: { code: -32602, message: "Invalid params for 'tools/call': missing 'name'." },
      }));
      return;
    }

    logToGodot('TRACE', 'Tool call started', { client_id: clientId, tool_name: name, has_args: !!args });

    // Transform the MCP request into a direct JSON-RPC request for Playwright
    const playwrightRequest = {
      jsonrpc: '2.0',
      id, // Pass through the original ID for response correlation
      method: name,
      params: args || {},
    };

    // Enqueue the transformed request for the Playwright subprocess
    enqueueRequest(clientId, playwrightRequest);
    return;
  }

  // 4. Handle client's `notifications/initialized` (just log and ignore)
  if (method === 'notifications/initialized') {
    log('debug', 'Client acknowledged initialization', { clientId });
    return;
  }

  // 5. Reject any other methods
  log('warn', 'Unsupported method received', { clientId, method });
  ws.send(JSON.stringify({
    jsonrpc: '2.0',
    id,
    error: {
      code: -32601,
      message: `Method not found: '${method}'. Use 'tools/call' to invoke browser methods.`,
    },
  }));
}

// ============================================================================
// WebSocket Connection Handling
// ============================================================================

function handleClientConnection(ws) {
  const clientId = crypto.randomUUID();
  clients.set(clientId, { ws, contexts: new Set() });

  log('info', 'Client connected', { clientId, totalClients: clients.size });
  logToGodot('INFO', 'Client connected', { client_id: clientId, total_clients: clients.size });

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      log('debug', 'Received message from client', { clientId, message });

      // Route request through the MCP protocol layer
      handleClientRequest(clientId, ws, message);
    } catch (err) {
      log('error', 'Failed to parse client message', { clientId, error: err.message });
      logToGodot('ERROR', 'Invalid JSON message received', { client_id: clientId, error: err.message });
      ws.send(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: {
          code: -32700,
          message: 'Parse error',
          data: { originalError: err.message },
        },
      }));
    }
  });

  ws.on('close', () => {
    cleanupClient(clientId);
  });

  ws.on('error', (err) => {
    log('error', 'WebSocket error', { clientId, error: err.message });
  });
}

function cleanupClient(clientId) {
  const client = clients.get(clientId);
  if (!client) return;

  log('info', 'Client disconnected, cleaning up contexts', {
    clientId,
    contextsToCleanup: client.contexts.size,
    totalClients: clients.size - 1,
  });

  // Queue context dispose requests for cleanup (best effort)
  // NOTE: Playwright MCP uses 'context.dispose' not 'context.close'
  client.contexts.forEach((contextId) => {
    const disposeRequest = {
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'context.dispose',
      params: { guid: contextId },
    };

    // Enqueue cleanup request (no response tracking)
    requestQueue.push({ clientId, request: disposeRequest });
  });

  clients.delete(clientId);

  // Trigger queue processing if cleanup requests were added
  if (client.contexts.size > 0 && !isProcessingQueue) {
    processNextRequest();
  }
}

// ============================================================================
// Health Check Endpoint
// ============================================================================

function handleHealthCheck(req, res) {
  const uptime = (Date.now() - serverStartTime) / 1000;
  const isSubprocessAlive = playwrightProcess !== null && !playwrightProcess.killed;
  const timeSinceLastActivity = Date.now() - lastSubprocessActivity;
  const isSubprocessResponsive = isSubprocessAlive && timeSinceLastActivity < CONFIG.healthCheckTimeoutMs;

  const status = isSubprocessAlive && isSubprocessResponsive ? 'healthy' : 'degraded';
  const httpStatus = status === 'healthy' ? 200 : 503;

  const health = {
    status,
    browser: isSubprocessAlive ? 'alive' : 'dead',
    uptime_seconds: parseFloat(uptime.toFixed(2)),
    playwright_subprocess: isSubprocessResponsive ? 'responsive' : 'unresponsive',
  };

  res.writeHead(httpStatus, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(health));

  log('debug', 'Health check', { health, httpStatus });
}

// ============================================================================
// HTTP and WebSocket Server Setup
// ============================================================================

// Create HTTP server for health check
server = http.createServer((req, res) => {
  if (req.url === '/health' && req.method === 'GET') {
    handleHealthCheck(req, res);
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

// Create WebSocket server (no separate HTTP server)
wss = new WebSocket.Server({ noServer: true });

// Handle WebSocket upgrade on same port as HTTP
server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

wss.on('connection', handleClientConnection);

// ============================================================================
// Graceful Shutdown
// ============================================================================

function gracefulShutdown(signal) {
  if (isShuttingDown) return;
  isShuttingDown = true;

  log('info', 'Graceful shutdown initiated', { signal });

  // Close all WebSocket connections
  wss.clients.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });

  // Close WebSocket server
  wss.close(() => {
    log('info', 'WebSocket server closed');
  });

  // Close HTTP server
  server.close(() => {
    log('info', 'HTTP server closed');

    // Terminate Playwright subprocess
    if (playwrightProcess) {
      log('info', 'Terminating Playwright subprocess');
      playwrightProcess.kill('SIGTERM');

      // Force kill after timeout
      setTimeout(() => {
        if (playwrightProcess && !playwrightProcess.killed) {
          log('warn', 'Force killing Playwright subprocess');
          playwrightProcess.kill('SIGKILL');
        }
        process.exit(0);
      }, 2000);
    } else {
      process.exit(0);
    }
  });

  // Force exit after timeout
  setTimeout(() => {
    log('error', 'Graceful shutdown timeout, forcing exit');
    process.exit(1);
  }, 5000);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// ============================================================================
// Application Startup
// ============================================================================

server.listen(CONFIG.port, () => {
  log('info', 'Marco server started', {
    port: CONFIG.port,
    browserType: CONFIG.browserType,
    headless: CONFIG.headless,
    logLevel: CONFIG.logLevel,
  });

  startPlaywrightSubprocess();
});
