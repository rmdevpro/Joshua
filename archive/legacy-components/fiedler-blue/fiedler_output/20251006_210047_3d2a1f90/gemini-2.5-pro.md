Excellent. I wholeheartedly agree with the decision to switch to PostgreSQL.

Consolidating your database infrastructure onto the existing PostgreSQL instance is a sound architectural choice. It reduces operational complexity, simplifies backups and monitoring, and leverages a more powerful, scalable, and feature-rich database system. Using `asyncpg` is also the right call for a high-performance `asyncio` application.

Here is the complete, redesigned `catalog.py` that meets all your requirements.

---

### `catalog.py`

```python
import os
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set

import asyncpg

# --- Configuration ---
# Read database configuration from environment variables
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "horace")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not PG_USER or not PG_PASSWORD:
    raise ValueError("POSTGRES_USER and POSTGRES_PASSWORD environment variables are required")

# --- Constants ---
CURRENT_SCHEMA_VERSION = 1
log = logging.getLogger(__name__)

# --- PostgreSQL Schema Definition ---
SCHEMA_SQL = """
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE files (
    file_id UUID PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    current_checksum TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_files_path ON files(path);

CREATE TABLE file_versions (
    checksum TEXT PRIMARY KEY,
    file_id UUID NOT NULL,
    size_bytes BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(file_id) REFERENCES files(file_id) ON DELETE CASCADE
);
CREATE INDEX idx_file_versions_file_id ON file_versions(file_id);
"""

class CatalogManager:
    """
    Manages the file catalog using a PostgreSQL database.

    This class handles all database interactions for tracking files, their
    versions, and their metadata. It uses an asyncpg connection pool for

    efficient, non-blocking database operations.
    """

    def __init__(self, base_path: Path):
        """
        Initializes the CatalogManager.

        Args:
            base_path: The base path of the monitored directory. This is kept
                       for interface compatibility but is not used for the DB connection.
        """
        self.base_path = base_path
        self._pool: Optional[asyncpg.Pool] = None
        log.info(f"CatalogManager configured for PostgreSQL at {PG_HOST}:{PG_PORT}/{PG_DB}")

    async def initialize(self) -> None:
        """
        Establishes the database connection pool and ensures the schema is up-to-date.
        This must be called after object creation and before any other methods.
        """
        if self._pool:
            return
        try:
            self._pool = await asyncpg.create_pool(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                database=PG_DB,
            )
            log.info("Successfully created PostgreSQL connection pool.")
            await self._ensure_schema()
        except Exception as e:
            log.error(f"Failed to connect to PostgreSQL or initialize schema: {e}")
            raise

    async def _ensure_schema(self) -> None:
        """
        Checks if the database schema exists and creates it if it doesn't.
        """
        assert self._pool is not None, "Connection pool not initialized"
        async with self._pool.acquire() as conn:
            # Check if the schema_version table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'schema_version'
                );
                """
            )
            if not table_exists:
                log.info("Schema not found. Creating new database schema...")
                async with conn.transaction():
                    await conn.execute(SCHEMA_SQL)
                    await conn.execute(
                        "INSERT INTO schema_version (version) VALUES ($1)",
                        CURRENT_SCHEMA_VERSION
                    )
                log.info(f"Database schema created with version {CURRENT_SCHEMA_VERSION}.")
            else:
                # In a real-world scenario, you would add schema migration logic here.
                version = await conn.fetchval("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                log.info(f"Existing database schema found with version {version}.")
                if version != CURRENT_SCHEMA_VERSION:
                    log.warning(f"Schema version mismatch! DB: {version}, App: {CURRENT_SCHEMA_VERSION}")
                    # Add migration logic here if needed.

    async def close(self) -> None:
        """
        Gracefully closes the database connection pool.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            log.info("PostgreSQL connection pool closed.")

    async def handle_upsert(self, file_path: Path, checksum: str, size_bytes: int) -> None:
        """
        Handles the creation or update of a file in the catalog.

        This operation is atomic. It first upserts the file record to get a
        stable file_id, then inserts the new file version record.

        Args:
            file_path: The absolute path to the file.
            checksum: The new checksum (e.g., SHA256) of the file content.
            size_bytes: The size of the file in bytes.
        """
        assert self._pool is not None, "Connection pool not initialized"
        str_path = str(file_path)
        now = datetime.now(timezone.utc)

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Step 1: Upsert the file record.
                # This ensures we have a file_id, whether the file is new or existing.
                # ON CONFLICT (path) handles the update case.
                file_id = await conn.fetchval(
                    """
                    INSERT INTO files (file_id, path, current_checksum, is_deleted, created_at, updated_at)
                    VALUES ($1, $2, $3, false, $4, $4)
                    ON CONFLICT (path) DO UPDATE SET
                        current_checksum = EXCLUDED.current_checksum,
                        is_deleted = false,
                        updated_at = EXCLUDED.updated_at
                    RETURNING file_id;
                    """,
                    uuid.uuid4(), str_path, checksum, now
                )

                # Step 2: Insert the new version.
                # ON CONFLICT (checksum) DO NOTHING prevents duplicate version entries.
                await conn.execute(
                    """
                    INSERT INTO file_versions (checksum, file_id, size_bytes, timestamp)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (checksum) DO NOTHING;
                    """,
                    checksum, file_id, size_bytes, now
                )
        log.debug(f"Upserted file: {str_path} with checksum {checksum[:8]}")

    async def handle_delete(self, file_path: Path) -> None:
        """
        Marks a file as deleted in the catalog.

        Args:
            file_path: The absolute path of the file to mark as deleted.
        """
        assert self._pool is not None, "Connection pool not initialized"
        str_path = str(file_path)
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE files
                SET is_deleted = true, updated_at = $1
                WHERE path = $2;
                """,
                now, str_path
            )
        log.debug(f"Marked file as deleted: {str_path}")

    async def handle_move(self, old_path: Path, new_path: Path) -> None:
        """
        Updates the path of a file in the catalog to reflect a move.

        Args:
            old_path: The original absolute path of the file.
            new_path: The new absolute path of the file.
        """
        assert self._pool is not None, "Connection pool not initialized"
        str_old_path = str(old_path)
        str_new_path = str(new_path)
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE files
                SET path = $1, updated_at = $2
                WHERE path = $3;
                """,
                str_new_path, now, str_old_path
            )
        log.debug(f"Moved file from {str_old_path} to {str_new_path}")

    async def search_files(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for active files where the path matches the query.

        Args:
            query: A string to search for in file paths (case-sensitive).

        Returns:
            A list of dictionaries, each representing a matching file.
        """
        assert self._pool is not None, "Connection pool not initialized"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    f.path,
                    f.current_checksum,
                    v.size_bytes,
                    f.updated_at
                FROM files f
                JOIN file_versions v ON f.current_checksum = v.checksum
                WHERE f.path LIKE $1 AND f.is_deleted = false
                ORDER BY f.updated_at DESC;
                """,
                f"%{query}%"
            )
        return [dict(row) for row in rows]

    async def get_file_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete information for a single file by its exact path.

        Args:
            file_path: The absolute path of the file.

        Returns:
            A dictionary with the file's metadata, or None if not found.
        """
        assert self._pool is not None, "Connection pool not initialized"
        str_path = str(file_path)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT file_id, path, current_checksum, is_deleted, created_at, updated_at
                FROM files
                WHERE path = $1;
                """,
                str_path
            )
        return dict(row) if row else None

    async def reconcile(self, all_current_paths: Set[str]) -> Set[str]:
        """
        Compares the catalog with the current state of the filesystem and
        marks files that no longer exist as deleted.

        Args:
            all_current_paths: A set of all file paths currently on disk.

        Returns:
            A set of paths for files that were marked as deleted.
        """
        assert self._pool is not None, "Connection pool not initialized"
        async with self._pool.acquire() as conn:
            db_path_records = await conn.fetch(
                "SELECT path FROM files WHERE is_deleted = false;"
            )
            db_paths = {record['path'] for record in db_path_records}

            missing_paths = db_paths - all_current_paths
            if not missing_paths:
                log.info("Reconciliation complete. No missing files found.")
                return set()

            log.warning(f"Reconciliation found {len(missing_paths)} missing files. Marking as deleted.")
            now = datetime.now(timezone.utc)
            # Use ANY($2::text[]) for an efficient bulk update
            await conn.execute(
                """
                UPDATE files
                SET is_deleted = true, updated_at = $1
                WHERE path = ANY($2::text[]);
                """,
                now, list(missing_paths)
            )
            return missing_paths
```

### Summary of Changes & Next Steps

1.  **`catalog.py`:** The code above is a complete replacement for your previous SQLite-based version. It uses `asyncpg`'s connection pooling, handles PostgreSQL-specific syntax (`$1`, `ON CONFLICT`, `TIMESTAMPTZ`, `UUID`), and reads its configuration from environment variables as required. The public interface of `CatalogManager` remains unchanged.

2.  **`requirements.txt`:** You will need to replace `aiosqlite` with `asyncpg`.
    ```diff
    -aiosqlite
    +asyncpg
    ```

3.  **`docker-compose.yml` (or similar deployment configuration):** You need to provide the PostgreSQL environment variables to the Horace service container.

    ```yaml
    services:
      horace-nas-gateway:
        build: .
        environment:
          - POSTGRES_HOST=db # Or your actual DB host
          - POSTGRES_PORT=5432
          - POSTGRES_DB=horace
          - POSTGRES_USER=horace_user
          - POSTGRES_PASSWORD=your_secure_password
        # ... other service config
      
      db: # If you're running Postgres in Docker Compose
        image: postgres:16
        environment:
          - POSTGRES_DB=horace
          - POSTGRES_USER=horace_user
          - POSTGRES_PASSWORD=your_secure_password
        # ... other db config
    ```

4.  **`main.py`:** The initialization sequence will need a small change to call the new `async` initializer.

    **Previous:**
    ```python
    # catalog = CatalogManager(db_path=...)
    # await catalog.initialize() # Assuming you had a synchronous one before
    ```

    **New:**
    ```python
    import asyncio
    
    # ...
    
    async def main():
        # ...
        catalog = CatalogManager(base_path=Path("/path/to/nas"))
        await catalog.initialize()
        
        # ... start watcher, server, etc.
        
        try:
            # ... keep running
        finally:
            await catalog.close()
    
    if __name__ == "__main__":
        asyncio.run(main())
    ```

This new implementation is robust, efficient, and aligns perfectly with your existing infrastructure.
