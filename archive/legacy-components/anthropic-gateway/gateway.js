#!/usr/bin/env node

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 8089;
const UPSTREAM_URL = process.env.UPSTREAM_URL || 'https://api.anthropic.com';
const DEWEY_URL = process.env.DEWEY_URL || 'http://192.168.1.210:8080/conversations';
const REDACT_API_KEYS = process.env.REDACT_API_KEYS !== 'false';

console.log('[Gateway] Starting Anthropic API Gateway');
console.log('[Gateway] Upstream:', UPSTREAM_URL);
console.log('[Gateway] Dewey:', DEWEY_URL);
console.log('[Gateway] Redact API Keys:', REDACT_API_KEYS);

// Middleware to capture and log request/response
const loggingMiddleware = createProxyMiddleware({
  target: UPSTREAM_URL,
  changeOrigin: true,

  // Intercept and log request
  onProxyReq: (proxyReq, req, res) => {
    const requestId = uuidv4();
    req.requestId = requestId;
    req.requestStart = Date.now();

    // Capture request body if present
    let requestBody = '';
    if (req.body) {
      requestBody = JSON.stringify(req.body);
      proxyReq.setHeader('Content-Length', Buffer.byteLength(requestBody));
      proxyReq.write(requestBody);
    }

    // Store for logging
    req.capturedRequest = {
      requestId,
      method: req.method,
      path: req.path,
      headers: sanitizeHeaders(req.headers),
      body: requestBody ? JSON.parse(requestBody) : null,
      timestamp: new Date().toISOString()
    };

    console.log(`[Gateway] ${requestId} -> ${req.method} ${req.path}`);
  },

  // Intercept and log response
  onProxyRes: (proxyRes, req, res) => {
    const chunks = [];

    proxyRes.on('data', (chunk) => {
      chunks.push(chunk);
    });

    proxyRes.on('end', async () => {
      const responseBody = Buffer.concat(chunks).toString('utf8');
      const duration = Date.now() - req.requestStart;

      const logEntry = {
        requestId: req.requestId,
        request: req.capturedRequest,
        response: {
          status: proxyRes.statusCode,
          headers: sanitizeHeaders(proxyRes.headers),
          body: responseBody ? tryParseJSON(responseBody) : null,
          timestamp: new Date().toISOString()
        },
        duration_ms: duration,
        source: 'anthropic-gateway',
        client: 'claude-code-container'
      };

      console.log(`[Gateway] ${req.requestId} <- ${proxyRes.statusCode} (${duration}ms)`);

      // Send to Dewey asynchronously (don't block response)
      logToDewey(logEntry).catch(err => {
        console.error('[Gateway] Failed to log to Dewey:', err.message);
      });
    });
  },

  onError: (err, req, res) => {
    console.error('[Gateway] Proxy error:', err.message);
    res.status(500).json({
      error: 'Gateway Error',
      message: err.message,
      requestId: req.requestId
    });
  }
});

// Parse JSON bodies
app.use(express.json({ limit: '50mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    upstream: UPSTREAM_URL,
    dewey: DEWEY_URL
  });
});

// All other requests go through proxy with logging
app.use('/', loggingMiddleware);

// Helper: Sanitize headers (redact API keys)
function sanitizeHeaders(headers) {
  const sanitized = { ...headers };

  if (REDACT_API_KEYS) {
    const sensitiveHeaders = ['x-api-key', 'authorization', 'cookie', 'set-cookie'];

    for (const key of sensitiveHeaders) {
      if (sanitized[key]) {
        sanitized[key] = '[REDACTED]';
      }
    }
  }

  return sanitized;
}

// Helper: Try to parse JSON, return raw on failure
function tryParseJSON(str) {
  try {
    return JSON.parse(str);
  } catch {
    return str;
  }
}

// Helper: Log to Dewey
async function logToDewey(logEntry) {
  try {
    const response = await fetch(DEWEY_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        metadata: {
          source: 'anthropic-gateway',
          request_id: logEntry.requestId,
          client: 'claude-code-container',
          duration_ms: logEntry.duration_ms
        },
        messages: [
          {
            role: 'user',
            content: JSON.stringify(logEntry.request.body || {}),
            metadata: {
              type: 'request',
              path: logEntry.request.path,
              method: logEntry.request.method
            }
          },
          {
            role: 'assistant',
            content: JSON.stringify(logEntry.response.body || {}),
            metadata: {
              type: 'response',
              status: logEntry.response.status,
              duration_ms: logEntry.duration_ms
            }
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`Dewey returned ${response.status}: ${await response.text()}`);
    }

    console.log(`[Gateway] ${logEntry.requestId} logged to Dewey`);
  } catch (error) {
    // Don't fail the request if logging fails
    console.error('[Gateway] Dewey logging error:', error.message);
  }
}

// Start server
app.listen(PORT, () => {
  console.log(`[Gateway] Listening on port ${PORT}`);
  console.log(`[Gateway] Ready to proxy requests to ${UPSTREAM_URL}`);
});
