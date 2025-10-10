"""
joshua_logger: Asynchronous, fault-tolerant logging client for Godot.

This library provides a simple, standardized way to send structured logs
to the Godot service. It is designed to be fire-and-forget and never
interfere with the application's execution.

Usage:
    from joshua_logger import Logger
    logger = Logger()
    await logger.log(level="INFO", message="Hello World", component="my_app")
"""
from .logger import Logger

__version__ = "1.0.0"

# The global singleton instance has been removed.
# Users should now instantiate the Logger class themselves.

__all__ = ["Logger"]
