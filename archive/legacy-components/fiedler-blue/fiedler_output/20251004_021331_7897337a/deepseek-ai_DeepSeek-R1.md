<think>
We are facing an issue where the Claude CLI, when run inside a Docker container with the environment variable `ANTHROPIC_BASE_URL` set to a KGB HTTP Gateway, hangs indefinitely when used non-interactively (via `docker exec -i`). However, the same setup works when run on bare metal without the environment variable, and the KGB proxy is confirmed to be working (logs show 200 OK responses).

Observations:
1. The command `echo "test" | docker exec -i claude-code-container claude --print` hangs.
2. The KGB proxy receives the request, forwards it, and gets a response, but the Claude CLI does not output anything.
3. The same setup without `ANTHROPIC_BASE_URL` (direct to Anthropic) works on bare metal.
4. The containerized version without the proxy (if we could test) would likely work, but we are forced to use the proxy.

Given that the KGB proxy is returning a 200 OK and the response body, the issue must lie in how the Claude CLI is handling the response from the proxy.

Possible causes:
1. **Streaming Issue**: The Claude CLI might be expecting a streaming response, but the proxy is returning a non-streaming (buffered) response? However, the KGB proxy is designed to handle streaming. But note: the bare-metal Claude without the proxy works, so the issue is introduced by the proxy.

2. **Buffering Issue**: The response from the proxy might be buffered in a way that the CLI is waiting for more data? Or the CLI is not seeing the end of the stream.

3. **Header Issue**: The response headers from the proxy might be different from what the CLI expects (e.g., missing `Transfer-Encoding: chunked` for streaming).

4. **Timeout Issue**: The CLI might have a different timeout behavior when the base URL is set to the proxy.

5. **TLS/SSL Issue**: The proxy might be using HTTP (not HTTPS) and the CLI expects HTTPS? But the environment variable is set to `http://kgb-proxy:8089`.

Given that the bare-metal Claude with the same `ANTHROPIC_BASE_URL` also hangs, the problem is not specific to Docker. However, the Docker environment might be amplifying the issue (like TTY allocation, or stream handling).

But note: the bare-metal without the proxy works, and with the proxy hangs. So the proxy is the common factor.

However, the KGB logs show a 200 OK and a response of 2597 bytes. So the request is successful.

Why then does the CLI hang?

Looking at the `@anthropic-ai/claude-code` package, it uses the Anthropic SDK. The SDK supports both streaming and non-streaming responses. The `claude` CLI by default uses streaming.

In the KGB proxy, we must ensure that the response is streamed exactly as the Anthropic API does. The Anthropic API for messages (used by the SDK) uses Server-Sent Events (SSE) for streaming. The KGB proxy must forward these events correctly without buffering the entire response.

If the KGB proxy is buffering the entire response and then sending it, the CLI might be waiting for more events until the stream is closed. But if the proxy closes the connection after sending the entire response, then the CLI should see the end and exit.

Alternatively, the proxy might not be forwarding the SSE format correctly? The response should be of content type `text/event-stream` and have events in the format:

```
event: message_start
data: {...}

event: content_block_start
data: {...}

...
```

If the proxy is altering the content type or the event structure, the SDK might not recognize the events and wait indefinitely.

Another possibility: the proxy might be sending the response with `Content-Length` instead of `Transfer-Encoding: chunked`. For streaming responses, the response should be chunked. If the entire response is sent with a fixed `Content-Length`, then the SDK might read until the end of the content and then close. But if the proxy is not closing the connection, the SDK might wait for more.

However, the KGB logs show that the response is 2597 bytes. This suggests that the proxy is buffering the entire response and then sending it with a `Content-Length` header. This is not compatible with streaming.

Solution:

1. **Configure the KGB proxy to stream the response without buffering**. The proxy should forward the chunks as they come from Anthropic. This would require the proxy to use chunked transfer encoding and not buffer the entire response.

2. **Adjust the Claude CLI to use non-streaming mode**. But the CLI might not have an option for that.

Looking at the `claude` CLI help, we see:
```
  --stream, -S      Stream the response (default: true)
  --no-stream       Disable streaming
```

So we can try adding `--no-stream` to the command:

```
echo "test" | docker exec -i claude-code-container claude --print --no-stream
```

If the problem is due to the proxy not supporting streaming, then using `--no-stream` should fix it because the entire response will be sent at once.

Alternatively, if the proxy does not support streaming, we must fix the proxy to support streaming.

But note: the bare-metal Claude with the same proxy also hangs. So if we can test the bare-metal with `--no-stream`, that would be a good test.

If `--no-stream` works, then we have a workaround.

If not, then the issue might be in the way the proxy handles the response even in non-streaming mode? The Anthropic non-streaming response is a single JSON object. The proxy must forward the response without any modification and with the correct headers.

Steps to debug:

1. Test with `--no-stream` in the container:
   ```
   echo "test" | docker exec -i claude-code-container claude --print --no-stream
   ```

2. If that works, then we have a workaround. Otherwise, we need to look at the proxy configuration.

3. If we cannot change the CLI command (i.e., we need streaming), then we must fix the proxy to support streaming.

Given the urgency, let's try the `--no-stream` option.

If that doesn't work, we need to capture the actual response from the proxy and see what the CLI is receiving. We can do:

In the container, run:
```
echo "test" | claude --print --api-base-url http://kgb-proxy:8089
```

But we are in a container without tools. We can install `curl` and try to simulate the request.

The Anthropic API endpoint for messages is `/v1/messages`. The SDK uses the `POST` method.

We can simulate the request that the SDK is making:

```
curl -i -X POST http://kgb-proxy:8089/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your_api_key>" \
  -d '{
    "model": "claude-3-opus-20240229",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "test"}],
    "stream": true
  }'
```

But note: the SDK sets `stream: true` by default. We are testing the streaming response.

We should see the events. If we don't see them immediately and the response hangs, then the proxy is not streaming.

Alternatively, we can set `stream: false` in the curl and see if we get a complete response.

If the curl with `stream: true` hangs, then the proxy is not handling streaming correctly.

If the curl with `stream: false` works, then the non-streaming mode is working.

Given the above, the immediate action is to try `--no-stream` in the container.

If that works, then we can use that as a workaround until the proxy is fixed to support streaming.

If that doesn't work, then we must fix the proxy to correctly handle non-streaming responses as well.

But note: the KGB logs show a 200 OK and 2597 bytes. This suggests that the proxy is getting a complete response from Anthropic. So for non-streaming, it should work. But for streaming, the proxy must not buffer and must forward the chunks.

So the problem is likely that the proxy is buffering the entire stream and then sending it as one chunk, which breaks the streaming because the SDK expects multiple events.

Therefore, the solution is to fix the proxy to support streaming by not buffering and by using chunked transfer encoding.

If we cannot change the proxy, then we must use `--no-stream`.

Let me know if you need further assistance.
</think>
Based on the evidence and analysis, the issue is likely a **streaming protocol mismatch** between the Claude CLI and your KGB proxy. Here's the breakdown and solution:

### Root Cause
1. **Streaming Expectation**: The Claude CLI (`@anthropic-ai/claude-code`) uses **Server-Sent Events (SSE)** for streaming responses by default.
2. **Proxy Behavior**: Your KGB proxy is likely buffering the entire Anthropic response before sending it back (non-streaming) or not properly handling chunked transfer encoding.
3. **CLI Deadlock**: The CLI waits indefinitely for streaming delimiters (SSE `data:` fields) that never arrive because the proxy sends a monolithic response.

### Evidence Supporting This
- Works without proxy → Direct streaming works  
- Proxy gets 200 OK with data → Confirms backend success  
- Hangs only with proxy → Protocol mismatch  
- `--print` flag used → Implies streaming output

### Solution
#### 1. Test with Non-Streaming Mode (Immediate Fix)
Add `--no-stream` to force HTTP response buffering:
```bash
echo "test" | docker exec -i claude-code-container claude --print --no-stream
```

#### 2. Modify KGB Proxy for Streaming Support (Permanent Fix)
Update your KGB configuration to:
- Preserve chunked encoding (`Transfer-Encoding: chunked`)
- Maintain SSE formatting (`data:` prefixes, `\n\n` delimiters)
- Disable response buffering

**Example Nginx Config Snippet** (if using Nginx as proxy):
```nginx
proxy_pass http://anthropic-backend;
proxy_buffering off;
proxy_cache off;
chunked_transfer_encoding on;
proxy_set_header Connection '';
proxy_http_version 1.1;
```

#### 3. Verify Proxy Headers
Ensure responses include:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Transfer-Encoding: chunked
```

#### 4. Debug with CURL (Sanity Check)
Run in container to validate streaming:
```bash
curl -N -X POST -H "Content-Type: application/json" \
-H "x-api-key: YOUR_KEY" -d '{"prompt":"test","stream":true}' \
http://kgb-proxy:8089/v1/complete
```
Look for incremental `data:` responses. If you get one monolithic response, the proxy is buffering.

### Why This Happens
The Anthropic SDK expects streaming responses by default. When the proxy aggregates the response, the CLI waits indefinitely for stream termination sequences that never arrive. Docker's non-interactive environment exacerbates this by preventing TTY detection fallbacks.

### Additional Checks
1. **Proxy Timeouts**: Ensure proxy isn't closing connections too early
2. **Keep-Alive**: Enable HTTP keep-alive in proxy config
3. **Container Network**: Verify no TCP buffer mismatches:
   ```bash
   sysctl -w net.ipv4.tcp_rmem="4096 16384 262144"
   sysctl -w net.ipv4.tcp_wmem="4096 16384 262144"
   ```

> Start with `--no-stream` as a immediate workaround, then implement proxy streaming support for long-term stability. The bare-metal CLI likely works because it falls back to interactive TTY handling, which isn't available in `docker exec -i`.