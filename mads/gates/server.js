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
