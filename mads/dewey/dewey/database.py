# dewey/database.py
"""
Async PostgreSQL connection pooling and query execution for Dewey.
"""
import logging
from contextlib import asynccontextmanager

import asyncpg

from dewey import config

logger = logging.getLogger(__name__)

class Database:
    """Manages the async PostgreSQL connection pool."""
    _pool = None

    async def initialize(self):
        """Initializes the async connection pool."""
        if self._pool is None:
            logger.info(f"Initializing async database connection pool for '{config.DB_NAME}' on {config.DB_HOST}:{config.DB_PORT}")
            try:
                self._pool = await asyncpg.create_pool(
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    database=config.DB_NAME,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    min_size=config.DB_POOL_MIN_CONN,
                    max_size=config.DB_POOL_MAX_CONN,
                    ssl='prefer',
                )
                logger.info("Async database connection pool initialized successfully.")
            except Exception as e:
                logger.critical(f"Failed to connect to PostgreSQL: {e}")
                raise

    async def close(self):
        """Closes all connections in the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed.")

    @asynccontextmanager
    async def acquire(self):
        """Provides a connection from the pool as an async context manager."""
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        """Provides a transactional database connection."""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn

# Create a single instance to be used throughout the application
db_pool = Database()
