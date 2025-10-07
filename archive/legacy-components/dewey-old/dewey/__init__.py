# dewey/__init__.py
"""Dewey MCP Server - Conversation storage and retrieval"""

from dewey import config
from dewey.database import db_pool

__version__ = "1.0.0"
__all__ = ['config', 'db_pool']
