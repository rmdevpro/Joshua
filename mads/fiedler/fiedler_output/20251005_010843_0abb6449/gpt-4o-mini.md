The symptoms you're describing indicate that the relay is aware of the tools available on the Gates server, but the tool calls made via Claude Code are failing to recognize them. This can happen due to several reasons, and troubleshooting could involve examining the following aspects:

1. **Tool Registration and Caching:**
   - When you changed the `serverInfo.name` from "gates-mcp-server" to "gates," it’s possible that any existing cached information about the server's tools in the Claude Code or the relay might not have been updated properly. Check if there is a mechanism to clear or refresh the cache on the client side to ensure it queries the latest tool registration.

2. **Notification System:**
   - Verify if there is a notification system that informs the clients (like Claude Code) about updates in tool availability. Sometimes, clients subscribe to changes and need to receive an event or message indicating that tools have been added or modified. Ensure that a notification was sent out for the newly named server and its tools.

3. **Relaying and Routing Issues:**
   - Although the relay reports that the Gates server has 3 tools, it’s worthwhile to check if there are any specific routing rules or configurations that might affect how the tools are accessed. Sometimes, tools might be exposed under different endpoints or require specific authentication contexts.

4. **Session State:**
   - If the connection between the client and the relay was established before the changes were made, the session state may not be aware of the updated tool names. A possible solution could be to refresh the client session or restart the client application to ensure it queries the latest server information afresh.

5. **Tool Name Prefix:**
   - Double-check if the tools are expected to have specific prefixes or naming conventions. Even if the other servers use simple names, Gates might require a specific namespace or prefix that needs to remain consistent with its expected use.

6. **Error Tracking and Logging:**
   - Investigate any logs on both the relay and the Gates server to see if there are any warnings or errors related to tool registration, health checks, or communications that could provide further insight.

To troubleshoot, I would recommend taking the following steps:

- Clear the cache in the Claude Code client or restart it to force a refresh of the available tools.
- Check the notification system to see if it registered the change properly.
- Review logs on both the relay and the Gates server for any anomalies.
- Re-test the calls using the exact names as they are registered on the Gates server.

By going through these steps methodically, you should be able to pinpoint the issue preventing Claude Code from recognizing the Gates tools despite the relay's correct status reporting.