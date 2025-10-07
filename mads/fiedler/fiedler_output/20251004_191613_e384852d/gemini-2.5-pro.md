Of course. Based on your detailed analysis, the core issue is the lack of an MCP protocol layer in Marco. It's acting as a transparent proxy instead of an intelligent gateway.

I will provide a specific implementation plan and the corresponding code changes for `server.js` to correctly implement the MCP layer. This solution will handle the protocol methods at the Marco level and only forward valid tool invocations to the Playwright subprocess, all while preserving your existing queue and context management logic.

### Implementation Approach

1.  **Introduce State for Playwright Tools:** We'll add a global variable, `playwrightToolSchema`, to store the list of tools provided by the Playwright subprocess. We also need a flag, `isPlaywrightInitialized`, to track its readiness.

2.  **Capture Playwright's Tool Schema:** We will modify `handlePlaywrightMessage` to intercept the `notifications/initialized` message that `@playwright/mcp` sends on startup. This message contains the tool schema we need to cache.

3.  **Implement the MCP Request Router:** We'll create a new function, `handleClientRequest`, that will act as the MCP protocol layer. This function will be called for every incoming message from a client.
    *   If the method is `initialize`, it will respond directly with Marco's capabilities.
    *   If the method is `tools/list`, it will respond directly with the cached `playwrightToolSchema`.
    *   If the method is `tools/call`, it will transform the request into a standard JSON-RPC call (e.g., `{ "method": "browser.newContext", ... }`) and pass it to the existing `enqueueRequest` function.
    *   It will gracefully handle the client's `notifications/initialized`.
    *   Any other method will be rejected as unsupported.

4.  **Integrate the Router:** We will update the WebSocket `'message'` event handler to call our new `handleClientRequest` router instead of blindly calling `enqueueRequest`.

This approach satisfies all your requirements with minimal disruption to the existing, working parts of the server.

---

### Code Changes for `server.js`

Here are the specific changes to apply to your `/mnt/projects/ICCM/marco/server.js` file.

**1. Add New Global State Variables**

Add these variables in the `Global State` section, around line 45.

```javascript
// ============================================================================
// Global State
// ============================================================================

// ... existing state variables ...

// MCP Protocol Layer State
let playwrightToolSchema = [];
let isPlaywrightInitialized = false;
```

**2. Reset State on Subprocess Restart**

In `startPlaywrightSubprocess()`, reset the new state variables to handle restarts correctly.

```javascript
function startPlaywrightSubprocess() {
  if (isShuttingDown) {
    return;
  }

  // Reset MCP state on restart
  isPlaywrightInitialized = false;
  playwrightToolSchema = [];

  if (restartAttempts >= CONFIG.maxRestarts) {
    // ... rest of the function ...
```

**3. Capture Tool Schema in `handlePlaywrightMessage`**

Modify the `else` block at the end of `handlePlaywrightMessage` to specifically capture the `notifications/initialized` from Playwright.

```javascript
// ... inside handlePlaywrightMessage, around line 200 ...
  }
  // Handle notifications (no id)
  else {
    // Intercept initialization notification from Playwright to capture tool schema
    if (message.method === 'notifications/initialized' && message.params && message.params.tools) {
      playwrightToolSchema = message.params.tools;
      isPlaywrightInitialized = true;
      log('info', 'Playwright MCP initialized and tools schema captured', { toolCount: playwrightToolSchema.length });
      // Do not broadcast this internal notification to clients.
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
```

**4. Create the MCP Request Router Function**

Add this new function, `handleClientRequest`, which will contain the core MCP logic. This can go right before the `WebSocket Connection Handling` section.

```javascript
// ============================================================================
// MCP Protocol Layer (NEW)
// ============================================================================

function handleClientRequest(clientId, ws, request) {
  const { method, params, id } = request;

  log('debug', 'Processing client request via MCP layer', { clientId, method });

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

    // Per MCP spec, server sends `notifications/initialized` after client initializes
    const notification = {
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    };
    ws.send(JSON.stringify(notification));
    return;
  }

  // 2. Handle MCP 'tools/list'
  if (method === 'tools/list') {
    if (!isPlaywrightInitialized) {
        ws.send(JSON.stringify({
            jsonrpc: '2.0', id, error: { code: -32000, message: 'Server not ready: Playwright tools not yet available.' }
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
        jsonrpc: '2.0', id, error: { code: -32602, message: "Invalid params for 'tools/call': missing 'name'." }
      }));
      return;
    }

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
```

**5. Update the WebSocket Message Handler**

Finally, modify `handleClientConnection` to use the new `handleClientRequest` router.

```javascript
// ... inside handleClientConnection, around line 345 ...

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      log('debug', 'Received message from client', { clientId, message });

      // Route request through the MCP protocol layer (MODIFIED)
      handleClientRequest(clientId, ws, message);

    } catch (err) {
      log('error', 'Failed to parse client message', { clientId, error: err.message });
      // ... rest of the error handling ...
```

With these changes, Marco will now correctly function as an MCP gateway, fixing the critical design flaw and preventing the relay from crashing. It properly separates protocol-level concerns from the underlying tool execution, which is forwarded to Playwright.
