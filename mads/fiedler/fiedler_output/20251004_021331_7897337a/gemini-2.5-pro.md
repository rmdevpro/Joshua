Excellent and detailed problem report. This is a classic proxy/streaming issue.

Based on your evidence, the diagnosis is clear:

**Your `KGB` HTTP gateway is breaking the streaming response from the Anthropic API by buffering it.**

### The Core Problem: Streaming vs. Buffering

1.  **How Claude API Works:** When you make a request to the Anthropic Messages API, it doesn't send the whole response at once. It uses a technology called **Server-Sent Events (SSE)**, which is a streaming protocol over HTTP. The server sends the response in small chunks (tokens) as they are generated. The `Content-Type` header for this is `text/event-stream`.
2.  **How the Claude CLI Works:** The CLI is built to handle this stream. It opens a connection and waits for these chunks to arrive one by one, printing them to the screen. It knows the response is finished only when it receives a special "end-of-stream" message from the server.
3.  **What Your Proxy is Doing:** Your KGB proxy receives the request and forwards it to Anthropic. Anthropic starts streaming the response back to KGB. However, instead of passing these chunks through to the CLI as they arrive, KGB is **buffering the entire response**. It waits until it has received all 2597 bytes from Anthropic, and only then does it send the *complete, non-streamed* response back to the Claude CLI in one go.
4.  **Why it Hangs:** The Claude CLI receives the full block of data, but it never receives the "end-of-stream" signal it's expecting because the stream was collapsed into a single response by the proxy. The CLI's internal logic is still waiting for the stream to close properly, so it hangs indefinitely.

This perfectly explains all your observations:
*   **KGB sees 200 OK:** Because it successfully received the *entire* response from Anthropic.
*   **CLI hangs:** Because it's a streaming client that received a non-streaming response.
*   `claude --version` works: It's a simple command that doesn't make a network request, so the proxy isn't involved.
*   Bare-metal with proxy hangs: This confirms the issue is the CLI-to-Proxy interaction, not Docker.
*   Bare-metal without proxy works: This confirms the CLI works perfectly with a proper SSE stream.

---

### How to Fix It

You have two primary paths to a solution: fix the proxy (the correct way) or change the client's behavior to match the broken proxy (the workaround).

#### Solution 1: Fix the KGB Proxy (Recommended)

You need to configure your `KGB` proxy to **disable response buffering** for the Anthropic endpoint. It must act as a true stream-through proxy.

Since I don't know what software "KGB" is, here are the general principles and examples for common proxy servers:

*   **Look for Buffering Settings:** Search your KGB proxy's configuration for terms like `buffer`, `proxy_buffering`, `stream`, or `chunked encoding`.
*   **Ensure Headers are Passed Through:** The proxy must not strip or alter critical headers from the Anthropic response, specifically `Content-Type: text/event-stream` and `Transfer-Encoding: chunked`.

**If KGB is based on Nginx:**
You would need to add something like this to the relevant `location` block in your Nginx config:

```nginx
location / {
    proxy_pass http://api.anthropic.com;
    
    # --- CRITICAL FOR STREAMING ---
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    proxy_buffering off;  # <-- This is the magic line
    proxy_cache off;
    chunked_transfer_encoding on;
    # ------------------------------
}
```

**If KGB is a custom app (Node.js, Go, Python):**
The code is likely reading the entire response body from Anthropic into a variable before writing it to the client response. It needs to be rewritten to pipe the response stream directly.

*   **Node.js/Express Example (Wrong Way):**
    ```javascript
    // This BUFFERS and will cause the hang
    const response = await fetch(anthropicUrl, options);
    const body = await response.text();
    res.send(body);
    ```
*   **Node.js/Express Example (Correct Way):**
    ```javascript
    // This STREAMS and will fix the issue
    const anthropicResponse = await fetch(anthropicUrl, options);
    res.setHeader('Content-Type', 'text/event-stream'); // Pass through headers
    anthropicResponse.body.pipe(res);
    ```

#### Solution 2: The Workaround (If you can't fix the proxy)

Tell the Claude CLI to not use streaming. The client will make a standard HTTP request and wait for the full response, which is exactly what your proxy is providing.

The Claude Code CLI has a flag for this: `--no-stream`.

**Try this command:**

```bash
echo "test" | docker exec -i claude-code-container claude --no-stream --print
```

This tells the CLI to make a non-streaming API call. The CLI will now happily accept the complete, buffered response from your KGB proxy and should exit immediately after printing it.

### Diagnostic Step: Prove the Theory with `curl`

You can confirm the buffering behavior of your proxy using `curl`. The `-N` or `--no-buffer` flag tells curl to process the output as it arrives.

1.  **Test against the real API (what it *should* look like):**
    ```bash
    # You will see output appear in chunks
    curl -N https://api.anthropic.com/v1/messages \
      -H "x-api-key: $ANTHROPIC_API_KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" \
      --data '{
        "model": "claude-3-opus-20240229",
        "max_tokens": 200,
        "stream": true,
        "messages": [{"role": "user", "content": "Tell me a short story."}]
      }'
    ```

2.  **Test against your proxy (what is *likely* happening):**
    *Run this from a machine that can reach the proxy (e.g., inside the Docker network or on the host).*

    ```bash
    # You will likely see nothing for a few seconds, then the entire JSON response dumped at once
    curl -N http://kgb-proxy:8089/v1/messages \
      -H "x-api-key: $ANTHROPIC_API_KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" \
      --data '{
        "model": "claude-3-opus-20240229",
        "max_tokens": 200,
        "stream": true,
        "messages": [{"role": "user", "content": "Tell me a short story."}]
      }'
    ```

If test #2 dumps all the text at the end instead of streaming it, you have 100% confirmation that the proxy is the issue.
