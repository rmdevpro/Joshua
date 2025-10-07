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
                    name: 'Playfair',
                    version: '1.0.0',
                    description: 'ICCM Diagram Generation Gateway',
                    capabilities: ['tools'],
                    protocol_version: '1.0'
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
});