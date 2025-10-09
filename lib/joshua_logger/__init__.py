"""
joshua_logger: Asynchronous, fault-tolerant logging client for Godot.

This library provides a simple, standardized way to send structured logs
to the Godot service. It is designed to be fire-and-forget and never
interfere with the application's execution.

A default logger instance is pre-configured and can be used directly.

Usage:
    from joshua_logger import logger
    await logger.log(level="INFO", message="Hello World", component="my_app")
"""
from .logger import Logger

__version__ = "1.0.0"

# Default logger instance for easy, zero-configuration use.
# The `logger` object can be imported and used directly from the package.
logger = Logger()

__all__ = ["Logger", "logger"]
