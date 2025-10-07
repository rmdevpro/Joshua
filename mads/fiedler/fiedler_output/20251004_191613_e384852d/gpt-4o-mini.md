To implement the MCP protocol layer in Marco while addressing the issues identified, we need to modify the code in `server.js` to handle specific MCP methods (`initialize`, `tools/list`, and `tools/call`) directly within Marco itself. We'll also create appropriate response structures for these methods and ensure that only valid Playwright commands are forwarded to the Playwright subprocess.

Here's how you can achieve this:

### Step-by-Step Implementation

1. **Define the MCP Protocol Methods**:
   Add methods to handle `initialize` and `tools/list` directly within Marco, returning the correct capabilities and tool list.

2. **Modify Request Handling**:
   Ensure that when messages are received from clients, we check if they are MCP protocol methods. If they are, handle them directly, otherwise defer to the Playwright subprocess.

3. **Adjust the Processing Logic**:
   Maintain the existing FIFO queue for Playwright operations, but filter out MCP protocol methods to avoid forwarding them to the Playwright subprocess.

### Code Changes

Below are the specific changes to be made in `server.js`:

#### 1. Define Tool List and Initialization Response

Add at the top of your file (after existing constants):

```javascript
const tools = {
  // Example tools, populate these based on your actual Playwright tools
  "evaluate": {
    description: "Evaluates a script in the context of the page.",
    inputSchema: { type: "object", properties: { script: { type: "string" } } },
  },
  // Add more tools as needed
};
```

#### 2. Create MCP Protocol Handlers

Below the `enqueueRequest` function, add handlers for `initialize` and `tools/list`:

```javascript
function handleMCPRequest(clientId, request) {
  const method = request.method;
  const requestId = request.id;

  let response;

  switch (method) {
    case 'initialize':
      response = {
        jsonrpc: '2.0',
        id: requestId,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: Object.keys(tools) },
          serverInfo: { name: "marco", version: "1.0.0" },
        },
      };
      break;

    case 'tools/list':
      response = {
        jsonrpc: '2.0',
        id: requestId,
        result: {
          tools: Object.entries(tools).map(([name, spec]) => ({ name, ...spec })),
        },
      };
      break;

    default:
      return null; // Indicates it's a Playwright method or unknown
  }

  const client = clients.get(clientId);
  if (client && client.ws.readyState === WebSocket.OPEN) {
    client.ws.send(JSON.stringify(response));
  }
}
```

#### 3. Update Client Message Handling

Modify the `handleClientConnection` to process MCP requests directly:

Replace the part inside `ws.on('message', ...)`:

```javascript
ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    log('debug', 'Received message from client', { clientId, message });

    // Handle MCP protocol methods directly
    if (handleMCPRequest(clientId, message) === null) {
      // If not handled, enqueue the request for Playwright
      enqueueRequest(clientId, message);
    }
  } catch (err) {
    log('error', 'Failed to parse client message', { clientId, error: err.message });
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
```

#### 4. Modify Request Forwarding Logic

Ensure that in the `processNextRequest` function, you handle only Playwright method calls. If it’s an MCP method, it would have been dealt with in the `handleMCPRequest` function and would not be forwarded.

Here's an example adjustment:

In the `processNextRequest` function, when analyzing methods before forwarding them, exclude the already handled MCP methods.

### Recap

With these modifications:

- The `initialize` and `tools/list` methods are processed directly by Marco, returning the appropriate responses to the relay.
- Other requests (Playwright tool invocations) continue to be sent to the Playwright subprocess.
- The integration remains in line with the FIFO queue requirements.
- This approach minimizes changes to the existing structure while adding necessary MCP protocol handling.

These implementations will directly address the identified issue, ensuring your Marco WebSocket server integrates smoothly with the MCP protocol and Playwright subprocess.