#!/usr/bin/env python3
"""Fiedler MCP Server - Exposes Fiedler as MCP tools for Claude Code."""

import json
import sys
from typing import Any, Dict, List

from joshua_logger import Logger
logger = Logger()

# Import Fiedler's functions
try:
    from fiedler.tools.send import fiedler_send
    from fiedler.tools.models import fiedler_list_models
    from fiedler.tools.config import fiedler_get_config
    import asyncio
    asyncio.run(logger.log("INFO", "Successfully imported Fiedler tools", "fiedler-mcp"))
except ImportError as e:
    import asyncio
    asyncio.run(logger.log("ERROR", f"Failed to import Fiedler tools: {e}", "fiedler-mcp"))
    sys.exit(1)


class FiedlerMCPServer:
    """MCP server implementation for Fiedler."""

    def __init__(self):
        import asyncio
        self.tools = {
            "fiedler_send": {
                "description": "Send prompts to multiple LLM models (Gemini, GPT-5, Llama, DeepSeek, Qwen, Grok) and get parallel responses. Use this for comparing model outputs, getting diverse perspectives, or when user mentions specific models.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt/query to send to the models"
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of file paths to include as context"
                        },
                        "models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Model names to query. Options: gemini-2.5-pro, gpt-5, llama-3.1-70b, llama-3.3-70b, deepseek-r1, qwen-2.5-72b, grok-4. Leave empty for defaults (gemini-2.5-pro, gpt-5, grok-4)."
                        }
                    },
                    "required": ["prompt"]
                }
            },
            "fiedler_list_models": {
                "description": "List all available LLM models and their configurations (aliases, capabilities, token limits)",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "fiedler_get_config": {
                "description": "Get Fiedler configuration and status (output directory, security settings, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
        asyncio.run(logger.log("INFO", f"Initialized Fiedler MCP Server with {len(self.tools)} tools", "fiedler-mcp"))

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        import asyncio
        method = request.get("method")
        asyncio.run(logger.log("INFO", f"Handling request: {method}", "fiedler-mcp"))

        if method == "initialize":
            asyncio.run(logger.log("INFO", "Initializing MCP server", "fiedler-mcp"))
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "fiedler-mcp-server",
                    "version": "1.0.0"
                }
            }

        elif method == "tools/list":
            asyncio.run(logger.log("INFO", f"Listing {len(self.tools)} available tools", "fiedler-mcp"))
            return {
                "tools": [
                    {"name": name, **spec}
                    for name, spec in self.tools.items()
                ]
            }

        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"].get("arguments", {})
            asyncio.run(logger.log("INFO", f"Calling tool: {tool_name} with arguments: {list(arguments.keys())}", "fiedler-mcp"))

            try:
                result = self._call_tool(tool_name, arguments)
                asyncio.run(logger.log("INFO", f"Tool {tool_name} completed successfully", "fiedler-mcp"))
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            except Exception as e:
                asyncio.run(logger.log("ERROR", f"Tool {tool_name} failed: {str(e)}", "fiedler-mcp"))
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {str(e)}"
                        }
                    ],
                    "isError": True
                }

        else:
            asyncio.run(logger.log("WARN", f"Unknown method: {method}", "fiedler-mcp"))
            return {"error": f"Unknown method: {method}"}

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute the requested tool."""
        import asyncio

        if tool_name == "fiedler_send":
            # fiedler_send is async - need to run it in event loop
            return asyncio.run(fiedler_send(
                prompt=arguments["prompt"],
                files=arguments.get("files"),
                models=arguments.get("models")
            ))

        elif tool_name == "fiedler_list_models":
            return fiedler_list_models()

        elif tool_name == "fiedler_get_config":
            return fiedler_get_config()

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def run(self):
        """Main server loop - reads from stdin, writes to stdout."""
        import asyncio
        asyncio.run(logger.log("INFO", "Fiedler MCP Server starting - listening on stdin", "fiedler-mcp"))

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    # Write response to stdout (MCP protocol)
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    asyncio.run(logger.log("ERROR", f"Invalid JSON received: {e}", "fiedler-mcp"))
                    error_response = {
                        "error": f"Invalid JSON: {str(e)}"
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

                except Exception as e:
                    asyncio.run(logger.log("ERROR", f"Error processing request: {e}", "fiedler-mcp"))
                    error_response = {
                        "error": str(e)
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            asyncio.run(logger.log("INFO", "Fiedler MCP Server shutting down", "fiedler-mcp"))
        except Exception as e:
            asyncio.run(logger.log("ERROR", f"Fatal error: {e}", "fiedler-mcp"))
            sys.exit(1)


if __name__ == "__main__":
    server = FiedlerMCPServer()
    server.run()
