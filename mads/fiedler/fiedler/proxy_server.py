"""Fiedler HTTP Streaming Proxy - Routes LLM requests through Fiedler."""
import asyncio
import os
import aiohttp
from aiohttp import web

from joshua_logger import Logger
logger = Logger()


class AnthropicStreamingProxy:
    """HTTP streaming proxy for Anthropic API."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8081):
        self.host = host
        self.port = port
        self.upstream = "https://api.anthropic.com"
        self.app = None
        self.runner = None
        asyncio.create_task(logger.log("INFO", f"Anthropic Streaming Proxy initialized on {host}:{port} -> {self.upstream}", "fiedler-proxy"))

    async def start(self):
        """Start the proxy server."""
        self.app = web.Application()

        # Routes
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_route('*', '/{path:.*}', self.proxy_request)

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        await logger.log("INFO", f"Anthropic Streaming Proxy started on {self.host}:{self.port}", "fiedler-proxy")

    async def stop(self):
        """Stop the proxy server."""
        if self.runner:
            await self.runner.cleanup()
        await logger.log("INFO", "Anthropic Streaming Proxy stopped", "fiedler-proxy")

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "upstream": self.upstream,
            "proxy": "fiedler-anthropic-streaming"
        })

    async def proxy_request(self, request: web.Request) -> web.Response:
        """Proxy request to Anthropic API with streaming."""
        path = request.match_info.get('path', '')

        try:
            # Build upstream URL
            upstream_url = f"{self.upstream}/{path}"
            if request.query_string:
                upstream_url += f"?{request.query_string}"

            # Read request body
            request_body = await request.read()

            # Filter headers - remove Host and other proxy-specific headers
            forward_headers = {}
            for key, value in request.headers.items():
                forward_headers[key] = value

            # Remove headers that should not be forwarded (case-insensitive)
            headers_to_remove = ['host', 'connection', 'keep-alive', 'proxy-connection']
            forward_headers = {k: v for k, v in forward_headers.items() if k.lower() not in headers_to_remove}

            # Ensure User-Agent is set
            if 'User-Agent' not in forward_headers and 'user-agent' not in forward_headers:
                forward_headers['User-Agent'] = 'Fiedler-Proxy/1.0'

            # Force identity encoding to prevent gzip compression (critical for streaming)
            forward_headers['Accept-Encoding'] = 'identity'

            await logger.log("INFO", f"Proxying {request.method} /{path} to {upstream_url}", "fiedler-proxy")

            # Forward request to upstream
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=upstream_url,
                    headers=forward_headers,
                    data=request_body,
                    allow_redirects=True
                ) as upstream_response:

                    # Create streaming response to client
                    # Filter out headers that shouldn't be forwarded when re-streaming
                    response_headers = dict(upstream_response.headers)
                    headers_to_remove = ['Content-Length', 'Content-Encoding', 'Transfer-Encoding']
                    for header in headers_to_remove:
                        response_headers.pop(header, None)
                        # Case-insensitive removal
                        for key in list(response_headers.keys()):
                            if key.lower() == header.lower():
                                response_headers.pop(key, None)

                    # Add SSE-specific headers to prevent downstream buffering
                    response_headers['Cache-Control'] = 'no-cache'
                    response_headers['X-Accel-Buffering'] = 'no'

                    response = web.StreamResponse(
                        status=upstream_response.status,
                        headers=response_headers
                    )
                    await response.prepare(request)

                    # Stream response chunks to client
                    # Use iter_any() for immediate, unbuffered streaming
                    async for chunk in upstream_response.content.iter_any():
                        if chunk:  # iter_any() can yield empty bytes
                            await response.write(chunk)

                    # Complete the streaming response
                    await response.write_eof()

                    await logger.log("INFO", f"Completed proxying {request.method} /{path} - Status {upstream_response.status}", "fiedler-proxy")

                    return response

        except Exception as e:
            await logger.log("ERROR", f"Proxy error for {request.method} /{path}: {e}", "fiedler-proxy")
            return web.json_response({
                "error": "Proxy Error",
                "message": str(e)
            }, status=500)


async def start_proxy_server(host: str = "0.0.0.0", port: int = 8081):
    """Start HTTP streaming proxy server."""
    proxy = AnthropicStreamingProxy(host, port)
    await proxy.start()
    return proxy
