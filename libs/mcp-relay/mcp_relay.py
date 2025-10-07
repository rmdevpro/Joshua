#!/mnt/projects/ICCM/mcp-relay/.venv/bin/python3
"""
MCP Relay - stdio to WebSocket multiplexer for Claude Code.

Acts as an MCP server on stdio, connects to multiple WebSocket MCP backends,
aggregates their tools, and routes tool calls to the appropriate backend.

Design:
- Claude Code connects via stdio (officially supported)
- Relay connects to backends via WebSocket (direct in bare metal, through KGB in containerized)
- Auto-reconnects to backends if they restart
- Exposes all backend tools as a unified interface
"""
import asyncio
import json
import logging
import sys
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

import websockets
from websockets.protocol import State
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Godot logging configuration
GODOT_URL = "ws://localhost:9060"
LOGGING_ENABLED = True  # Set to False to disable Godot logging

async def log_to_godot(level: str, message: str, data: dict = None, trace_id: str = None):
    """Send log to Godot logging infrastructure via MCP tool."""
    if not LOGGING_ENABLED:
        return

    try:
        async with websockets.connect(GODOT_URL, open_timeout=1, max_size=209715200) as ws:
            # Call logger_log tool
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "logger_log",
                    "arguments": {
                        "level": level,
                        "message": message,
                        "component": "mcp-relay",
                        "data": data,
                        "trace_id": trace_id
                    }
                },
                "id": 1
            }
            await ws.send(json.dumps(request))
            response = await asyncio.wait_for(ws.recv(), timeout=1.0)
    except Exception as e:
        # Silently fail - don't disrupt relay operation if logging fails
        logger.debug(f"Godot logging failed: {e}")


class ConfigFileHandler(FileSystemEventHandler):
    """Watches backends.yaml for changes and triggers reload."""

    def __init__(self, relay, config_path: str):
        self.relay = relay
        self.config_path = str(Path(config_path).absolute())

    def on_modified(self, event):
        # Check if the modified file matches our config file
        if not event.is_directory and str(Path(event.src_path).absolute()) == self.config_path:
            logger.info(f"Config file changed: {self.config_path}")
            # Schedule reload in the event loop
            loop = asyncio.get_event_loop()
            loop.create_task(self.relay.reload_config())


class MCPRelay:
    """MCP server that multiplexes stdio to multiple WebSocket backends."""

    def __init__(self, config_path: str = "/mnt/projects/ICCM/mcp-relay/backends.yaml"):
        self.config_path = config_path
        self.backends: Dict[str, dict] = {}  # backend_name -> {url, ws, tools, health, error}
        self.tool_routing: Dict[str, str] = {}  # tool_name -> backend_name
        self.reconnect_delay = 5
        self.initialized = False
        self.stdout_writer = None  # Will be set by run() for sending notifications
        self.load_config()

    async def notify_tools_changed(self):
        """Send notifications/tools/list_changed to Claude Code."""
        if not self.stdout_writer:
            logger.warning("Cannot send notification: stdout_writer not set")
            return

        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed"
        }

        try:
            message = json.dumps(notification) + "\n"
            self.stdout_writer.write(message.encode())
            await self.stdout_writer.drain()
            logger.info("Sent notifications/tools/list_changed to client")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def load_config(self):
        """Load backend configuration."""
        try:
            config = yaml.safe_load(Path(self.config_path).read_text())
            for backend in config['backends']:
                name = backend['name']
                self.backends[name] = {
                    'url': backend['url'],
                    'ws': None,
                    'tools': [],
                    'health': 'unknown',  # unknown, healthy, degraded, failed
                    'error': None
                }
            logger.info(f"Loaded {len(self.backends)} backends: {list(self.backends.keys())}")
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            sys.exit(1)

    async def reload_config(self):
        """Reload configuration and reconnect to changed backends."""
        logger.info("Reloading configuration...")

        try:
            # Load new config
            config = yaml.safe_load(Path(self.config_path).read_text())
            new_backends = {}

            for backend in config['backends']:
                name = backend['name']
                new_url = backend['url']
                new_backends[name] = new_url

            # Compare with current backends and reconnect if URL changed
            for name, new_url in new_backends.items():
                if name in self.backends:
                    old_url = self.backends[name]['url']
                    if old_url != new_url:
                        logger.info(f"Backend {name} URL changed: {old_url} → {new_url}")
                        # Close old connection
                        if self.backends[name]['ws']:
                            await self.backends[name]['ws'].close()
                        # Update URL and reconnect
                        self.backends[name]['url'] = new_url
                        self.backends[name]['ws'] = None
                        self.backends[name]['tools'] = []
                        await self.reconnect_backend(name)
                else:
                    # New backend added
                    logger.info(f"New backend added: {name}")
                    self.backends[name] = {
                        'url': new_url,
                        'ws': None,
                        'tools': [],
                        'health': 'unknown',
                        'error': None
                    }
                    await self.reconnect_backend(name)

            # Remove backends that no longer exist in config
            removed = set(self.backends.keys()) - set(new_backends.keys())
            for name in removed:
                logger.info(f"Backend removed: {name}")
                if self.backends[name]['ws']:
                    await self.backends[name]['ws'].close()
                del self.backends[name]
                # Remove tools from routing table
                self.tool_routing = {k: v for k, v in self.tool_routing.items() if v != name}

            logger.info("Configuration reloaded successfully")

        except Exception as e:
            logger.error(f"Config reload failed: {e}", exc_info=True)

    async def connect_backend(self, backend_name: str) -> bool:
        """Connect to a backend MCP server with error resilience."""
        backend = self.backends[backend_name]
        url = backend['url']

        try:
            ws = await websockets.connect(url, max_size=209715200)
            backend['ws'] = ws
            logger.info(f"Connected to {backend_name}: {url}")

            # Send initialize to backend
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-relay",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
            await ws.send(json.dumps(init_request))

            # Handle initialize response with error boundary
            try:
                response_text = await ws.recv()
                response = json.loads(response_text)

                if 'error' in response:
                    # Backend returned error for initialize - mark as degraded
                    error_msg = response['error'].get('message', 'Unknown error')
                    logger.error(f"{backend_name} initialize failed: {error_msg}")
                    backend['health'] = 'degraded'
                    backend['error'] = f"Initialize error: {error_msg}"
                    await ws.close()
                    backend['ws'] = None
                    return False

                logger.info(f"{backend_name} initialized successfully")

            except json.JSONDecodeError as e:
                logger.error(f"{backend_name} returned invalid JSON during initialize: {e}")
                backend['health'] = 'failed'
                backend['error'] = f"Invalid JSON response: {e}"
                await ws.close()
                backend['ws'] = None
                return False

            # Send initialized notification
            await ws.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }))

            # Consume any response to the notification (some servers send errors for unknown notifications)
            try:
                notification_response = await asyncio.wait_for(ws.recv(), timeout=0.5)
                logger.debug(f"{backend_name} notification response: {notification_response}")
            except asyncio.TimeoutError:
                pass  # No response is fine for notifications

            # Discover tools with error boundary
            success = await self.discover_tools(backend_name)
            if not success:
                # Tool discovery failed - mark as degraded but keep connection
                backend['health'] = 'degraded'
                backend['error'] = 'Tool discovery failed'
                logger.warning(f"{backend_name} marked as degraded: tool discovery failed")
                return True  # Still return True - we're connected, just degraded

            # Fully healthy
            backend['health'] = 'healthy'
            backend['error'] = None
            logger.info(f"{backend_name} is healthy with {len(backend['tools'])} tools")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {backend_name}: {e}")
            backend['ws'] = None
            backend['health'] = 'failed'
            backend['error'] = f"Connection failed: {e}"
            return False

    async def discover_tools(self, backend_name: str) -> bool:
        """Discover tools from a backend with error resilience."""
        backend = self.backends[backend_name]
        ws = backend['ws']

        if not ws:
            return False

        try:
            # Request tools list
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            await ws.send(json.dumps(request))

            # Handle response with error boundary
            try:
                response_text = await ws.recv()
                response = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"{backend_name} returned invalid JSON during tool discovery: {e}")
                return False

            logger.debug(f"Tool discovery response from {backend_name}: {json.dumps(response)[:200]}")

            # Check for error response
            if 'error' in response:
                error_msg = response['error'].get('message', 'Unknown error')
                logger.error(f"{backend_name} tool discovery error: {error_msg}")
                return False

            # Validate response structure
            if 'result' not in response or 'tools' not in response['result']:
                logger.error(f"{backend_name} invalid tools/list response structure: {response}")
                return False

            tools = response['result']['tools']
            old_tool_count = len(backend.get('tools', []))
            backend['tools'] = tools

            # Update routing table
            for tool in tools:
                tool_name = tool['name']
                self.tool_routing[tool_name] = backend_name
                logger.info(f"Registered tool: {tool_name} → {backend_name}")

            # Notify client if tools changed (and we're initialized)
            if self.initialized and len(tools) != old_tool_count:
                await self.notify_tools_changed()

            return True

        except Exception as e:
            logger.error(f"Failed to discover tools from {backend_name}: {e}")
            return False

    async def connect_all_backends(self):
        """Connect to all configured backends with graceful degradation."""
        tasks = [self.connect_backend(name) for name in self.backends.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results, treating exceptions as failures
        connected = sum(1 for r in results if r is True)
        logger.info(f"Connected to {connected}/{len(self.backends)} backends")

        # Log health status
        for name, backend in self.backends.items():
            health = backend.get('health', 'unknown')
            if health == 'healthy':
                logger.info(f"✅ {name}: healthy ({len(backend['tools'])} tools)")
            elif health == 'degraded':
                logger.warning(f"⚠️  {name}: degraded - {backend.get('error', 'unknown error')}")
            elif health == 'failed':
                logger.error(f"❌ {name}: failed - {backend.get('error', 'unknown error')}")
            else:
                logger.warning(f"❓ {name}: {health}")

    async def reconnect_backend(self, backend_name: str):
        """Reconnect to a backend with retry logic."""
        while True:
            if await self.connect_backend(backend_name):
                return
            logger.info(f"Retrying {backend_name} in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)

    def get_all_tools(self) -> List[dict]:
        """Aggregate tools from all backends plus relay management tools."""
        tools = []

        # Add relay management tools
        relay_tools = [
            {
                "name": "relay_add_server",
                "description": "Add a new MCP server to the relay and connect to it",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for this MCP server (e.g., 'fiedler', 'dewey')"
                        },
                        "url": {
                            "type": "string",
                            "description": "WebSocket URL of the MCP server (e.g., 'ws://localhost:9010')"
                        }
                    },
                    "required": ["name", "url"]
                }
            },
            {
                "name": "relay_remove_server",
                "description": "Remove an MCP server from the relay",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the MCP server to remove"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "relay_list_servers",
                "description": "List all MCP servers managed by the relay with their status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "relay_reconnect_server",
                "description": "Force reconnect to an MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the MCP server to reconnect"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "relay_get_status",
                "description": "Get detailed status of all MCP servers",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

        tools.extend(relay_tools)

        # Add tools from all connected servers
        for backend in self.backends.values():
            tools.extend(backend['tools'])

        return tools

    def save_backends_to_yaml(self):
        """Save current runtime backend configuration to backends.yaml"""
        config = {
            'backends': [
                {'name': name, 'url': backend['url']}
                for name, backend in self.backends.items()
            ]
        }

        # Atomic write: write to temp file, then rename
        config_file = Path(__file__).parent / 'backends.yaml'
        temp_file = config_file.with_suffix('.yaml.tmp')

        try:
            with open(temp_file, 'w') as f:
                # Write header comment
                f.write("# MCP Relay Backend Configuration\n")
                f.write("#\n")
                f.write("# This file is automatically updated by relay management tools.\n")
                f.write("# Manual edits will be overwritten.\n\n")

                # Write YAML
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Atomic rename
            temp_file.rename(config_file)
            return True
        except Exception as e:
            logging.error(f"Failed to save backends.yaml: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    async def handle_add_server(self, arguments: dict) -> dict:
        """Handle relay_add_server tool call."""
        name = arguments.get("name")
        url = arguments.get("url")

        if name in self.backends:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"Server '{name}' already exists. Use relay_reconnect_server to reconnect or relay_remove_server first."
                    }]
                }
            }

        # Add new server
        self.backends[name] = {
            'url': url,
            'ws': None,
            'tools': [],
            'health': 'unknown',
            'error': None
        }

        # Connect to it
        success = await self.connect_backend(name)

        if success:
            # Save to backends.yaml for persistence
            self.save_backends_to_yaml()

            # Notify Claude Code that tools have changed
            await self.notify_tools_changed()

            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"✅ Server '{name}' added and connected successfully\nURL: {url}\nTools discovered: {len(self.backends[name]['tools'])}\n\n💾 Configuration saved to backends.yaml"
                    }]
                }
            }
        else:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Server '{name}' added but connection failed\nURL: {url}\nWill retry automatically..."
                    }]
                }
            }

    async def handle_remove_server(self, arguments: dict) -> dict:
        """Handle relay_remove_server tool call."""
        name = arguments.get("name")

        if name not in self.backends:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"❌ Server '{name}' not found"
                    }]
                }
            }

        # Close connection
        if self.backends[name]['ws']:
            await self.backends[name]['ws'].close()

        # Remove from routing table
        self.tool_routing = {k: v for k, v in self.tool_routing.items() if v != name}

        # Remove server
        del self.backends[name]

        # Save to backends.yaml for persistence
        self.save_backends_to_yaml()

        # Notify Claude Code that tools have changed
        await self.notify_tools_changed()

        return {
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"✅ Server '{name}' removed successfully\n\n💾 Configuration saved to backends.yaml"
                }]
            }
        }

    async def handle_list_servers(self, arguments: dict) -> dict:
        """Handle relay_list_servers tool call."""
        servers = []
        for name, backend in self.backends.items():
            ws = backend['ws']
            connected = ws is not None and ws.state == State.OPEN
            health = backend.get('health', 'unknown')
            error = backend.get('error')

            servers.append({
                "name": name,
                "url": backend['url'],
                "connected": connected,
                "health": health,
                "error": error,
                "tools": len(backend['tools'])
            })

        text = "**MCP Relay - Connected Servers:**\n\n"
        for s in servers:
            # Status icon based on health
            if s['health'] == 'healthy':
                status_icon = "✅"
            elif s['health'] == 'degraded':
                status_icon = "⚠️"
            elif s['health'] == 'failed':
                status_icon = "❌"
            else:
                status_icon = "❓"

            status = "Connected" if s['connected'] else "Disconnected"
            text += f"- **{s['name']}**: {status_icon} {status} ({s['health']})\n"
            text += f"  - URL: {s['url']}\n"
            text += f"  - Tools: {s['tools']}\n"
            if s['error']:
                text += f"  - Error: {s['error']}\n"
            text += "\n"

        return {
            "result": {
                "content": [{
                    "type": "text",
                    "text": text
                }]
            }
        }

    async def handle_reconnect_server(self, arguments: dict) -> dict:
        """Handle relay_reconnect_server tool call."""
        name = arguments.get("name")

        if name not in self.backends:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"❌ Server '{name}' not found"
                    }]
                }
            }

        # Close existing connection
        if self.backends[name]['ws']:
            await self.backends[name]['ws'].close()
            self.backends[name]['ws'] = None

        # Reconnect
        success = await self.connect_backend(name)

        if success:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"✅ Server '{name}' reconnected successfully\nTools: {len(self.backends[name]['tools'])}"
                    }]
                }
            }
        else:
            return {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"❌ Failed to reconnect to '{name}'"
                    }]
                }
            }

    async def handle_get_status(self, arguments: dict) -> dict:
        """Handle relay_get_status tool call."""
        # Helper to check if websocket is connected
        def is_connected(ws):
            return ws is not None and ws.state == State.OPEN

        status = {
            "total_servers": len(self.backends),
            "connected_servers": sum(1 for b in self.backends.values() if is_connected(b['ws'])),
            "healthy_servers": sum(1 for b in self.backends.values() if b.get('health') == 'healthy'),
            "degraded_servers": sum(1 for b in self.backends.values() if b.get('health') == 'degraded'),
            "failed_servers": sum(1 for b in self.backends.values() if b.get('health') == 'failed'),
            "total_tools": sum(len(b['tools']) for b in self.backends.values()),
            "servers": []
        }

        for name, backend in self.backends.items():
            connected = is_connected(backend['ws'])
            server_info = {
                "name": name,
                "url": backend['url'],
                "connected": connected,
                "health": backend.get('health', 'unknown'),
                "tools": len(backend['tools']),
                "tool_names": [t['name'] for t in backend['tools']]
            }
            if backend.get('error'):
                server_info['error'] = backend['error']
            status["servers"].append(server_info)

        import json
        return {
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"**MCP Relay Status:**\n\n```json\n{json.dumps(status, indent=2)}\n```"
                }]
            }
        }

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Route tool call to appropriate backend or handle relay management tools."""
        trace_id = str(uuid.uuid4())

        # Log tool call initiation
        asyncio.create_task(log_to_godot(
            "TRACE",
            f"Tool call received: {tool_name}",
            {"tool_name": tool_name, "arguments": arguments},
            trace_id
        ))

        # Handle relay management tools
        if tool_name == "relay_add_server":
            return await self.handle_add_server(arguments)
        elif tool_name == "relay_remove_server":
            return await self.handle_remove_server(arguments)
        elif tool_name == "relay_list_servers":
            return await self.handle_list_servers(arguments)
        elif tool_name == "relay_reconnect_server":
            return await self.handle_reconnect_server(arguments)
        elif tool_name == "relay_get_status":
            return await self.handle_get_status(arguments)

        # Route to backend server
        backend_name = self.tool_routing.get(tool_name)

        if not backend_name:
            asyncio.create_task(log_to_godot(
                "ERROR",
                f"Unknown tool: {tool_name}",
                {"tool_name": tool_name, "available_tools": list(self.tool_routing.keys())},
                trace_id
            ))
            raise ValueError(f"Unknown tool: {tool_name}")

        backend = self.backends[backend_name]
        ws = backend['ws']

        asyncio.create_task(log_to_godot(
            "TRACE",
            f"Routing tool to backend: {backend_name}",
            {"tool_name": tool_name, "backend": backend_name, "backend_url": backend['url']},
            trace_id
        ))

        if not ws:
            # Try to reconnect
            logger.warning(f"Backend {backend_name} disconnected, reconnecting...")
            await self.reconnect_backend(backend_name)
            ws = backend['ws']

        # Forward tool call to backend
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        }

        asyncio.create_task(log_to_godot(
            "TRACE",
            f"Sending request to backend: {backend_name}",
            {"request": request},
            trace_id
        ))

        try:
            await ws.send(json.dumps(request))
            response = json.loads(await ws.recv())

            asyncio.create_task(log_to_godot(
                "TRACE",
                f"Received response from backend: {backend_name}",
                {"response": response, "has_error": "error" in response},
                trace_id
            ))

            return response
        except (websockets.exceptions.ConnectionClosed,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK) as e:
            # Connection lost - reconnect and retry
            logger.warning(f"Backend {backend_name} connection lost: {e}, reconnecting...")
            asyncio.create_task(log_to_godot(
                "WARN",
                f"Backend connection lost, reconnecting: {backend_name}",
                {"backend": backend_name, "error": str(e)},
                trace_id
            ))

            backend['ws'] = None  # Mark as disconnected
            await self.reconnect_backend(backend_name)
            ws = backend['ws']

            # Retry the tool call once
            logger.info(f"Retrying tool call: {tool_name}")
            await ws.send(json.dumps(request))
            response = json.loads(await ws.recv())

            asyncio.create_task(log_to_godot(
                "TRACE",
                f"Retry successful for tool: {tool_name}",
                {"response": response},
                trace_id
            ))

            return response
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {e}")
            asyncio.create_task(log_to_godot(
                "ERROR",
                f"Tool call failed: {tool_name}",
                {"tool_name": tool_name, "backend": backend_name, "error": str(e), "error_type": type(e).__name__},
                trace_id
            ))
            raise

    async def handle_request(self, request: dict) -> Optional[dict]:
        """Handle MCP request from Claude."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "initialize":
                # Initialize relay
                if not self.initialized:
                    await self.connect_all_backends()
                    self.initialized = True

                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "mcp-relay",
                            "version": "1.0.0"
                        }
                    },
                    "id": request_id
                }

            elif method == "notifications/initialized":
                # No response needed for notifications
                return None

            elif method == "tools/list":
                tools = self.get_all_tools()
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": tools
                    },
                    "id": request_id
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                logger.info(f"Calling tool: {tool_name}")
                response = await self.call_tool(tool_name, arguments)

                # Forward backend response (preserve id)
                if "result" in response:
                    return {
                        "jsonrpc": "2.0",
                        "result": response["result"],
                        "id": request_id
                    }
                elif "error" in response:
                    return {
                        "jsonrpc": "2.0",
                        "error": response["error"],
                        "id": request_id
                    }
                else:
                    return response

            else:
                logger.warning(f"Unknown method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }

    async def run(self):
        """Main stdio loop."""
        logger.info("MCP Relay starting on stdio")

        # Start file watcher for config changes
        config_dir = str(Path(self.config_path).parent)
        event_handler = ConfigFileHandler(self, self.config_path)
        observer = Observer()
        observer.schedule(event_handler, config_dir, recursive=False)
        observer.start()
        logger.info(f"Watching config file: {self.config_path}")

        # Read from stdin, write to stdout
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, asyncio.get_event_loop())

        # Store writer for sending notifications
        self.stdout_writer = writer

        logger.info("MCP Relay ready")

        try:
            while True:
                # Read JSON-RPC request (line-delimited)
                line = await reader.readline()
                if not line:
                    break

                try:
                    request = json.loads(line.decode('utf-8'))
                    logger.info(f"Received request: {request.get('method')}")

                    response = await self.handle_request(request)

                    if response:
                        writer.write(json.dumps(response).encode('utf-8') + b'\n')
                        await writer.drain()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Request handling error: {e}", exc_info=True)

        finally:
            # Cleanup
            observer.stop()
            observer.join()
            for backend in self.backends.values():
                if backend['ws']:
                    await backend['ws'].close()
            logger.info("MCP Relay shutdown")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Relay - stdio to WebSocket multiplexer")
    parser.add_argument("--config", default="/mnt/projects/ICCM/mcp-relay/backends.yaml",
                       help="Path to backends configuration file")
    args = parser.parse_args()

    relay = MCPRelay(config_path=args.config)
    asyncio.run(relay.run())
