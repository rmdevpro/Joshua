"""
joshua_network: Standardized networking library for the Joshua project.

This library provides battle-tested Server and Client implementations for
WebSocket-based JSON-RPC 2.0 communication, ensuring consistency and
reliability across all components.
"""
from .errors import ToolError
from .server import Server
from .client import Client

__version__ = "1.0.0"

__all__ = ["Server", "Client", "ToolError"]
