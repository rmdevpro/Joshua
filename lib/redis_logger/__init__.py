"""
Joshua Redis Logger Package.

Exposes the primary `RedisLogger` class for easy import.
"""
from .redis_logger import RedisLogger
from .version import __version__

__all__ = ["RedisLogger", "__version__"]
