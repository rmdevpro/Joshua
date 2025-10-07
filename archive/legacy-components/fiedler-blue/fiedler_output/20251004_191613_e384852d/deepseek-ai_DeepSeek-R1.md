<think>
We are given two files: `server.js` (Marco) and `mcp_server.py` (Dewey). The problem is that Marco currently forwards every message (including MCP protocol methods) to the Playwright subprocess, which doesn't understand them. We need to handle MCP protocol methods at the Marco level and only forward actual tool invocations.

The MCP protocol methods that Marco must handle are:
- `initialize`
- `tools/list`
- `tools/call`
- `notifications/initialized` (note: this is a notification, so it doesn't expect a response)

However, note that in the provided Dewey example, the `notifications/initialized` method is not handled explicitly. Instead, the Dewey example handles:
- `initialize`
- `tools/list`
- `tools/call`

Also, note that the Dewey example handles direct tool calls (without the `tools/call` wrapper) for backward compatibility. But in Marco, we are only concerned with the MCP protocol.

Plan for Marco:
1. Intercept incoming WebSocket messages and parse them as JSON-RPC requests.
2. For the following methods, handle them at the Marco level and do not forward to Playwright:
   - `initialize`
   - `tools/list`
   - `tools/call` (but note: `tools/call` is for actual tool invocations? Actually, no. The `tools/call` method is the MCP way to call a tool. However, in our case, the actual tool invocations (like `browser.newContext`, `page.goto`, etc.) are not MCP protocol methods. They are the tools that Playwright understands. So we should forward those to Playwright. But wait: the MCP protocol says that the client uses `tools/call` to invoke a tool. However, in our current Marco, the client is sending direct tool invocations (like `browser.newContext`). This is because the relay (client) is designed to work with Playwright MCP, which expects direct tool calls. 

But note: the problem states that the relay sends MCP protocol methods (like `initialize` and `tools/list`) and Marco is forwarding them to Playwright, which doesn't understand them. So we must handle `initialize` and `tools/list` in Marco. What about `tools/call`? 

Looking at the Dewey example, it handles `tools/call` by extracting the tool name and arguments and then calling the appropriate tool function. However, in Marco, the actual tool invocations (like `browser.newContext`) are sent as direct method calls (not wrapped in `tools/call`). Therefore, we don't need to handle `tools/call` in Marco? 

Wait, the problem says: "Only forward actual tool invocations (browser.*, page.*, context.*) to Playwright subprocess". So the MCP protocol methods are `initialize`, `tools/list`, and `notifications/initialized`. The `tools/call` method is not used by the relay? 

Actually, the relay might be using the MCP protocol in two ways:
1. The initial handshake: `initialize` and `notifications/initialized`.
2. Then, it uses `tools/list` to get the list of tools (which in Playwright MCP would be the browser automation commands).
3. Then, it uses `tools/call` to invoke a tool? Or does it use direct invocation?

The problem states that the relay is crashing because Marco forwards `initialize` to Playwright. So we must handle `initialize` and `tools/list` in Marco. The `notifications/initialized` is a notification from the client to the server (so Marco should handle it by not forwarding and just acknowledging? But note: the MCP protocol doesn't require a response for notifications).

However, looking at the Dewey example, it does not handle `notifications/initialized`. So let's stick to the methods we see in Dewey: `initialize`, `tools/list`, and `tools/call`. But note: the problem says that Marco should handle `notifications/initialized`? Actually, the problem says: "Handle ... `notifications/initialized` at Marco level". But in the MCP protocol, `initialized` is a notification that the client sends to the server after the server responds to `initialize`. The server doesn't need to respond to a notification. So Marco should just ignore it? Or handle it by doing nothing? 

But note: the current Marco code doesn't have any handling for these methods. We are going to add a new function to handle the MCP protocol methods.

Steps for Marco:
- In the WebSocket message handler, after parsing the message, check the method.
- If the method is one of the MCP protocol methods that we handle (`initialize`, `tools/list`, `notifications/initialized`), then handle it and do not enqueue the request.
- For `tools/call`: note that in the MCP protocol, the client uses `tools/call` to invoke a tool. But in our Marco, we are expecting direct tool invocations (like `browser.newContext`). So we must convert the `tools/call` into a direct tool invocation? 

But wait: the relay might be using `tools/call` to invoke a tool. How does the relay work? The problem states that the relay expects the same behavior as Dewey. In Dewey, the `tools/call` method is handled by extracting the tool name and arguments and then calling the tool function. In Marco, we want to forward the actual tool invocation to Playwright. So if we receive a `tools/call` request, we should:
1. Extract the tool name and arguments.
2. Create a new JSON-RPC request with the tool name as the method and the arguments as the params.
3. Then enqueue that new request to the Playwright subprocess.

But note: the problem says "Only forward actual tool invocations (browser.*, page.*, context.*) to Playwright". So we must handle `tools/call` by converting it to a direct tool call and then enqueuing it.

Alternatively, we could change the relay to send direct tool calls? But that is out of our control. The problem states that the relay is sending MCP protocol methods. So we must handle `tools/call` at the Marco level and convert it to a direct call.

But note: the provided Dewey example also supports direct tool calls (without `tools/call`) for backward compatibility. However, the relay might be using the MCP protocol strictly (using `tools/call`). So we must support both?

Actually, the problem does not specify. But to be safe, we can do:
- If the method is `tools/call`, then we convert it to a direct tool call and enqueue that.
- Otherwise, if the method is one of the MCP protocol methods (`initialize`, `tools/list`, `notifications/initialized`), handle it in Marco.
- Otherwise, assume it is a direct tool call and enqueue it.

But note: the `notifications/initialized` is a notification (no id). We don't need to respond, but we should not forward it to Playwright.

So let's break down:

1. `initialize`:
   - The client sends an `initialize` request. Marco should respond with the capabilities of the server (like in Dewey). But note: the capabilities should include the tool schema? Actually, the tool schema comes from Playwright. How do we get it?

   However, the problem says: "Track tool schema from Playwright's initialize response". This implies that when we start the Playwright subprocess, it sends an `initialize` response that includes the tool schema. We must capture that and then use it to respond to the client's `initialize` request.

   How it should work:
   - When Marco starts the Playwright subprocess, it will receive an `initialize` notification (or request?) from the subprocess? Actually, the Playwright MCP subprocess, when started, sends an `initialize` request to Marco? But in our current Marco, we are not handling that.

   We need to change the way we start the Playwright subprocess: we must wait for its `initialize` response and capture the tool schema. Then, when a client connects and sends `initialize`, we respond with the same tool schema (or a subset?).

   But note: the current Marco code does not handle the initial handshake with the Playwright subprocess. We are just starting the subprocess and then forwarding messages. We need to capture the `initialize` response from the subprocess and store the tool schema.

   Steps for capturing the tool schema from Playwright:
   - When the Playwright subprocess starts, it will send an `initialize` request? Or a response? Actually, in the MCP protocol, the server (Playwright) sends an `initialize` request to the client (Marco) when the connection is established? But in our current Marco, we are not sending an `initialize` request to the Playwright subprocess. We are just forwarding client requests.

   We must establish the connection with Playwright by sending an `initialize` request to it? Then it will respond with its capabilities. We can store that and then use it to respond to the client's `initialize` request.

   However, the problem says: "Minimal changes". So let's reconsider: the relay expects the same capabilities as from Playwright. We can hardcode the capabilities? But that would break if Playwright updates.

   Alternatively, we can do:
   - When Marco starts the Playwright subprocess, it sends an `initialize` request to the subprocess and waits for the response. Then it stores the capabilities.

   But note: the current Marco code does not have a handshake with the subprocess. We are just starting it and then forwarding messages. We need to add an initial handshake.

   However, the problem says: "Track tool schema from Playwright's initialize response". So we must capture it.

   Proposed plan for `initialize`:
   - When the Playwright subprocess starts, Marco sends an `initialize` request to it (with some parameters? maybe empty) and waits for the response.
   - Marco stores the `result` from that response (which contains the capabilities and the tool schema) in a variable, say `playwrightCapabilities`.
   - Then, when a client sends an `initialize` request, Marco responds with `playwrightCapabilities` (or a modified version?).

   But note: the client might send parameters in the `initialize` request. We should pass those to the Playwright subprocess? Actually, the MCP protocol says that the client sends an `initialize` request to the server (Marco) and Marco should respond with its own capabilities. We are using the Playwright capabilities as our own.

   So we do:
   - Marco sends an `initialize` request to Playwright (without any client parameters) at startup and stores the response.
   - Then, for each client `initialize` request, Marco responds with the stored capabilities.

   But note: the client might send different parameters? We are ignoring them. That's acceptable because the Playwright capabilities are fixed.

2. `tools/list`:
   - The client requests the list of tools. Marco should respond with the tool schema that it stored from the Playwright `initialize` response. The tool schema is in `playwrightCapabilities.capabilities.tools`? Actually, in the Playwright MCP, the `initialize` response has a `capabilities` object that includes a `tools` array? We need to look at the Playwright MCP documentation, but we don't have it. However, the problem says to use the same as Dewey? But Dewey returns a fixed list of tools. We are going to return the tools from Playwright.

   So we store the entire `result` from the Playwright `initialize` response. Then for `tools/list`, we return the `tools` array from that result? But note: the `tools/list` response in Dewey returns an object with a `tools` property that is an array of tool definitions. We can do the same.

   However, the Playwright `initialize` response might not have a `tools` array? We need to see what it returns. Since we don't have it, we assume that the Playwright `initialize` response has a `capabilities` object that includes a `tools` property. Then we can do:

   ```javascript
   // For `tools/list` request
   response = {
     jsonrpc: "2.0",
     id: request.id,
     result: {
       tools: playwrightCapabilities.capabilities.tools
     }
   }
   ```

   But note: the Dewey example returns an array of tools under `result.tools`. So we do the same.

3. `tools/call`:
   - The client sends a `tools/call` request with `name` and `arguments`. We convert this to a direct tool call by creating a new JSON-RPC request:
     ```json
     {
       "jsonrpc": "2.0",
       "id": <same id or generate a new one?>,
       "method": <the tool name>,
       "params": <the arguments>
     }
     ```
   - Then we enqueue this new request to the Playwright queue.

   But note: the original `tools/call` request has an id. We must respond to it when the tool call completes. However, we are replacing it with a new request that has a new id? Then we have to map the response back to the original id.

   Alternatively, we can keep the same id? But the Playwright subprocess will use that id in the response. Then when we get the response from Playwright, we have to convert it back to a `tools/call` response? But the client expects a response in the form of `tools/call`? Actually, no. The client expects a response to the `tools/call` request. The response should be:

   ```json
   {
     "jsonrpc": "2.0",
     "id": <original id>,
     "result": {
        ... // the result from the tool
     }
   }
   ```

   But the Playwright response will be:

   ```json
   {
     "jsonrpc": "2.0",
     "id": <same id as the direct tool call>,
     "result": ... // the result of the direct tool call
   }
   ```

   So we have to:
   - Create a new direct tool call request with a new id (so we can track it) and remember the original id and the original request (which is `tools/call`).
   - When we get the response for the direct tool call, we then send a response for the original `tools/call` request with the same result.

   However, this complicates the pending request tracking. Alternatively, we can use the same id for the direct tool call? But then the Playwright subprocess will see the same id that was used for `tools/call`. That might be acceptable? But note: the client might have multiple in-flight requests and the ids must be unique per connection. Since we are using the same id, it would be unique for the client.

   But what if the client sends two `tools/call` with the same id? That would be invalid per JSON-RPC. So we can use the same id for the direct tool call.

   Steps for `tools/call`:
   - Extract `params.name` and `params.arguments`.
   - Create a new request object:
        ```javascript
        const toolRequest = {
          jsonrpc: "2.0",
          id: request.id, // same id as the tools/call request
          method: params.name,
          params: params.arguments
        };
        ```
   - Then enqueue `toolRequest` (which will be sent to Playwright).
   - Do not respond immediately. We will respond when we get the response from Playwright for this id.

   But note: the pending request map in Marco is keyed by the request id. When we enqueue `toolRequest`, we are using the same id. Then when the response comes back from Playwright, we will look up by that id and find the client and then send the response. The client will see a response to the `tools/call` request? But the response from Playwright is for the direct tool call. We must wrap it in a `tools/call` response? Actually, no. The client expects the result of the tool call. The `tools/call` response should have a `result` field that contains the result of the tool. So we can just forward the result from the direct tool call as the result of the `tools/call` request.

   However, the Dewey example returns the result in a specific way? In Dewey, the `tools/call` response has a `result` field that is an object with a `content` array. But that is Dewey-specific. The client of Marco (the relay) expects the same response as from Playwright? So we should just forward the result from Playwright.

   Therefore, we don't need to change the response. We just forward the response from Playwright as the response to the `tools/call` request. The client will see the same response as if it had called the tool directly.

   But note: the id in the response will be the same as the `tools/call` request. That is correct.

   However, we must not mark the `tools/call` request as pending in the same way? Actually, we are enqueuing the converted request and then it will be added to the pending requests when it is sent. The pending request map will map the id to the client and the resolve/reject functions. When the response comes, it will be sent to the client. So it will work.

4. `notifications/initialized`:
   - This is a notification (no id). We should do nothing? But note: the Playwright subprocess might expect this notification? Actually, the MCP protocol says that after the client receives the `initialize` response, it sends an `initialized` notification. So Marco should forward this to the Playwright subprocess? But the problem says to handle it at the Marco level. 

   However, the problem says: "Handle ... `notifications/initialized` at Marco level". And then only forward actual tool invocations. So we should not forward it. But then the Playwright subprocess might be waiting for it? 

   This is a problem. We must understand the MCP protocol between Marco and Playwright. Since Marco is acting as a client to Playwright, it must follow the MCP protocol. So when Marco receives the `initialized` notification from the client (the relay), it should forward it to Playwright? But the problem says not to forward MCP protocol methods. 

   Alternatively, Marco should send the `initialized` notification to Playwright on behalf of the client? Because the client is sending it to Marco, and Marco is the client of Playwright. So we should forward it? But then we are forwarding an MCP protocol method. 

   This is a conflict. The problem says: "Only forward actual tool invocations". So we should not forward `initialized`. 

   How does Playwright MCP work? It expects:
   - The client (Marco) sends an `initialize` request to Playwright.
   - Playwright responds with its capabilities.
   - Then the client (Marco) sends an `initialized` notification to Playwright.

   But note: the relay is sending the `initialized` notification to Marco. So Marco should, upon receiving the `initialized` notification from the relay, send an `initialized` notification to Playwright? But that would be forwarding. And the problem says not to forward MCP protocol methods. 

   Alternatively, Marco should handle the `initialized` notification by sending its own `initialized` notification to Playwright? But that would be done once per client? Actually, no. The Playwright subprocess is shared by multiple clients. We cannot send multiple `initialized` notifications to Playwright.

   This indicates that the MCP protocol between the relay and Marco is per-connection, but the Playwright subprocess is shared. Therefore, we must not forward the `initialized` notification to Playwright. Instead, we should send the `initialized` notification to Playwright only once when the subprocess is started? 

   But the MCP protocol requires that the `initialized` notification is sent after the `initialize` response. And we are going to send the `initialize` request to Playwright at startup. Then we should send the `initialized` notification to Playwright immediately after? 

   So we change the startup of the Playwright subprocess:
   - Start the subprocess.
   - Send `initialize` request and wait for response (store capabilities).
   - Send `initialized` notification to Playwright.

   Then, when a client sends an `initialized` notification, we do nothing (because we already initialized the connection with Playwright).

   Therefore, we can ignore the `initialized` notification from the client? Or we can handle it by doing nothing.

   But note: the client might expect a response? No, it's a notification.

   So for `notifications/initialized` from the client, we do nothing.

Summary of changes:

1. When starting the Playwright subprocess, we need to perform the MCP handshake:
   - Send an `initialize` request to Playwright and wait for the response. Store the capabilities.
   - Send an `initialized` notification to Playwright.

2. In the WebSocket message handler for a client:
   - If the method is `initialize`:
        - Respond immediately with the stored capabilities (without forwarding to Playwright).
   - If the method is `tools/list`:
        - Respond with the list of tools from the stored capabilities (without forwarding).
   - If the method is `tools/call`:
        - Convert it to a direct tool call request (with the same id) and enqueue that request.
        (do not enqueue the original `tools/call` request)
   - If the method is `notifications/initialized`:
        - Do nothing (ignore).
   - Else (direct tool call or other):
        - Enqueue the request (current behavior).

3. We must also handle the case where the Playwright subprocess restarts. We need to redo the handshake and update the stored capabilities.

Implementation details:

- We need a variable to store the capabilities: `let playwrightCapabilities = null;`
- We need to modify the `startPlaywrightSubprocess` function to perform the handshake.

Steps in `startPlaywrightSubprocess`:
   - After starting the subprocess, wait for the stdout to send the `initialize` request and then the `initialized` notification.
   - But note: we cannot send until the subprocess is ready? We are already listening to stdout. We can send the `initialize` request immediately after the subprocess is spawned.

   We'll create a function `performHandshake()` that returns a promise. We call it after the subprocess is started.

   ```javascript
   async function performHandshake() {
     if (!playwrightProcess) {
       return;
     }

     // Send initialize request
     const initializeRequest = {
       jsonrpc: "2.0",
       id: "marco_initialize_1", // we can use a fixed id for handshake
       method: "initialize",
       params: {} // or whatever parameters are required? Playwright might not require any.
     };

     return new Promise((resolve, reject) => {
       // We'll wait for the response with id "marco_initialize_1"
       const handshakeTimeout = setTimeout(() => {
         reject(new Error('Handshake timeout'));
       }, 5000);

       // Temporary handler for the handshake response
       const handleHandshakeResponse = (messageLine) => {
         try {
           const message = JSON.parse(messageLine);
           if (message.id === initializeRequest.id) {
             // This is the response we are waiting for
             clearTimeout(handshakeTimeout);
             // Remove this temporary handler? We can't easily remove one listener. Alternatively, we can use a one-time event.
             playwrightCapabilities = message.result;
             log('info', 'Playwright capabilities received', { capabilities: playwrightCapabilities });

             // Now send the initialized notification
             const initializedNotification = {
               jsonrpc: "2.0",
               method: "notifications/initialized",
               params: {}
             };
             playwrightProcess.stdin.write(JSON.stringify(initializedNotification) + '\n');

             resolve();
           }
         } catch (err) {
           // Not a JSON message? Ignore.
         }
       };

       // We are already collecting stdout in the 'data' event. We need to intercept the handshake response.
       // We can temporarily override the stdout handler? Or we can use a one-time event.
       // Instead, we'll use a temporary event listener that is removed after the handshake.
       const originalStdoutHandler = playwrightProcess.stdout.on;
       playwrightProcess.stdout.removeAllListeners('data'); // This is dangerous because we have the main handler.
       // We cannot remove the main handler. So we'll use a different approach.

       // Instead, we'll wrap the existing stdout handler and look for the handshake response.
       // We'll save the existing buffer and then restore after the handshake? This is complex.

       // Alternatively, we can use the existing `handlePlaywrightMessage` function? But it doesn't know about the handshake.

       // We can set a flag and in `handlePlaywrightMessage` we look for the handshake response.
       // Let's do that.

       // We'll set a variable `handshakeResolve` and `handshakeReject` and then in `handlePlaywrightMessage` we check for the id.
       handshakeResolve = resolve;
       handshakeReject = reject;

       // Send the initialize request
       playwrightProcess.stdin.write(JSON.stringify(initializeRequest) + '\n');
     });
   }
   ```

   But this is complex. We can instead handle the handshake in the existing `handlePlaywrightMessage` function by checking for the handshake id.

   We'll do:

   - In `startPlaywrightSubprocess`, after spawning the process, we send the `initialize` request and then wait for the response by setting a promise that is resolved when we get the response for that id.

   We'll add:

   ```javascript
   let handshakePromise = null;
   let handshakeResolve = null;
   let handshakeReject = null;

   function startPlaywrightSubprocess() {
     // ... existing code

     // After spawning, send initialize request and set up handshake promise
     handshakePromise = new Promise((resolve, reject) => {
       handshakeResolve = resolve;
       handshakeReject = reject;
     });

     const initializeRequest = {
       jsonrpc: "2.0",
       id: "marco_initialize_1",
       method: "initialize",
       params: {}
     };
     playwrightProcess.stdin.write(JSON.stringify(initializeRequest) + '\n');

     // Also set a timeout for the handshake
     const handshakeTimeout = setTimeout(() => {
       log('error', 'Playwright handshake timed out');
       handshakeReject(new Error('Handshake timeout'));
       // Kill and restart? We might want to restart.
       playwrightProcess.kill();
     }, 5000);

     handshakePromise.then(() => {
       clearTimeout(handshakeTimeout);
       // Send initialized notification
       const initializedNotification = {
         jsonrpc: "2.0",
         method: "notifications/initialized",
         params: {}
       };
       playwrightProcess.stdin.write(JSON.stringify(initializedNotification) + '\n');
     }).catch(err => {
       clearTimeout(handshakeTimeout);
       log('error', 'Playwright handshake failed', { error: err.message });
       playwrightProcess.kill();
     });
   }
   ```

   Then in `handlePlaywrightMessage`:

   ```javascript
   if (message.id === "marco_initialize_1") {
     if (handshakeResolve) {
       playwrightCapabilities = message.result;
       handshakeResolve();
       handshakeResolve = null;
       handshakeReject = null;
     }
     return; // don't process this as a normal response
   }
   ```

   But note: we are also getting the handshake response in the normal pending requests? We don't have a pending request for it because we didn't enqueue it. So it's safe.

   However, we must be cautious: the handshake response is not for a client request, so we don't want to send it to any client.

4. We must also redo the handshake when the subprocess restarts.

5. In the WebSocket message handler, we add:

   ```javascript
   ws.on('message', (data) => {
     try {
       const message = JSON.parse(data.toString());
       log('debug', 'Received message from client', { clientId, message });

       // Handle MCP protocol methods
       if (message.method === "initialize") {
         if (!playwrightCapabilities) {
           // Handshake not complete? We should wait? Or fail.
           ws.send(JSON.stringify({
             jsonrpc: "2.0",
             id: message.id,
             error: {
               code: -32603,
               message: "Server not ready"
             }
           }));
           return;
         }
         // Respond with capabilities
         ws.send(JSON.stringify({
           jsonrpc: "2.0",
           id: message.id,
           result: playwrightCapabilities
         }));
         return;
       } else if (message.method === "tools/list") {
         if (!playwrightCapabilities) {
           ws.send(JSON.stringify({
             jsonrpc: "2.0",
             id: message.id,
             error: {
               code: -32603,
               message: "Server not ready"
             }
           }));
           return;
         }
         // Respond with the tools list from capabilities
         ws.send(JSON.stringify({
           jsonrpc: "2.0",
           id: message.id,
           result: {
             tools: playwrightCapabilities.capabilities.tools
           }
         }));
         return;
       } else if (message.method === "tools/call") {
         // Convert to direct tool call
         const toolName = message.params.name;
         const toolArgs = message.params.arguments;
         const toolRequest = {
           jsonrpc: "2.0",
           id: message.id, // same id
           method: toolName,
           params: toolArgs
         };
         // Enqueue the toolRequest
         enqueueRequest(clientId, toolRequest);
         return;
       } else if (message.method === "notifications/initialized") {
         // Do nothing
         return;
       }

       // Otherwise, enqueue the request (direct tool call or other)
       enqueueRequest(clientId, message);
     } catch (err) {
       // ... existing error handling
     }
   });
   ```

   Note: we return after handling these methods so they are not enqueued.

6. We must also handle the case where the handshake fails or times out. We should not respond to `initialize` or `tools/list` until the handshake is complete.

7. We must store `playwrightCapabilities` in a global variable and reset it when the subprocess restarts.

Given the complexity, we must be cautious about the order of changes.

Let's outline the code changes:

Global variable:
```javascript
let playwrightCapabilities = null; // Store the capabilities from Playwright handshake
let handshakeResolve = null;
let handshakeReject = null;
```

In `startPlaywrightSubprocess`:
   - After spawning the process, create a handshake promise and send the `initialize` request.

In `handlePlaywrightMessage`:
   - Add a condition to catch the handshake response.

In the WebSocket message handler:
   - Add the conditionals for the MCP protocol methods.

We also need to handle the `initialized` notification to Playwright after the handshake.

But note: the handshake is only done once per subprocess start. When the subprocess restarts, we do the handshake again.

We must reset `playwrightCapabilities` to null when the subprocess exits.

In the `playwrightProcess.on('exit')` handler, add:
```javascript
playwrightCapabilities = null;
```

And in `startPlaywrightSubprocess`, we reset `restartAttempts` after stable operation? We already have a timeout for that.

This is a significant change. We must be cautious about the handshake and the timing.

Let's write the code changes step by step.

Due to the complexity, we'll break it down:

Step 1: Add global variables for handshake
```javascript
let playwrightCapabilities = null;
let handshakeResolve = null;
let handshakeReject = null;
```

Step 2: In `startPlaywrightSubprocess`, after spawning, send the handshake `initialize` request and set up the handshake promise and timeout.

Step 3: In `handlePlaywrightMessage`, handle the handshake response.

Step 4: In the WebSocket message handler, handle the MCP protocol methods.

Step 5: In the subprocess exit handler, reset `playwrightCapabilities`.

We'll now provide the code changes in the required format.

Note: This solution is complex and might have edge cases. We are doing minimal changes to meet the requirements.

Let's write the code changes for `server.js`:
</think>
To address the MCP protocol layer bug in Marco, we need to implement protocol handling at the gateway level while maintaining the existing FIFO queue for Playwright operations. Here's the solution:

### Key Changes Required:
1. **Store Playwright capabilities** during subprocess initialization
2. **Intercept MCP protocol methods** (`initialize`, `tools/list`, `notifications/initialized`)
3. **Convert `tools/call`** to direct Playwright invocations
4. **Handle `initialized` notification** for Playwright handshake

### Implementation Plan:

#### 1. Add Global State for Capabilities
```javascript
// ============================================================================
// Global State
// ============================================================================
let playwrightCapabilities = null; // Add this line
```

#### 2. Modify Playwright Startup Handshake
```javascript
function startPlaywrightSubprocess() {
  // ... existing code ...

  // After spawning the process:
  const handshake = () => {
    if (!playwrightProcess || playwrightProcess.killed) return;

    // Send initialize request to Playwright
    const initializeRequest = {
      jsonrpc: "2.0",
      id: "marco_initialize_1",
      method: "initialize",
      params: {}
    };
    playwrightProcess.stdin.write(JSON.stringify(initializeRequest) + '\n');
  };

  // Handle handshake response
  const originalHandleMessage = handlePlaywrightMessage;
  handlePlaywrightMessage = (messageLine) => {
    try {
      const message = JSON.parse(messageLine);
      if (message.id === "marco_initialize_1") {
        playwrightCapabilities = message.result;
        log('info', 'Received Playwright capabilities', { capabilities: playwrightCapabilities });
        
        // Send initialized notification to Playwright
        const initializedNotification = {
          jsonrpc: "2.0",
          method: "notifications/initialized",
          params: {}
        };
        playwrightProcess.stdin.write(JSON.stringify(initializedNotification) + '\n');
        
        // Restore original handler
        handlePlaywrightMessage = originalHandleMessage;
      }
    } catch (err) {
      log('error', 'Handshake failed', { error: err.message });
    }
    originalHandleMessage(messageLine);
  };

  // Start handshake
  setTimeout(handshake, 100);
}
```

#### 3. Implement MCP Protocol Handler
```javascript
// ============================================================================
// MCP Protocol Handler
// ============================================================================
function handleMCPRequest(clientId, ws, request) {
  const { method, id, params } = request;

  try {
    switch (method) {
      case "initialize":
        if (!playwrightCapabilities) {
          throw new Error("Playwright not initialized");
        }
        ws.send(JSON.stringify({
          jsonrpc: "2.0",
          id,
          result: playwrightCapabilities
        }));
        return true;

      case "tools/list":
        if (!playwrightCapabilities?.capabilities?.tools) {
          throw new Error("Tools not available");
        }
        ws.send(JSON.stringify({
          jsonrpc: "2.0",
          id,
          result: {
            tools: playwrightCapabilities.capabilities.tools
          }
        }));
        return true;

      case "tools/call":
        // Convert to direct Playwright invocation
        enqueueRequest(clientId, {
          jsonrpc: "2.0",
          id,
          method: params.name,
          params: params.arguments
        });
        return true;

      case "notifications/initialized":
        // No action needed (handled during startup)
        return true;
    }
  } catch (err) {
    log('error', 'MCP handling failed', { method, error: err.message });
    ws.send(JSON.stringify({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32603,
        message: "Internal error",
        data: { originalError: err.message }
      }
    }));
    return true;
  }

  return false; // Not an MCP method
}
```

#### 4. Modify WebSocket Message Handler
```javascript
ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    log('debug', 'Received message from client', { clientId, message });

    // Handle MCP protocol first
    if (handleMCPRequest(clientId, ws, message)) {
      return;
    }

    // Enqueue other requests
    enqueueRequest(clientId, message);
  } catch (err) {
    // ... existing error handling ...
  }
});
```

#### 5. Update Subprocess Cleanup
```javascript
playwrightProcess.on('exit', (code, signal) => {
  // ... existing code ...
  playwrightCapabilities = null; // Reset capabilities
});
```

### Key Improvements:
1. **Protocol Separation**:
   - MCP methods handled at gateway level
   - Playwright only sees actual invocations (`browser.*`, `page.*`, etc.)

2. **Capability Tracking**:
   - Stores tool schema during initialization
   - Reuses schema for `tools/list` responses

3. **Queue Preservation**:
   - Maintains FIFO processing for Playwright operations
   - Converts `tools/call` to direct invocations before enqueueing

4. **Handshake Management**:
   - Performs Playwright initialization once
   - Handles `initialized` notification internally

### Testing Considerations:
1. Verify handshake completes before client connections
2. Test `initialize` returns capabilities immediately
3. Confirm `tools/list` shows Playwright tools
4. Ensure `tools/call` gets converted and enqueued
5. Validate `notifications/initialized` is no-op

This solution maintains your existing architecture while adding the necessary protocol layer. The changes are minimal and focused on the MCP-specific requirements, preserving your queue management and context tracking logic.