Of course. Here is the corrected `catalog.py` that implements the PostgreSQL backend while strictly adhering to the required public interface for compatibility with `watcher.py` and `mcp_server.py`.

This version incorporates all the feedback, including:
- **Exact Method Signatures**: All public methods match the original SQLite interface.
- **Internal Logic**: Checksum calculation and filesystem scanning are now internal to `handle_upsert` and `reconcile`, respectively.
- **Connection Pooling**: Uses `async with self._pool.acquire() as conn:` for all database operations.
- **Batch Operations**: `reconcile` uses a highly efficient batch update for marking files as deleted.
- **Helper Method**: A non-blocking `_compute_checksum` method is included as requested.
- **Robustness**: Includes solid error handling, logging, and transaction management.

---

### `catalog.py` (Corrected PostgreSQL Implementation)

```python
import asyncio
import hashlib
import logging
import os
from datetime importdatetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper function for non-blocking I/O ---

def _blocking_hash_file(file_path: Path) -> str:
    """
    A blocking function to compute SHA-256 hash.
    Designed to be run in a thread pool executor to avoid blocking asyncio event loop.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (FileNotFoundError, IsADirectoryError):
        # File might be deleted or changed between discovery and hashing
        return ""

def _blocking_scan_disk(root: Path) -> Set[str]:
    """
    A blocking function to walk the filesystem and collect relative file paths.
    Designed to be run in a thread pool executor.
    """
    paths = set()
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            full_path = Path(dirpath) / filename
            try:
                # Ensure it's a file and not a symlink to a directory
                if full_path.is_file():
                    relative_path = full_path.relative_to(root)
                    paths.add(str(relative_path))
            except (FileNotFoundError, OSError):
                # File might be deleted during the scan
                continue
    return paths


class CatalogManager:
    """
    Manages a file catalog backed by a PostgreSQL database.
    This class maintains interface compatibility with the original SQLite version.
    """
    _CURRENT_SCHEMA_VERSION = 1

    def __init__(self, db_path: Path, base_path: Path):
        """
        Initializes the CatalogManager for PostgreSQL.
        The db_path parameter is ignored but kept for interface compatibility.
        Connection details are retrieved from the DATABASE_URL environment variable.
        """
        self.base_path = base_path
        self._pool: Optional[asyncpg.Pool] = None
        self.dsn = os.environ.get(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/mcp_catalog"
        )
        logger.info(f"CatalogManager initialized for base path: {self.base_path}")
        logger.debug(f"db_path parameter '{db_path}' received but ignored for PostgreSQL.")

    async def connect(self):
        """
        Establishes the connection pool to PostgreSQL and ensures schema is up to date.
        This method replaces the original 'initialize' to match the required interface.
        """
        if self._pool:
            logger.warning("Connection pool already exists. Ignoring connect call.")
            return
        try:
            self._pool = await asyncpg.create_pool(dsn=self.dsn)
            logger.info("Successfully connected to PostgreSQL and created connection pool.")
            await self._initialize_schema()
        except Exception as e:
            logger.critical(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise

    async def close(self):
        """Closes the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed.")

    async def _initialize_schema(self):
        """Creates and migrates the database schema if necessary."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Schema versioning table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)

                # Check current version
                version_record = await conn.fetchrow("SELECT MAX(version) as version FROM schema_version")
                current_version = version_record['version'] or 0

                if current_version < 1:
                    logger.info("Schema version is less than 1, applying initial schema...")
                    # Main files table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS files (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            path TEXT NOT NULL UNIQUE,
                            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                    """)
                    # File versions table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS file_versions (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                            checksum TEXT NOT NULL,
                            size_bytes BIGINT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                    """)
                    # Indexes
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files (path) WHERE is_deleted = false")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_file_versions_file_id ON file_versions (file_id)")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_file_versions_checksum ON file_versions (checksum)")

                    # Update schema version
                    await conn.execute("INSERT INTO schema_version (version) VALUES ($1)", self._CURRENT_SCHEMA_VERSION)
                    logger.info(f"Schema version {self._CURRENT_SCHEMA_VERSION} applied successfully.")

    async def _compute_checksum(self, file_path: Path) -> str:
        """
        Asynchronously computes the SHA-256 checksum of a file without blocking the event loop.
        """
        if not file_path.exists() or not file_path.is_file():
            return ""
        loop = asyncio.get_running_loop()
        try:
            checksum = await loop.run_in_executor(
                None,  # Use the default thread pool executor
                _blocking_hash_file,
                file_path
            )
            return checksum
        except Exception as e:
            logger.error(f"Error computing checksum for {file_path}: {e}")
            return ""

    async def handle_upsert(self, full_path: Path):
        """
        Handles the insertion or update of a file record.
        Computes checksum and size internally to match the required interface.
        """
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        try:
            if not full_path.is_file():
                logger.warning(f"Upsert requested for non-existent or non-file path: {full_path}")
                return

            relative_path_str = str(full_path.relative_to(self.base_path))
            size_bytes = full_path.stat().st_size
            checksum = await self._compute_checksum(full_path)

            if not checksum:
                logger.error(f"Skipping upsert for {full_path} due to checksum computation failure.")
                return

            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    # This query performs an "upsert" on the files table.
                    # If the path exists, it updates updated_at and un-deletes it.
                    # If it doesn't exist, it inserts a new record.
                    # It returns the file's UUID in either case.
                    file_id = await conn.fetchval("""
                        WITH ins AS (
                            INSERT INTO files (path, updated_at)
                            VALUES ($1, $2)
                            ON CONFLICT (path) DO UPDATE
                            SET is_deleted = FALSE, updated_at = $2
                            RETURNING id
                        )
                        SELECT id FROM ins;
                    """, relative_path_str, datetime.now(timezone.utc))

                    # Check if this exact version (checksum) already exists to avoid duplicates
                    latest_version = await conn.fetchrow("""
                        SELECT checksum FROM file_versions
                        WHERE file_id = $1
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, file_id)

                    if not latest_version or latest_version['checksum'] != checksum:
                        await conn.execute("""
                            INSERT INTO file_versions (file_id, checksum, size_bytes)
                            VALUES ($1, $2, $3)
                        """, file_id, checksum, size_bytes)
                        logger.info(f"Upserted new version for: {relative_path_str}")
                    else:
                        logger.debug(f"File version is unchanged, skipping version insert for: {relative_path_str}")

        except Exception as e:
            logger.error(f"Failed to handle upsert for {full_path}: {e}", exc_info=True)

    async def handle_delete(self, full_path: Path):
        """Marks a file as deleted in the catalog."""
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        relative_path_str = str(full_path.relative_to(self.base_path))
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE files
                    SET is_deleted = TRUE, updated_at = $1
                    WHERE path = $2
                """, datetime.now(timezone.utc), relative_path_str)
                if result == "UPDATE 1":
                    logger.info(f"Marked as deleted: {relative_path_str}")
                else:
                    logger.warning(f"Attempted to delete non-existent record: {relative_path_str}")
        except Exception as e:
            logger.error(f"Failed to handle delete for {relative_path_str}: {e}", exc_info=True)

    async def handle_move(self, src_path: Path, dest_path: Path):
        """Updates the path of a file in the catalog."""
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        src_rel_path = str(src_path.relative_to(self.base_path))
        dest_rel_path = str(dest_path.relative_to(self.base_path))
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE files
                    SET path = $1, updated_at = $2
                    WHERE path = $3
                """, dest_rel_path, datetime.now(timezone.utc), src_rel_path)
                if result == "UPDATE 1":
                    logger.info(f"Moved path from {src_rel_path} to {dest_rel_path}")
                else:
                    logger.warning(f"Attempted to move non-existent record: {src_rel_path}")
        except asyncpg.UniqueViolationError:
            logger.error(f"Move failed: destination path {dest_rel_path} already exists.")
        except Exception as e:
            logger.error(f"Failed to handle move for {src_rel_path}: {e}", exc_info=True)

    async def reconcile(self):
        """
        Reconciles the filesystem state with the catalog.
        Scans the filesystem internally to discover all current files.
        """
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        logger.info("Starting reconciliation process...")
        loop = asyncio.get_running_loop()
        
        # 1. Get all file paths from the filesystem (non-blocking)
        disk_paths_set = await loop.run_in_executor(None, _blocking_scan_disk, self.base_path)
        logger.info(f"Found {len(disk_paths_set)} files on disk.")

        # 2. Get all non-deleted paths from the database
        async with self._pool.acquire() as conn:
            db_records = await conn.fetch("SELECT path FROM files WHERE is_deleted = false")
            db_paths_set = {record['path'] for record in db_records}
        logger.info(f"Found {len(db_paths_set)} active files in database.")

        # 3. Compare and find differences
        new_paths = disk_paths_set - db_paths_set
        missing_paths = db_paths_set - disk_paths_set

        # 4. Process differences
        logger.info(f"Reconciliation: {len(new_paths)} new files to add, {len(missing_paths)} missing files to mark as deleted.")

        # Upsert new files concurrently
        if new_paths:
            upsert_tasks = [self.handle_upsert(self.base_path / p) for p in new_paths]
            await asyncio.gather(*upsert_tasks)
            logger.info(f"Finished processing {len(new_paths)} new files.")

        # Batch-update missing files as deleted
        if missing_paths:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    UPDATE files
                    SET is_deleted = true, updated_at = $1
                    WHERE path = ANY($2::text[])
                """, datetime.now(timezone.utc), list(missing_paths))
            logger.info(f"Marked {len(missing_paths)} missing files as deleted.")
        
        logger.info("Reconciliation process completed.")

    async def search_files(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Searches for files by path."""
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        try:
            async with self._pool.acquire() as conn:
                # Use a LATERAL JOIN to get the latest version for each file efficiently
                rows = await conn.fetch("""
                    SELECT
                        f.path,
                        f.updated_at,
                        fv.checksum,
                        fv.size_bytes,
                        fv.created_at AS version_created_at
                    FROM files f
                    JOIN LATERAL (
                        SELECT checksum, size_bytes, created_at
                        FROM file_versions
                        WHERE file_id = f.id
                        ORDER BY created_at DESC
                        LIMIT 1
                    ) fv ON TRUE
                    WHERE f.path ILIKE $1 AND f.is_deleted = FALSE
                    ORDER BY f.updated_at DESC
                    LIMIT $2
                """, f'%{query}%', limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search files with query '{query}': {e}", exc_info=True)
            return []

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a single file, including its latest version.
        Parameter is 'str' type for interface compatibility.
        """
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT
                        f.path,
                        f.is_deleted,
                        f.created_at,
                        f.updated_at,
                        fv.checksum,
                        fv.size_bytes,
                        fv.created_at AS version_created_at
                    FROM files f
                    JOIN LATERAL (
                        SELECT checksum, size_bytes, created_at
                        FROM file_versions
                        WHERE file_id = f.id
                        ORDER BY created_at DESC
                        LIMIT 1
                    ) fv ON TRUE
                    WHERE f.path = $1
                """, file_path)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get file info for '{file_path}': {e}", exc_info=True)
            return None
```
