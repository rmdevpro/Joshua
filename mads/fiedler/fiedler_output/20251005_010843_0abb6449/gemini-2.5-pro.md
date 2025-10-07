Excellent question. This is a classic and tricky state synchronization problem. Based on the symptoms you've described, the root cause is almost certainly a caching or state desynchronization issue within the Claude Code environment itself, not the relay.

Let's break down why this happens and how to fix it.

### The Most Likely Cause: Stale Tool Registry in the Model's Session

Here’s the sequence of events that leads to this specific bug:

1.  **Initial Session Start:** When your session with Claude Code began, the MCP Relay connected to your servers, including the one named `"gates-mcp-server"`.
2.  **Tool Registration:** The relay advertised the available tools to the Claude Code environment. At this point, the model learned about a tool named `mcp__iccm__gates-mcp-server_list_capabilities` (and the other two). This list of tools is loaded into the model's context for the current session. **This is the crucial step.**
3.  **You Change the Server Name:** You stopped the Gates server, changed its `serverInfo.name` to `"gates"`, and restarted it.
4.  **Relay Reconnects:** The MCP Relay, being resilient, saw the old server disappear and the "new" one appear. From the relay's perspective, it correctly connected to a server named `"gates"` and discovered its 3 tools. This is why `relay_get_status` and `relay_reconnect_server` show everything as healthy. The relay's internal state is perfectly up-to-date.
5.  **The Disconnect:** The relay likely sent a "tool update" notification to the Claude Code environment, saying "hey, forget about the `gates-mcp-server` tools and use these new `gates` tools instead."
6.  **The Failure Point:** For a variety of reasons (often to maintain session consistency and performance), the model's core environment does not always dynamically hot-swap its fundamental tool definitions mid-session. It holds onto the list of tools it was given at the beginning.

So, you have this situation:

*   **Claude Code's Brain:** "I know about `fiedler`, `dewey`, `playfair`, and `gates-mcp-server` tools. That's my world."
*   **MCP Relay's State:** "I am connected to `fiedler`, `dewey`, `playfair`, and `gates`. The `gates-mcp-server` is gone."

When you try to call `mcp__iccm__gates_list_capabilities`, Claude Code checks its internal, *stale* list of tools, doesn't find a match, and correctly reports **"No such tool available"**. It doesn't even attempt to send the request to the relay, because as far as it's concerned, that tool doesn't exist.

### Answering Your Specific Questions

*   **Is there a caching issue?** **Yes, absolutely.** This is the core of the problem. The model's environment has cached the tool definitions from the start of the session.
*   **A notification issue?** **Yes, this is the mechanism.** The notification from the relay to the model to update the toolset was either not sent, not supported, or (most likely) ignored by the model's environment to prevent state corruption mid-turn.
*   **Something specific to how new servers are registered mid-session?** **Yes.** It's specifically about *changing the identity* of a server mid-session. Adding a completely new server with a new name might work, but *renaming* one often exposes this caching behavior because the old definitions need to be purged and replaced, which is a more complex operation.

### How to Fix It

The solution is to force a complete refresh of the model's environment so it learns the new, correct tool names from a clean slate.

#### The Immediate, Guaranteed Fix:

**Restart the session.**

In a notebook environment, this means restarting the kernel. If you're in another environment, it means ending the current conversation/session and starting a brand new one.

This will cause the entire stack to re-initialize. The MCP Relay will connect to all servers *as they are currently configured*, and it will present the correct, final list of tools (`mcp__iccm__gates_...` included) to the brand new model session.

#### Diagnostic Step (for confirmation):

Before you restart, try this for science:

```
# Ask Claude to call the OLD tool name
call mcp__iccm__gates-mcp-server_list_capabilities
```

You will likely get a *different* error. Instead of "No such tool available," you might get a timeout, a connection error, or a message from the relay saying "server 'gates-mcp-server' is not connected." This would prove that the model *knows about the old tool* but can't reach it, confirming the stale registry theory.

### Best Practice Going Forward

When you need to make a fundamental change to a server's identity (like its `serverInfo.name`), the most reliable workflow is:

1.  Make the configuration change in your server code.
2.  Restart the server container.
3.  **Restart your Claude Code session/kernel.**

This ensures that all components have a consistent and synchronized view of the available tools from the very beginning.
