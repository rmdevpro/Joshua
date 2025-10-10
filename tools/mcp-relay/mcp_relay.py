#!/home/aristotle9/mcp-relay/.venv/bin/python3
"""
MCP Relay V3 - stdio to WebSocket multiplexer for Claude Code.

Acts as an MCP server on stdio, connects to multiple WebSocket MCP backends,
aggregates their tools, and routes tool calls to the appropriate backend.

V3.7 Changes:
- CRITICAL BUG FIX: Added missing "jsonrpc": "2.0" field to all relay management tool responses.
- Relay tools (relay_get_status, relay_list_servers, etc) were returning incomplete JSON-RPC responses.
- Without the jsonrpc field, Claude Code silently ignored all relay tool responses.
- All 5 management tool handlers now return proper MCP protocol-compliant responses.
- Updated version to 3.7.0.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
import fcntl
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import websockets
from websockets.protocol import State
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add joshua_logger to path
sys.path.insert(0, '/mnt/projects/Joshua/lib')
from joshua_logger import Logger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


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

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Use local path relative to script
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backends.yaml")
        self.config_path = config_path
        self.logger = Logger()  # Instantiate the logger for this relay instance
        # backend_name -> {url, ws, tools, invalid_tools, validation_errors, health, error, keep_alive_task}
        self.backends: Dict[str, dict] = {}
        self.tool_routing: Dict[str, str] = {}  # tool_name -> backend_name
        self.routing_lock = asyncio.Lock()
        self.reload_lock = asyncio.Lock()
        self.reconnect_locks: Dict[str, asyncio.Lock] = {}
        self.request_id_counter = 0
        self.reconnect_delay = 5
        self.initialized = False
        self.stdout_writer = None  # Will be set by run() for sending notifications
        self.last_invalid_count = 0
        self.tool_call_reconnect_timeout = 10  # seconds - timeout for reconnects during tool calls
        self.websocket_timeout = 900  # seconds (15 minutes) - timeout for WebSocket send/recv operations (LLM calls can be slow)
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
                    'invalid_tools': [],
                    'validation_errors': [],
                    'health': 'unknown',  # unknown, healthy, degraded, failed
                    'error': None,
                    'keep_alive_task': None
                }
            logger.info(f"Loaded {len(self.backends)} backends: {list(self.backends.keys())}")
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            sys.exit(1)

    async def reload_config(self):
        """Reload configuration and reconnect to changed backends."""
        async with self.reload_lock:  # Prevent concurrent reloads
            logger.info("Reloading configuration...")

            try:
                # Load new config
                config = yaml.safe_load(Path(self.config_path).read_text())
                new_backends = {backend['name']: backend['url'] for backend in config['backends']}
                old_backend_names = set(self.backends.keys())

                # Compare with current backends and reconnect if URL changed
                for name, new_url in new_backends.items():
                    if name in self.backends:
                        old_backend = self.backends[name]
                        if old_backend['url'] != new_url:
                            logger.info(f"Backend {name} URL changed: {old_backend['url']} → {new_url}")
                            # Close old connection and cancel keepalive
                            if old_backend.get('ws'):
                                await old_backend['ws'].close()
                            if old_backend.get('keep_alive_task'):
                                task = old_backend['keep_alive_task']
                                task.cancel()
                                # Don't await - let it finish in background
                                # Task is designed to break when connection closed

                            # Update URL and reconnect
                            old_backend['url'] = new_url
                            old_backend['ws'] = None
                            old_backend['tools'] = []
                            old_backend['invalid_tools'] = []
                            old_backend['validation_errors'] = []
                            # V3.4 Fix (MEDIUM): Make reconnect non-blocking
                            asyncio.create_task(self.reconnect_backend(name))
                    else:
                        # New backend added
                        logger.info(f"New backend added: {name}")
                        self.backends[name] = {
                            'url': new_url, 'ws': None, 'tools': [], 'invalid_tools': [],
                            'validation_errors': [], 'health': 'unknown', 'error': None,
                            'keep_alive_task': None
                        }
                        # V3.4 Fix (MEDIUM): Make reconnect non-blocking
                        asyncio.create_task(self.reconnect_backend(name))

                # Remove backends that no longer exist in config
                removed = old_backend_names - set(new_backends.keys())
                for name in removed:
                    logger.info(f"Backend removed: {name}")
                    backend_to_remove = self.backends[name]
                    if backend_to_remove.get('ws'):
                        await backend_to_remove['ws'].close()
                    if backend_to_remove.get('keep_alive_task'):
                        task = backend_to_remove['keep_alive_task']
                        task.cancel()
                        # Don't await - let it finish in background
                        # Task is designed to break when connection closed

                    # V3.4 Fix (HIGH): Purge tools from routing table FIRST to prevent
                    # a race condition where a tool call could find a tool whose
                    # backend has already been deleted.
                    await self._purge_backend_tools(name)
                    del self.backends[name]

                # Track if we made changes and notify client
                backends_changed = bool(removed) or any(
                    name for name in new_backends if name not in old_backend_names
                )
                if backends_changed:
                    await self.notify_tools_changed()

                logger.info("Configuration reloaded successfully")

            except Exception as e:
                logger.error(f"Config reload failed: {e}", exc_info=True)

    def validate_tool_schema(self, tool_name: str, tool_def: dict) -> Tuple[bool, str]:
        """Validate a tool's schema according to MCP requirements."""
        if 'description' not in tool_def: return False, "Missing 'description' field"
        if 'inputSchema' not in tool_def: return False, "Missing 'inputSchema' field"
        input_schema = tool_def.get('inputSchema')
        if not isinstance(input_schema, dict): return False, f"inputSchema must be a dict, got {type(input_schema).__name__}"
        schema_type = input_schema.get('type')
        if schema_type != 'object':
            return False, f"inputSchema.type must be 'object', got '{schema_type}'" if schema_type else "inputSchema missing 'type' field (expected 'object')"
        properties = input_schema.get('properties')
        if properties is not None and not isinstance(properties, dict): return False, "inputSchema.properties must be a dict if present"
        required_fields = input_schema.get('required')
        if required_fields is not None:
            if not isinstance(required_fields, list): return False, "inputSchema.required must be a list if present"
            if not all(isinstance(item, str) for item in required_fields): return False, "inputSchema.required must be a list of strings"
            if properties:
                for req_field in required_fields:
                    if req_field not in properties: return False, f"Required field '{req_field}' not found in inputSchema.properties"
        return True, ""

    def _get_next_request_id(self) -> int:
        """Get a unique ID for a JSON-RPC request."""
        self.request_id_counter += 1
        return self.request_id_counter

    async def _purge_backend_tools(self, backend_name: str):
        """Remove all tools for a given backend from the routing table."""
        async with self.routing_lock:
            tools_to_remove = [
                tool_name for tool_name, owner in self.tool_routing.items()
                if owner == backend_name
            ]
            for tool_name in tools_to_remove:
                del self.tool_routing[tool_name]
            if tools_to_remove:
                logger.info(f"Purged {len(tools_to_remove)} tools for backend: {backend_name}")

    async def keep_alive(self, backend_name: str):
        """Send periodic pings to keep WebSocket alive."""
        backend = self.backends[backend_name]
        while True:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                ws = backend.get('ws')
                if ws and ws.state == State.OPEN:
                    await ws.ping()
                else:
                    logger.debug(f"Keepalive for {backend_name} stopping, connection closed.")
                    break
            except asyncio.CancelledError:
                logger.debug(f"Keepalive task for {backend_name} cancelled.")
                break
            except Exception as e:
                logger.warning(f"Keepalive ping failed for {backend_name}: {e}")
                break

    async def _perform_handshake(self, backend_name: str, ws) -> bool:
        """Handle MCP initialize handshake."""
        try:
            init_request = {
                "jsonrpc": "2.0", "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "mcp-relay", "version": "3.0.0"}
                }, "id": self._get_next_request_id()
            }
            await ws.send(json.dumps(init_request))
            response = json.loads(await ws.recv())

            if 'error' in response:
                error_msg = response['error'].get('message', 'Unknown error')
                logger.error(f"{backend_name} initialize failed: {error_msg}")
                self.backends[backend_name]['error'] = f"Initialize error: {error_msg}"
                return False

            logger.info(f"{backend_name} initialized successfully")
            await ws.send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            return True
        except json.JSONDecodeError as e:
            logger.error(f"{backend_name} returned invalid JSON during initialize: {e}")
            self.backends[backend_name]['error'] = f"Invalid JSON response: {e}"
            return False
        except Exception as e:
            logger.error(f"{backend_name} handshake failed: {e}")
            self.backends[backend_name]['error'] = f"Handshake failed: {e}"
            return False

    async def _fetch_and_validate_tools(self, backend_name: str) -> None:
        """Discover tools and update backend health status."""
        backend = self.backends[backend_name]
        success, details = await self.discover_tools(backend_name)

        if not success:
            backend['health'] = 'degraded'
            backend['error'] = f"Tool discovery failed: {details.get('error', 'unknown error')}"
            logger.warning(f"{backend_name} marked as degraded: tool discovery failed")
            return

        invalid_count = details.get('invalid_count', 0)
        if invalid_count > 0:
            backend['health'] = 'degraded'
            errors_summary = f"{invalid_count} tool(s) have invalid schemas or naming conflicts"
            backend['error'] = errors_summary
            logger.warning(f"{backend_name} marked as degraded: {errors_summary}")
            for error in details.get('errors', []):
                logger.warning(f"  {error}")
        else:
            backend['health'] = 'healthy'
            backend['error'] = None

        valid_count = details.get('valid_count', 0)
        logger.info(f"{backend_name} connected with {valid_count} valid tools" +
                   (f" ({invalid_count} invalid)" if invalid_count > 0 else ""))

    async def connect_backend(self, backend_name: str) -> bool:
        """Connect to a backend MCP server."""
        await self._purge_backend_tools(backend_name)

        backend = self.backends[backend_name]
        url = backend['url']

        if backend.get('keep_alive_task'):
            task = backend['keep_alive_task']
            task.cancel()
            # Don't await, let it finish in background
            backend['keep_alive_task'] = None

        try:
            ws = await websockets.connect(url, max_size=209715200)
            backend['ws'] = ws
            logger.info(f"Connected to {backend_name}: {url}")

            if not await self._perform_handshake(backend_name, ws):
                backend['health'] = 'failed'
                await ws.close()
                backend['ws'] = None
                return False

            await self._fetch_and_validate_tools(backend_name)

            backend['keep_alive_task'] = asyncio.create_task(self.keep_alive(backend_name))

            return True

        except Exception as e:
            logger.error(f"Failed to connect to {backend_name}: {e}")
            backend['ws'] = None
            backend['health'] = 'failed'
            backend['error'] = f"Connection failed: {e}"
            return False

    async def discover_tools(self, backend_name: str) -> Tuple[bool, dict]:
        """Discover tools from a backend with validation and race condition protection."""
        backend = self.backends[backend_name]
        ws = backend['ws']
        if not ws: return False, {"error": "No websocket connection"}

        try:
            request = {"jsonrpc": "2.0", "method": "tools/list", "id": self._get_next_request_id()}
            await ws.send(json.dumps(request))
            response = json.loads(await ws.recv())

            if 'error' in response:
                error_msg = response['error'].get('message', 'Unknown error')
                return False, {"error": error_msg}
            if 'result' not in response or 'tools' not in response['result']:
                return False, {"error": "Invalid response structure"}

            tools = response['result']['tools']
            old_tool_count = len(backend.get('tools', []))
            tools_added_to_routing = False  # Track if we added new tools to routing table

            valid_tools, invalid_tools, validation_errors = [], [], []
            seen_tools = set()

            for tool in tools:
                tool_name = tool.get('name', '<unnamed>')

                if tool_name in seen_tools:
                    error_msg = f"Duplicate tool within same backend: '{tool_name}'"
                    invalid_tools.append(tool)
                    validation_errors.append(f"- {tool_name}: {error_msg}")
                    logger.error(f"Invalid tool from {backend_name}: {error_msg}")
                    continue
                seen_tools.add(tool_name)

                is_valid, error_msg = self.validate_tool_schema(tool_name, tool)
                if not is_valid:
                    invalid_tools.append(tool)
                    validation_errors.append(f"- {tool_name}: {error_msg}")
                    logger.warning(f"Invalid tool from {backend_name}: {tool_name} - {error_msg}")
                    continue

                has_collision = False
                colliding_backend = None
                async with self.routing_lock:
                    if tool_name in self.tool_routing and self.tool_routing[tool_name] != backend_name:
                        colliding_backend = self.tool_routing[tool_name]
                        has_collision = True
                    else:
                        # Check if this is a NEW tool being added
                        if tool_name not in self.tool_routing:
                            tools_added_to_routing = True
                        self.tool_routing[tool_name] = backend_name
                        has_collision = False

                if has_collision:
                    error_msg = f"Tool name collision: '{tool_name}' is already provided by backend '{colliding_backend}'"
                    invalid_tools.append(tool)
                    validation_errors.append(f"- {tool_name}: {error_msg}")
                    logger.error(f"Invalid tool from {backend_name}: {error_msg}")
                else:
                    valid_tools.append(tool)

            for tool in valid_tools:
                logger.debug(f"Registered tool: {tool['name']} → {backend_name}")

            backend['tools'] = valid_tools
            backend['invalid_tools'] = invalid_tools
            backend['validation_errors'] = validation_errors

            # Send notification if we added NEW tools to the routing table
            if self.initialized and tools_added_to_routing:
                await self.notify_tools_changed()

            details = {"valid_count": len(valid_tools), "invalid_count": len(invalid_tools), "errors": validation_errors}
            return True, details

        except json.JSONDecodeError as e: return False, {"error": f"Invalid JSON response: {e}"}
        except Exception as e: return False, {"error": str(e)}

    async def connect_all_backends(self):
        """Connect to all configured backends with graceful degradation."""
        tasks = [self.connect_backend(name) for name in self.backends.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        connected = sum(1 for r in results if r is True)
        logger.info(f"Connected to {connected}/{len(self.backends)} backends")
        for name, backend in self.backends.items():
            health = backend.get('health', 'unknown')
            if health == 'healthy': logger.info(f"✅ {name}: healthy ({len(backend['tools'])} tools)")
            elif health == 'degraded': logger.warning(f"⚠️  {name}: degraded - {backend.get('error', 'unknown error')}")
            elif health == 'failed': logger.error(f"❌ {name}: failed - {backend.get('error', 'unknown error')}")
            else: logger.warning(f"❓ {name}: {health}")

    async def reconnect_backend(self, backend_name: str):
        """Reconnect to a backend with retry logic."""
        # Create a lock for this backend if not exists
        if backend_name not in self.reconnect_locks:
            self.reconnect_locks[backend_name] = asyncio.Lock()

        lock = self.reconnect_locks[backend_name]

        # Prevent concurrent reconnection attempts for the same backend.
        # Multiple tool calls to a failed backend could trigger simultaneous
        # reconnects, causing duplicate connections and resource leaks.
        async with lock:  # Ensure only one reconnect attempt per backend at a time
            while True:
                # Check if backend still exists before attempting reconnect
                if backend_name not in self.backends:
                    logger.info(f"Backend {backend_name} no longer exists, stopping reconnection attempts")
                    return

                if await self.connect_backend(backend_name):
                    return
                logger.info(f"Retrying {backend_name} in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)

    def get_all_tools(self) -> List[dict]:
        """Aggregate tools from all backends plus relay management tools."""
        tools = [
            {"name": "relay_add_server", "description": "Add a new MCP server to the relay", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "url": {"type": "string"}}, "required": ["name", "url"]}},
            {"name": "relay_remove_server", "description": "Remove an MCP server from the relay", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
            {"name": "relay_list_servers", "description": "List all MCP servers managed by the relay", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "relay_reconnect_server", "description": "Force reconnect to an MCP server", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
            {"name": "relay_get_status", "description": "Get detailed status of all MCP servers", "inputSchema": {"type": "object", "properties": {}}}
        ]
        total_invalid = 0

        backends_snapshot = dict(self.backends)  # Shallow copy to iterate safely
        for backend_name, backend in backends_snapshot.items():
            tools.extend(backend.get('tools', []))
            invalid_count = len(backend.get('invalid_tools', []))
            if invalid_count > 0:
                total_invalid += invalid_count

        if total_invalid > 0 and total_invalid != self.last_invalid_count:
            logger.warning(f"Excluded {total_invalid} invalid tools from tools/list response")
            self.last_invalid_count = total_invalid
        elif total_invalid == 0:
            self.last_invalid_count = 0

        return tools

    def save_backends_to_yaml(self):
        """Save current runtime backend configuration to backends.yaml with file locking"""
        config = {'backends': [{'name': name, 'url': backend['url']} for name, backend in self.backends.items()]}
        config_file = Path(self.config_path)
        temp_file = config_file.with_suffix('.yaml.tmp')

        try:
            # Use the config file itself for locking (prevents lock file accumulation)
            with open(config_file, 'a+') as lockfile:
                # Acquire exclusive lock (will block if another process has it)
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)

                # Write to temporary file
                with open(temp_file, 'w') as f:
                    f.write("# MCP Relay Backend Configuration\n# This file is automatically updated by relay management tools.\n\n")
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                # Atomically replace the config file
                os.replace(str(temp_file), str(config_file))

                # Lock is automatically released when 'with' block exits
            return True
        except Exception as e:
            logging.error(f"Failed to save backends.yaml: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    async def handle_add_server(self, arguments: dict) -> dict:
        """Handle relay_add_server tool call."""
        async with self.reload_lock:
            name, url = arguments.get("name"), arguments.get("url")
            if name in self.backends:
                return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"Server '{name}' already exists."}]}}
            self.backends[name] = {
                'url': url, 'ws': None, 'tools': [], 'invalid_tools': [], 'validation_errors': [],
                'health': 'unknown', 'error': None, 'keep_alive_task': None
            }
            success = await self.connect_backend(name)
            backend = self.backends[name]
            if success:
                health, valid_count, invalid_count = backend.get('health', 'unknown'), len(backend['tools']), len(backend.get('invalid_tools', []))
                response_text = f"✅ Server '{name}' added and connected\nURL: {url}\n"
                if health == 'degraded' and backend.get('validation_errors'):
                    response_text += f"⚠️ WARNING: Backend degraded\nInvalid tools ({invalid_count}):\n"
                    response_text += "\n".join(f"  {e}" for e in backend['validation_errors'])
                    response_text += f"\nValid tools: {valid_count}/{valid_count + invalid_count}\n"
                else:
                    response_text += f"Tools discovered: {valid_count}\n"
                response_text += f"Health: {health}\n"
                if self.save_backends_to_yaml(): response_text += "\n💾 Configuration saved."
                else: response_text += "\n🚨 WARNING: Failed to save configuration."
                await self.notify_tools_changed()
                return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": response_text}]}}
            else:
                del self.backends[name] # Clean up failed add
                return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"⚠️ Server '{name}' added but connection failed\nError: {backend.get('error', 'Unknown')}\nWill retry..."}]}}

    async def handle_remove_server(self, arguments: dict) -> dict:
        """Handle relay_remove_server tool call."""
        async with self.reload_lock:
            name = arguments.get("name")
            if name not in self.backends:
                return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"❌ Server '{name}' not found"}]}}
            backend = self.backends[name]
            if backend.get('ws'): await backend['ws'].close()
            if backend.get('keep_alive_task'):
                task = backend['keep_alive_task']
                task.cancel()
                # Don't await, let it finish in background
            await self._purge_backend_tools(name)
            del self.backends[name]
            save_success = self.save_backends_to_yaml()
            await self.notify_tools_changed()
            response_text = f"✅ Server '{name}' removed.\n"
            if save_success: response_text += "\n💾 Configuration saved."
            else: response_text += "\n🚨 WARNING: Failed to save configuration."
            return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": response_text}]}}

    async def handle_list_servers(self, arguments: dict) -> dict:
        servers = []
        for name, backend in self.backends.items():
            ws, health = backend.get('ws'), backend.get('health', 'unknown')
            servers.append({
                "name": name, "url": backend['url'], "connected": ws is not None and ws.state == State.OPEN,
                "health": health, "error": backend.get('error'), "valid_tools": len(backend['tools']),
                "invalid_tools": len(backend.get('invalid_tools', []))
            })
        text = "**MCP Relay - Connected Servers:**\n\n"
        for s in servers:
            status_icon = {"healthy": "✅", "degraded": "⚠️", "failed": "❌"}.get(s['health'], "❓")
            status = "Connected" if s['connected'] else "Disconnected"
            text += f"- **{s['name']}**: {status_icon} {status} ({s['health']})\n  - URL: {s['url']}\n  - Valid Tools: {s['valid_tools']}\n"
            if s['invalid_tools'] > 0: text += f"  - Invalid Tools: {s['invalid_tools']}\n"
            if s['error']: text += f"  - Error: {s['error']}\n"
            text += "\n"
        return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": text}]}}

    async def handle_reconnect_server(self, arguments: dict) -> dict:
        """Handle relay_reconnect_server tool call."""
        name = arguments.get("name")
        if name not in self.backends:
            return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"❌ Server '{name}' not found"}]}}
        backend = self.backends[name]
        if backend.get('ws'): await backend['ws'].close()
        if backend.get('keep_alive_task'):
            task = backend['keep_alive_task']
            task.cancel()
            # Don't await, let it finish in background
        backend['ws'], backend['keep_alive_task'] = None, None
        backend['invalid_tools'], backend['validation_errors'] = [], []
        success = await self.connect_backend(name)
        if success:
            health = backend.get('health', 'unknown')
            response_text = f"✅ Server '{name}' reconnected.\nValid Tools: {len(backend['tools'])}\n"
            if len(backend.get('invalid_tools', [])) > 0:
                response_text += f"Invalid Tools: {len(backend['invalid_tools'])}\n"
            response_text += f"Health: {health}"
            return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": response_text}]}}
        else:
            return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"❌ Failed to reconnect to '{name}'"}]}}

    async def handle_get_status(self, arguments: dict) -> dict:
        """Handle relay_get_status tool call."""
        is_connected = lambda ws: ws is not None and ws.state == State.OPEN
        status = {
            "total_servers": len(self.backends),
            "connected_servers": sum(1 for b in self.backends.values() if is_connected(b.get('ws'))),
            "servers": []
        }
        for name, backend in self.backends.items():
            server_info = {
                "name": name, "url": backend['url'], "connected": is_connected(backend.get('ws')),
                "health": backend.get('health', 'unknown'), "tools": len(backend['tools']),
                "tool_names": [t['name'] for t in backend['tools']]
            }
            if backend.get('invalid_tools'):
                server_info['invalid_tools'] = len(backend['invalid_tools'])
                server_info['validation_errors'] = backend.get('validation_errors', [])
            if backend.get('error'): server_info['error'] = backend['error']
            status["servers"].append(server_info)
        return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": f"**MCP Relay Status:**\n\n```json\n{json.dumps(status, indent=2)}\n```"}]}}

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Route tool call to appropriate backend or handle relay management tools."""
        trace_id = str(uuid.uuid4())
        asyncio.create_task(self.logger.log("TRACE", f"Tool call received: {tool_name}", "mcp-relay", data={"tool_name": tool_name, "arguments": arguments}, trace_id=trace_id))

        handlers = {
            "relay_add_server": self.handle_add_server, "relay_remove_server": self.handle_remove_server,
            "relay_list_servers": self.handle_list_servers, "relay_reconnect_server": self.handle_reconnect_server,
            "relay_get_status": self.handle_get_status
        }
        if tool_name in handlers: return await handlers[tool_name](arguments)

        # V3.4 Fix (LOW): Protect read with routing lock for consistency
        async with self.routing_lock:
            backend_name = self.tool_routing.get(tool_name)

        if not backend_name:
            asyncio.create_task(self.logger.log("ERROR", f"Unknown tool: {tool_name}", "mcp-relay", data={"tool_name": tool_name, "available_tools": list(self.tool_routing.keys())}, trace_id=trace_id))
            raise ValueError(f"Unknown tool: {tool_name}")

        # Handle backend removal race condition
        try:
            backend = self.backends[backend_name]
        except KeyError:
            error_msg = f"Backend '{backend_name}' for tool '{tool_name}' has been removed"
            asyncio.create_task(self.logger.log("ERROR", error_msg, "mcp-relay", data={"tool_name": tool_name, "backend": backend_name}, trace_id=trace_id))
            raise RuntimeError(error_msg)

        ws = backend.get('ws')
        asyncio.create_task(self.logger.log("TRACE", f"Routing tool to backend: {backend_name}", "mcp-relay", data={"tool_name": tool_name, "backend": backend_name}, trace_id=trace_id))

        if not ws or ws.state != State.OPEN:
            logger.warning(f"Backend {backend_name} disconnected, reconnecting...")
            try:
                await asyncio.wait_for(
                    self.reconnect_backend(backend_name),
                    timeout=self.tool_call_reconnect_timeout
                )
            except asyncio.TimeoutError:
                error_msg = f"Backend {backend_name} reconnection timed out after {self.tool_call_reconnect_timeout}s"
                logger.error(error_msg)
                asyncio.create_task(self.logger.log("ERROR", error_msg, "mcp-relay", data={"tool_name": tool_name}, trace_id=trace_id))
                raise RuntimeError(error_msg)
            ws = backend.get('ws')

        request = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}, "id": self._get_next_request_id()}
        asyncio.create_task(self.logger.log("TRACE", f"Sending request to backend: {backend_name}", "mcp-relay", data={"request": request}, trace_id=trace_id))

        try:
            try:
                await asyncio.wait_for(ws.send(json.dumps(request)), timeout=self.websocket_timeout)
                response_text = await asyncio.wait_for(ws.recv(), timeout=self.websocket_timeout)
                response = json.loads(response_text)
            except asyncio.TimeoutError:
                error_msg = f"Tool call to {backend_name} timed out after {self.websocket_timeout}s"
                logger.error(error_msg)
                asyncio.create_task(self.logger.log("ERROR", error_msg, "mcp-relay", data={"tool_name": tool_name}, trace_id=trace_id))
                raise RuntimeError(error_msg)

            asyncio.create_task(self.logger.log("TRACE", f"Received response from backend: {backend_name}", "mcp-relay", data={"response": response}, trace_id=trace_id))
            return response
        except websockets.exceptions.ConnectionClosed as e:
            asyncio.create_task(self.logger.log("WARN", f"Backend connection lost, reconnecting: {backend_name}", "mcp-relay", data={"error": str(e)}, trace_id=trace_id))
            backend['ws'] = None
            try:
                await asyncio.wait_for(
                    self.reconnect_backend(backend_name),
                    timeout=self.tool_call_reconnect_timeout
                )
            except asyncio.TimeoutError:
                error_msg = f"Backend {backend_name} reconnection timed out after {self.tool_call_reconnect_timeout}s"
                logger.error(error_msg)
                asyncio.create_task(self.logger.log("ERROR", error_msg, "mcp-relay", data={"tool_name": tool_name}, trace_id=trace_id))
                raise RuntimeError(error_msg)

            ws = backend['ws']
            logger.info(f"Retrying tool call: {tool_name}")
            try:
                await asyncio.wait_for(ws.send(json.dumps(request)), timeout=self.websocket_timeout)
                response_text = await asyncio.wait_for(ws.recv(), timeout=self.websocket_timeout)
                response = json.loads(response_text)
            except asyncio.TimeoutError:
                error_msg = f"Tool call to {backend_name} timed out after {self.websocket_timeout}s"
                logger.error(error_msg)
                asyncio.create_task(self.logger.log("ERROR", error_msg, "mcp-relay", data={"tool_name": tool_name}, trace_id=trace_id))
                raise RuntimeError(error_msg)

            asyncio.create_task(self.logger.log("TRACE", f"Retry successful for tool: {tool_name}", "mcp-relay", data={"response": response}, trace_id=trace_id))
            return response
        except Exception as e:
            asyncio.create_task(self.logger.log("ERROR", f"Tool call failed: {tool_name}", "mcp-relay", data={"error": str(e)}, trace_id=trace_id))
            raise

    async def handle_request(self, request: dict) -> Optional[dict]:
        """Handle MCP request from Claude."""
        method, request_id, params = request.get("method"), request.get("id"), request.get("params", {})
        try:
            if method == "initialize":
                if not self.initialized:
                    await self.connect_all_backends()
                    self.initialized = True
                return {"jsonrpc": "2.0", "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "mcp-relay", "version": "3.7.0"}}, "id": request_id}
            elif method == "notifications/initialized": return None
            elif method == "tools/list": return {"jsonrpc": "2.0", "result": {"tools": self.get_all_tools()}, "id": request_id}
            elif method == "tools/call":
                response = await self.call_tool(params.get("name"), params.get("arguments", {}))
                response["id"] = request_id  # Forward response, but use original request ID
                asyncio.create_task(self.logger.log("TRACE", f"Returning response for tools/call", "mcp-relay", data={"response_has_result": "result" in response, "response_has_id": "id" in response, "response_preview": str(response)[:200]}))
                return response
            else:
                return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": request_id}
        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": request_id}

    async def run(self):
        """Main stdio loop."""
        logger.info("MCP Relay starting on stdio")

        # Watch the parent directory (watchdog requires directory, not file)
        # ConfigFileHandler.on_modified() filters for our specific config file
        config_dir = str(Path(self.config_path).parent)
        event_handler = ConfigFileHandler(self, self.config_path)
        observer = Observer()
        observer.schedule(event_handler, config_dir, recursive=False)
        observer.start()
        logger.info(f"Watching config file: {self.config_path}")

        reader = asyncio.StreamReader()
        await asyncio.get_event_loop().connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
        self.stdout_writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, asyncio.get_event_loop())

        logger.info("MCP Relay ready")
        try:
            while True:
                line = await reader.readline()
                if not line: break
                try:
                    request = json.loads(line.decode('utf-8'))
                    logger.info(f"Received request: {request.get('method')}")
                    response = await self.handle_request(request)
                    if response:
                        self.stdout_writer.write(json.dumps(response).encode('utf-8') + b'\n')
                        await self.stdout_writer.drain()
                except json.JSONDecodeError as e: logger.error(f"Invalid JSON: {e}")
                except Exception as e: logger.error(f"Request handling error: {e}", exc_info=True)
        finally:
            observer.stop()
            observer.join()
            for backend in self.backends.values():
                if backend.get('ws'): await backend['ws'].close()
                if backend.get('keep_alive_task'):
                    task = backend['keep_alive_task']
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass # Expected
            logger.info("MCP Relay shutdown")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCP Relay - stdio to WebSocket multiplexer")
    default_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backends.yaml")
    parser.add_argument("--config", default=default_config, help="Path to backends configuration file")
    args = parser.parse_args()
    relay = MCPRelay(config_path=args.config)
    asyncio.run(relay.run())
