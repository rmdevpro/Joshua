Excellent. The requirements have been unanimously approved. Let's proceed with the implementation of the Horace NAS Gateway.

Here is the complete, production-ready code, organized by file as specified in the implementation scope.

---

### `requirements.txt`

First, let's define the project dependencies.

```text
# requirements.txt

# For the web server (MCP)
fastapi
uvicorn[standard]

# For the filesystem watcher
watchdog

# For scheduled tasks (ZFS snapshots)
apscheduler

# For improved database performance and logging
aiosqlite
```

---

### `horace/catalog.py`

This module handles all interactions with the SQLite database, including schema management, versioning, and file operations.

```python
# horace/catalog.py

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

logger = logging.getLogger(__name__)

DB_SCHEMA_VERSION = 1
CHECKSUM_ALGO = "sha256"


class CatalogManager:
    """
    Manages the SQLite catalog for file metadata and version history.

    This class handles database initialization, schema versioning, and all
    CRUD operations related to files and their content-addressed versions.
    It is designed to be used asynchronously.
    """

    def __init__(self, db_path: Path, base_path: Path):
        """
        Initializes the CatalogManager.

        Args:
            db_path: The path to the SQLite database file.
            base_path: The root directory being monitored (e.g., /mnt/irina_storage/files).
                       Used to make stored paths relative.
        """
        self.db_path = db_path
        self.base_path = base_path
        self._db: Optional[aiosqlite.Connection] = None
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def connect(self):
        """Connects to the database and initializes the schema."""
        if self._db and not self._db.is_closed():
            return

        logger.info(f"Connecting to catalog database at {self.db_path}")
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._db.execute("PRAGMA foreign_keys=ON;")
        await self._initialize_schema()

    async def close(self):
        """Closes the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Catalog database connection closed.")

    async def _initialize_schema(self):
        """
        Creates database tables if they don't exist and handles schema migrations.
        """
        async with self._db.cursor() as cursor:
            # Check for schema version table
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if await cursor.fetchone() is None:
                logger.info("Schema version table not found. Creating initial schema.")
                await self._create_v1_schema(cursor)
                await cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (DB_SCHEMA_VERSION,))
            else:
                await cursor.execute("SELECT MAX(version) as v FROM schema_version")
                current_version = (await cursor.fetchone())["v"]
                if current_version < DB_SCHEMA_VERSION:
                    # In a real-world scenario, you would add migration logic here.
                    # For now, we'll just log a warning.
                    logger.warning(f"Database schema version {current_version} is older than "
                                   f"supported version {DB_SCHEMA_VERSION}. Migrations needed.")
        await self._db.commit()

    async def _create_v1_schema(self, cursor: aiosqlite.Cursor):
        """Creates the version 1 schema for the catalog."""
        logger.info("Creating database schema v1...")
        await cursor.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await cursor.execute("""
            CREATE TABLE files (
                file_id TEXT PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                current_checksum TEXT, -- Can be NULL if file is known but content is not
                is_deleted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
        """)
        await cursor.execute("CREATE INDEX idx_files_path ON files(path);")
        await cursor.execute("""
            CREATE TABLE file_versions (
                checksum TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(file_id) REFERENCES files(file_id) ON DELETE CASCADE
            );
        """)
        await cursor.execute("CREATE INDEX idx_file_versions_file_id ON file_versions(file_id);")

    async def _compute_checksum(self, full_path: Path) -> Optional[str]:
        """
        Computes the SHA-256 checksum of a file.

        Reads the file in chunks to handle large files efficiently.

        Returns:
            The hex digest of the checksum, prefixed with the algorithm,
            or None if the file cannot be read.
        """
        if not full_path.is_file():
            return None
        hasher = hashlib.new(CHECKSUM_ALGO)
        try:
            with open(full_path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return f"{CHECKSUM_ALGO}:{hasher.hexdigest()}"
        except (IOError, PermissionError) as e:
            logger.error(f"Could not compute checksum for {full_path}: {e}")
            return None

    def _get_relative_path(self, full_path: Path) -> str:
        """Converts an absolute path to a path relative to the base watch directory."""
        return str(full_path.relative_to(self.base_path))

    async def handle_upsert(self, full_path: Path):
        """
        Handles a file creation or modification event.

        This is the core logic for versioning. It computes the file's checksum
        and creates new entries in the `files` and `file_versions` tables
        if the content is new for that path.
        """
        if not full_path.is_file():
            logger.debug(f"Skipping upsert for non-file path: {full_path}")
            return

        rel_path_str = self._get_relative_path(full_path)
        checksum = await self._compute_checksum(full_path)
        if not checksum:
            return

        size_bytes = full_path.stat().st_size
        now = datetime.utcnow()

        async with self._db.execute("SELECT file_id, current_checksum FROM files WHERE path = ?", (rel_path_str,)) as cursor:
            file_row = await cursor.fetchone()

        if not file_row:
            # New file
            file_id = str(uuid.uuid4())
            logger.info(f"New file detected: '{rel_path_str}' [checksum: {checksum}]")
            await self._db.execute(
                "INSERT INTO files (file_id, path, current_checksum, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (file_id, rel_path_str, checksum, now, now)
            )
            await self._db.execute(
                "INSERT OR IGNORE INTO file_versions (checksum, file_id, size_bytes, timestamp) VALUES (?, ?, ?, ?)",
                (checksum, file_id, size_bytes, now)
            )
        else:
            # Existing file, check for new version
            file_id = file_row["file_id"]
            if file_row["current_checksum"] != checksum:
                logger.info(f"New version detected for '{rel_path_str}' [checksum: {checksum}]")
                await self._db.execute(
                    "UPDATE files SET current_checksum = ?, updated_at = ?, is_deleted = 0 WHERE file_id = ?",
                    (checksum, now, file_id)
                )
                await self._db.execute(
                    "INSERT OR IGNORE INTO file_versions (checksum, file_id, size_bytes, timestamp) VALUES (?, ?, ?, ?)",
                    (checksum, file_id, size_bytes, now)
                )
            else:
                # File content is the same, but maybe it was restored. Ensure it's not marked deleted.
                await self._db.execute("UPDATE files SET is_deleted = 0, updated_at = ? WHERE file_id = ?", (now, file_id))

        await self._db.commit()

    async def handle_delete(self, full_path: Path):
        """Handles a file deletion event by marking the file as deleted."""
        rel_path_str = self._get_relative_path(full_path)
        logger.info(f"File deleted: '{rel_path_str}'")
        await self._db.execute(
            "UPDATE files SET is_deleted = 1, updated_at = ? WHERE path = ?",
            (datetime.utcnow(), rel_path_str)
        )
        await self._db.commit()

    async def handle_move(self, src_path: Path, dest_path: Path):
        """Handles a file move/rename event."""
        src_rel_path = self._get_relative_path(src_path)
        dest_rel_path = self._get_relative_path(dest_path)
        logger.info(f"File moved: '{src_rel_path}' -> '{dest_rel_path}'")
        
        # In a rename, the source path might not exist in the DB if it was a temporary file.
        # The destination path is what matters. We treat it as an upsert.
        # If the source path *was* tracked, we update its path.
        async with self._db.execute("SELECT file_id FROM files WHERE path = ?", (src_rel_path,)) as cursor:
            file_row = await cursor.fetchone()

        if file_row:
            await self._db.execute(
                "UPDATE files SET path = ?, updated_at = ? WHERE file_id = ?",
                (dest_rel_path, datetime.utcnow(), file_row["file_id"])
            )
            await self._db.commit()
        else:
            # This happens with the "write to temp and rename" pattern.
            # The temp file was never cataloged, so we just catalog the final destination file.
            await self.handle_upsert(dest_path)

    async def reconcile(self):
        """
        Performs a full scan of the filesystem to synchronize the catalog.

        This is crucial for recovering state after downtime.
        """
        logger.info("Starting filesystem reconciliation...")
        
        # Step 1: Scan filesystem and upsert all found files
        filesystem_paths = set()
        tasks = []
        for current_path in self.base_path.rglob('*'):
            if current_path.is_file() and '.horace' not in str(current_path):
                rel_path = self._get_relative_path(current_path)
                filesystem_paths.add(rel_path)
                tasks.append(self.handle_upsert(current_path))
        
        # Process in batches to avoid overwhelming the system
        batch_size = 100
        for i in range(0, len(tasks), batch_size):
            await asyncio.gather(*tasks[i:i+batch_size])
            logger.info(f"Reconciliation progress: {i+len(tasks[i:i+batch_size])}/{len(tasks)} files processed.")

        # Step 2: Find files in DB that are no longer on disk
        async with self._db.execute("SELECT path FROM files WHERE is_deleted = 0") as cursor:
            db_paths = {row['path'] for row in await cursor.fetchall()}

        missing_paths = db_paths - filesystem_paths
        if missing_paths:
            logger.info(f"Found {len(missing_paths)} files in catalog that are missing from filesystem. Marking as deleted.")
            now = datetime.utcnow()
            for path in missing_paths:
                 await self._db.execute(
                    "UPDATE files SET is_deleted = 1, updated_at = ? WHERE path = ?",
                    (now, path)
                )
            await self._db.commit()

        logger.info("Filesystem reconciliation complete.")

    async def search_files(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Searches for files by path."""
        async with self._db.execute(
            "SELECT path, current_checksum, updated_at FROM files WHERE path LIKE ? AND is_deleted = 0 LIMIT ?",
            (f"%{query}%", limit)
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information and version history for a single file.
        """
        async with self._db.execute(
            "SELECT file_id, path, current_checksum, created_at, updated_at FROM files WHERE path = ? AND is_deleted = 0",
            (file_path,)
        ) as cursor:
            file_info = await cursor.fetchone()

        if not file_info:
            return None

        result = dict(file_info)
        async with self._db.execute(
            "SELECT checksum, size_bytes, timestamp FROM file_versions WHERE file_id = ? ORDER BY timestamp DESC",
            (result["file_id"],)
        ) as cursor:
            versions = await cursor.fetchall()
        
        result["versions"] = [dict(v) for v in versions]
        return result

```

---

### `horace/watcher.py`

This module uses `watchdog` to monitor filesystem events and queues them for asynchronous processing by the `CatalogManager`.

```python
# horace/watcher.py

import asyncio
import logging
from pathlib import Path
from typing import NamedTuple

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from horace.catalog import CatalogManager

logger = logging.getLogger(__name__)

class Event(NamedTuple):
    """Represents a filesystem event to be processed."""
    event_type: str
    src_path: Path
    dest_path: Optional[Path] = None


class CatalogEventHandler(FileSystemEventHandler):
    """
    Handles filesystem events from watchdog and puts them onto an async queue.
    """
    def __init__(self, queue: asyncio.Queue, base_path: Path):
        self.queue = queue
        self.base_path = base_path

    def _should_ignore(self, path_str: str) -> bool:
        """Determines if an event for a given path should be ignored."""
        # Ignore events within Horace's own metadata directory
        if '.horace' in path_str:
            return True
        # Ignore temporary files from common applications
        if path_str.endswith('~') or path_str.endswith('.tmp'):
            return True
        return False

    def on_moved(self, event: FileSystemEvent):
        if event.is_directory or self._should_ignore(event.dest_path):
            return
        logger.debug(f"Event queued: MOVED {event.src_path} -> {event.dest_path}")
        self.queue.put_nowait(Event('moved', Path(event.src_path), Path(event.dest_path)))

    def on_created(self, event: FileSystemEvent):
        # We prefer MOVED_TO/CLOSE_WRITE, but this can be a fallback.
        if event.is_directory or self._should_ignore(event.src_path):
            return
        logger.debug(f"Event queued: CREATED {event.src_path}")
        self.queue.put_nowait(Event('created', Path(event.src_path)))

    def on_modified(self, event: FileSystemEvent):
        # This event is the closest watchdog gives us to CLOSE_WRITE.
        # It's the primary trigger for updates.
        if event.is_directory or self._should_ignore(event.src_path):
            return
        logger.debug(f"Event queued: MODIFIED {event.src_path}")
        self.queue.put_nowait(Event('modified', Path(event.src_path)))

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory or self._should_ignore(event.src_path):
            return
        logger.debug(f"Event queued: DELETED {event.src_path}")
        self.queue.put_nowait(Event('deleted', Path(event.src_path)))


class WatcherService:
    """
    The main service that watches the filesystem and processes events.
    """
    def __init__(self, catalog_manager: CatalogManager, watch_path: Path):
        self.catalog = catalog_manager
        self.watch_path = watch_path
        self.queue = asyncio.Queue()

    async def run(self):
        """Starts the watcher and the event processing loop."""
        # Start watchdog observer in a separate thread
        event_handler = CatalogEventHandler(self.queue, self.watch_path)
        observer = Observer()
        observer.schedule(event_handler, str(self.watch_path), recursive=True)
        observer.start()
        logger.info(f"File watcher started on '{self.watch_path}'")

        try:
            await self._process_events()
        except asyncio.CancelledError:
            logger.info("Watcher service shutting down.")
        finally:
            observer.stop()
            observer.join()

    async def _process_events(self):
        """The main async loop that consumes events from the queue."""
        while True:
            try:
                event: Event = await self.queue.get()
                logger.info(f"Processing event: {event.event_type} on {event.src_path}")

                if event.event_type in ('created', 'modified'):
                    await self.catalog.handle_upsert(event.src_path)
                elif event.event_type == 'deleted':
                    await self.catalog.handle_delete(event.src_path)
                elif event.event_type == 'moved' and event.dest_path:
                    await self.catalog.handle_move(event.src_path, event.dest_path)
                
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event {event}: {e}", exc_info=True)
```

---

### `horace/zfs_ops.py`

This module provides a simple, synchronous wrapper around ZFS command-line tools. Asynchronous execution is handled by running these in a thread pool.

```python
# horace/zfs_ops.py

import logging
import subprocess
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

def _run_command(command: List[str]) -> Optional[str]:
    """
    Executes a shell command and returns its stdout.
    Logs errors and returns None on failure.
    """
    try:
        logger.debug(f"Executing ZFS command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error(f"ZFS command not found: '{command[0]}'. Is ZFS installed and in the system's PATH?")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing ZFS command: {' '.join(command)}")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stderr: {e.stderr.strip()}")
        return None

def create_snapshot(dataset: str, prefix: str) -> Optional[str]:
    """
    Creates a ZFS snapshot with a timestamp.

    Args:
        dataset: The name of the ZFS dataset (e.g., 'tank/horace/files').
        prefix: A prefix for the snapshot name (e.g., 'hourly', 'daily').

    Returns:
        The full name of the created snapshot, or None on failure.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snapshot_name = f"{dataset}@{prefix}-{timestamp}"
    command = ["zfs", "snapshot", snapshot_name]
    
    if _run_command(command) is not None:
        logger.info(f"Successfully created ZFS snapshot: {snapshot_name}")
        return snapshot_name
    return None

def list_snapshots(dataset: str) -> List[str]:
    """
    Lists all snapshots for a given dataset.

    Args:
        dataset: The name of the ZFS dataset.

    Returns:
        A list of snapshot names.
    """
    command = ["zfs", "list", "-t", "snapshot", "-o", "name", "-s", "creation", "-r", dataset]
    output = _run_command(command)
    if output:
        # First line is the header 'NAME', so we skip it.
        return output.splitlines()[1:]
    return []

def destroy_snapshot(snapshot_name: str) -> bool:
    """
    Destroys a ZFS snapshot.

    Args:
        snapshot_name: The full name of the snapshot to destroy.

    Returns:
        True on success, False on failure.
    """
    command = ["zfs", "destroy", snapshot_name]
    if _run_command(command) is not None:
        logger.info(f"Successfully destroyed ZFS snapshot: {snapshot_name}")
        return True
    return False

def prune_snapshots(dataset: str, retention_rules: dict):
    """
    Prunes old snapshots based on a retention policy.
    
    Example retention_rules:
    {
        "hourly": 24, # keep 24 hourly snapshots
        "daily": 14,
    }
    """
    logger.info(f"Pruning snapshots for dataset '{dataset}'...")
    all_snapshots = list_snapshots(dataset)
    
    for prefix, keep_count in retention_rules.items():
        # Filter snapshots matching the current prefix, sorted oldest to newest
        prefix_snapshots = sorted([s for s in all_snapshots if f"@{prefix}-" in s])
        
        to_delete_count = len(prefix_snapshots) - keep_count
        if to_delete_count > 0:
            logger.info(f"Found {len(prefix_snapshots)} '{prefix}' snapshots. "
                        f"Keeping {keep_count}, deleting {to_delete_count}.")
            for snapshot in prefix_snapshots[:to_delete_count]:
                destroy_snapshot(snapshot)

```

---

### `horace/mcp_server.py`

The updated FastAPI server, providing the query and management endpoints for the NAS gateway.

```python
# horace/mcp_server.py

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query

from horace.catalog import CatalogManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Horace NAS Gateway MCP",
    description="Provides cataloging, versioning, and search for the Irina Storage.",
    version="2.1.0",
)

# This will be replaced by the actual instance in main.py
catalog: Optional[CatalogManager] = None

@app.on_event("startup")
async def startup_event():
    # In a real app, you might use dependency injection (e.g., FastAPI's Depends)
    # but for simplicity, we use a global-like module variable.
    # The actual instance is created and assigned in main.py
    if catalog is None:
        raise RuntimeError("CatalogManager not initialized. Run through main.py.")
    await catalog.connect()

@app.on_event("shutdown")
async def shutdown_event():
    if catalog:
        await catalog.close()

@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

@app.get("/search", response_model=List[Dict[str, Any]], tags=["Files"])
async def search_files(
    q: str = Query(..., min_length=1, description="Search query for file paths.")
):
    """
    Searches the catalog for files with paths matching the query.
    """
    if not catalog:
        raise HTTPException(status_code=503, detail="Service not initialized")
    results = await catalog.search_files(query=q)
    return results

@app.get("/info", response_model=Dict[str, Any], tags=["Files"])
async def get_file_info(
    path: str = Query(..., description="The relative path to the file within the storage.")
):
    """
    Retrieves detailed metadata and version history for a specific file.
    """
    if not catalog:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    info = await catalog.get_file_info(file_path=path)
    if info is None:
        raise HTTPException(status_code=404, detail=f"File not found in catalog: {path}")
    return info

@app.post("/restore_version", tags=["Files"])
async def restore_version(path: str, checksum: str):
    """
    Restores a specific version of a file.

    NOTE: The v2.1 requirements state the primary mechanism for this is out of scope.
    This endpoint serves as a placeholder for a future implementation that would
    search ZFS snapshots or a content-addressable store to retrieve the file
    content associated with the given checksum and write it to the specified path.
    """
    logger.warning(
        f"Placeholder RESTORE request for path='{path}' with checksum='{checksum}'. "
        "Actual restoration logic is not implemented in this version."
    )
    # 1. Validate that the checksum is a known historical version for the path.
    # 2. Search ZFS snapshots for a file with this content hash.
    # 3. If found, copy it to the destination path.
    # 4. The watcher will automatically pick up the change and update the catalog.
    raise HTTPException(
        status_code=501,
        detail="File content restoration from checksum is not implemented. "
               "This is a placeholder for a future feature. "
               "For disaster recovery, use ZFS snapshot restoration."
    )

@app.get("/collections", tags=["Collections"])
async def list_collections():
    """
    (Placeholder) Lists logical collections.
    
    In this NAS gateway model, collections are simply the top-level directories.
    """
    if not catalog or not catalog.base_path.exists():
        raise HTTPException(status_code=503, detail="Storage path not accessible")

    collections = [
        d.name for d in catalog.base_path.iterdir() if d.is_dir()
    ]
    return {"collections": collections}

```

---

### `horace/main.py`

The main entry point for the Horace service. It orchestrates the startup of all components: catalog, watcher, server, and the ZFS snapshot scheduler.

```python
# horace/main.py

import asyncio
import logging
import os
from pathlib import Path

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import horace.mcp_server as mcp_server
from horace.catalog import CatalogManager
from horace.watcher import WatcherService
from horace.zfs_ops import create_snapshot, prune_snapshots

# --- Configuration ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
FILES_PATH = Path(os.environ.get("HORACE_FILES_PATH", "/mnt/irina_storage/files"))
METADATA_PATH = Path(os.environ.get("HORACE_METADATA_PATH", "/mnt/irina_storage/.horace"))
DB_PATH = METADATA_PATH / "catalog.db"
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", 8000))

# ZFS Configuration
ENABLE_ZFS_SNAPSHOTS = os.environ.get("ENABLE_ZFS_SNAPSHOTS", "true").lower() == "true"
ZFS_DATASET = os.environ.get("ZFS_DATASET", "tank/horace/files")
ZFS_RETENTION = {
    "hourly": 24,
    "daily": 14,
    "weekly": 12, # ~3 months
    "monthly": 12 # 1 year
}

# --- Logging Setup ---
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("uvicorn").setLevel(LOG_LEVEL)
logging.getLogger("apscheduler").setLevel("WARNING")
logger = logging.getLogger(__name__)


async def run_snapshot_task(prefix: str):
    """Async wrapper to run snapshot creation in a thread pool."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,  # Use default executor
        create_snapshot,
        ZFS_DATASET,
        prefix
    )

async def run_prune_task():
    """Async wrapper to run snapshot pruning."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        prune_snapshots,
        ZFS_DATASET,
        ZFS_RETENTION
    )

async def main():
    """Main function to initialize and run all services."""
    logger.info("--- Starting Horace NAS Gateway v2.1 ---")
    
    # 1. Initialize Catalog Manager
    catalog = CatalogManager(db_path=DB_PATH, base_path=FILES_PATH)
    await catalog.connect()
    
    # Make catalog instance available to the web server
    mcp_server.catalog = catalog

    # 2. Perform Initial Filesystem Scan (Reconciliation)
    await catalog.reconcile()

    # 3. Initialize Watcher Service
    watcher = WatcherService(catalog_manager=catalog, watch_path=FILES_PATH)

    # 4. Initialize API Server
    config = uvicorn.Config(mcp_server.app, host=API_HOST, port=API_PORT, log_level=LOG_LEVEL.lower())
    server = uvicorn.Server(config)

    # 5. Initialize ZFS Snapshot Scheduler
    scheduler = AsyncIOScheduler()
    if ENABLE_ZFS_SNAPSHOTS:
        logger.info(f"ZFS snapshotting enabled for dataset '{ZFS_DATASET}'")
        scheduler.add_job(run_snapshot_task, CronTrigger(minute=0), args=["hourly"])
        scheduler.add_job(run_snapshot_task, CronTrigger(hour=0, minute=5), args=["daily"])
        scheduler.add_job(run_snapshot_task, CronTrigger(day_of_week='sun', hour=1, minute=5), args=["weekly"])
        scheduler.add_job(run_snapshot_task, CronTrigger(day=1, hour=2, minute=5), args=["monthly"])
        scheduler.add_job(run_prune_task, CronTrigger(hour=3, minute=0)) # Prune daily
        scheduler.start()
    else:
        logger.warning("ZFS snapshotting is disabled.")

    # Run watcher and server concurrently
    try:
        await asyncio.gather(
            watcher.run(),
            server.serve()
        )
    except asyncio.CancelledError:
        logger.info("Main task cancelled. Shutting down.")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await catalog.close()
        logger.info("--- Horace NAS Gateway shut down gracefully ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")

```

---

### `Dockerfile`

A production-ready Dockerfile that builds the Horace service, creates a non-root user, and sets the appropriate entry point.

```dockerfile
# Dockerfile

# Use a specific, recent version of Python for reproducibility
FROM python:3.11.5-slim-bullseye

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY horace/ /app/horace/

# Change ownership of the app directory to the non-root user
# Note: Volumes mounted later will have their own ownership
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "-m", "horace.main"]
```

---

### `docker-compose.yml`

This file defines the Horace service and its required ZFS-backed volumes, along with an example of how another service (`playfair-mcp`) would consume the shared storage.

```yaml
# docker-compose.yml

version: '3.8'

volumes:
  # This volume maps to the ZFS dataset shared with all services.
  # The host path /mnt/tank/horace/files must exist and be a ZFS dataset mountpoint.
  # Ensure its ownership on the host matches the UID/GID below (e.g., `chown 1000:1000 /mnt/tank/horace/files`).
  irina_storage_files:
    driver: local
    driver_opts:
      type: none
      device: /mnt/tank/horace/files # <-- IMPORTANT: CHANGE TO YOUR HOST PATH
      o: bind

  # This volume maps to Horace's private metadata dataset.
  # It should only be mounted by the Horace container.
  # Ensure ownership on the host matches (e.g., `chown 1000:1000 /mnt/tank/horace/metadata`).
  irina_storage_metadata:
    driver: local
    driver_opts:
      type: none
      device: /mnt/tank/horace/metadata # <-- IMPORTANT: CHANGE TO YOUR HOST PATH
      o: bind

services:
  horace-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    # Run as a non-root user. This UID/GID must match the ownership
    # of the ZFS datasets on the host.
    user: "1000:1000"
    ports:
      - "8000:8000"
    volumes:
      # Mounts the shared files directory (read-write)
      - irina_storage_files:/mnt/irina_storage/files
      # Mounts the private metadata directory
      - irina_storage_metadata:/mnt/irina_storage/.horace
      # Mount /etc/localtime to ensure container time matches host time for snapshots
      - /etc/localtime:/etc/localtime:ro
    environment:
      # These paths match the mount points inside the container
      - HORACE_FILES_PATH=/mnt/irina_storage/files
      - HORACE_METADATA_PATH=/mnt/irina_storage/.horace
      # Set to 'false' to disable ZFS snapshot creation from within Docker
      - ENABLE_ZFS_SNAPSHOTS=true 
      - ZFS_DATASET=tank/horace/files # The dataset name to snapshot
      - LOG_LEVEL=INFO
    # To allow Horace to run zfs commands, the Docker socket or zfs-tools could be
    # mapped into the container. This is a security risk. A better production
    # approach is to run snapshotting via a cron job on the host.
    # For this implementation, we assume zfs commands are available if enabled.
    # To make them available, you could install zfs-tools in the Dockerfile
    # and give the container sufficient privileges, though this is not recommended.
    # A safer alternative is to have a host-based cron job.
    # For simplicity here, we assume the feature can be toggled.

  # --- Example of another service using the shared storage ---
  playfair-mcp:
    image: alpine:latest
    # This is just a placeholder to demonstrate the mount
    command: sh -c "while true; do echo 'Writing file...' > /mnt/irina_storage/files/playfair/test-$(date +%s).txt; sleep 10; done"
    restart: unless-stopped
    user: "1000:1000"
    volumes:
      # This service ONLY mounts the shared files volume.
      # It has no access to Horace's private metadata.
      - irina_storage_files:/mnt/irina_storage/files
```

---

### `migration/migrate_to_nas.py`

A command-line script to guide an administrator through the migration process, covering planning, infrastructure validation, data migration, and the initial catalog scan.

```python
# migration/migrate_to_nas.py

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add project root to path to import horace modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from horace.catalog import CatalogManager

# --- Basic Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("migration_script")

# --- Helper Functions ---
def print_header(title: str):
    """Prints a formatted header."""
    print("\n" + "=" * 80)
    print(f"// {title.upper()}")
    print("=" * 80)

def confirm(prompt: str) -> bool:
    """Asks the user for confirmation."""
    while True:
        choice = input(f"{prompt} [y/N]: ").lower().strip()
        if choice in ['y', 'yes']:
            return True
        if choice in ['n', 'no', '']:
            return False

def check_command(command: str) -> bool:
    """Checks if a command exists on the system."""
    return shutil.which(command) is not None

# --- Migration Phases ---

def phase_0_planning():
    print_header("Phase 0: Planning and Validation")
    print("""
This script will guide you through migrating your data to the Horace NAS Gateway.

REQUIREMENTS:
1.  You must have root or sudo access on the host machine.
2.  ZFS must be installed and a zpool (e.g., 'tank') must be available.
3.  Your legacy data must be accessible from this machine.
4.  All services should be stopped before data migration (Phase 2).

ROLLBACK PLAN:
-   This script does NOT delete your source data.
-   A backup of your source data is STRONGLY recommended.
-   To roll back, stop the new Horace services, point your applications back
    to the original data source, and restore from your backup if needed.
""")
    if not confirm("Have you read the plan and created a full backup of your data?"):
        logger.error("Backup is essential. Aborting migration.")
        sys.exit(1)

def phase_1_infrastructure(files_dataset: str, metadata_dataset: str, uid: int, gid: int):
    print_header("Phase 1: Infrastructure Setup")
    print(f"""
This phase requires you to run ZFS commands on the HOST machine.
The script will provide the commands for you to execute.

  - Files Dataset:    {files_dataset}
  - Metadata Dataset: {metadata_dataset}
  - Ownership:        UID={uid}, GID={gid}
""")
    if not check_command("zfs"):
        logger.error("`zfs` command not found. Please ensure ZFS is installed and in your PATH.")
        sys.exit(1)

    parent_dataset = os.path.dirname(files_dataset)
    files_mountpoint = f"/mnt/{files_dataset}"
    metadata_mountpoint = f"/mnt/{metadata_dataset}"

    commands = [
        f"sudo zfs create {parent_dataset}",
        f"sudo zfs create -o compression=lz4 -o atime=off -o mountpoint={files_mountpoint} {files_dataset}",
        f"sudo zfs create -o compression=lz4 -o atime=off -o mountpoint={metadata_mountpoint} {metadata_dataset}",
        f"sudo chown -R {uid}:{gid} {files_mountpoint}",
        f"sudo chown -R {uid}:{gid} {metadata_mountpoint}",
        f"ls -ld {files_mountpoint}",
        f"ls -ld {metadata_mountpoint}",
    ]

    print("\nPlease execute these commands on your host machine in another terminal:")
    for cmd in commands:
        print(f"  {cmd}")
    
    if not confirm("\nHave you successfully executed all the infrastructure setup commands?"):
        logger.error("Infrastructure setup is required to continue. Aborting.")
        sys.exit(1)
    
    logger.info("Infrastructure validation successful.")
    return Path(files_mountpoint), Path(metadata_mountpoint)


def phase_2_migration(source_dir: Path, dest_dir: Path, metadata_dir: Path):
    print_header("Phase 2: Data Migration and Initial Scan")
    print(f"""
This phase will:
1.  Copy data from your source directory to the new ZFS dataset.
    - Source: {source_dir}
    - Destination: {dest_dir}
2.  Perform the initial scan to populate the Horace catalog.
    - Catalog DB: {metadata_dir / 'catalog.db'}
""")
    if not source_dir.is_dir():
        logger.error(f"Source directory '{source_dir}' does not exist. Aborting.")
        sys.exit(1)
    
    if not confirm("Ready to begin copying data? Ensure all services writing to the source are stopped."):
        sys.exit(0)

    # Data copy using rsync for efficiency
    if check_command("rsync"):
        logger.info("Using rsync to copy data...")
        try:
            subprocess.run(
                ["rsync", "-av", "--info=progress2", str(source_dir) + "/", str(dest_dir) + "/"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Rsync failed with error: {e}")
            sys.exit(1)
    else:
        logger.warning("rsync not found. Falling back to Python's shutil.copytree (may be slower).")
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
    
    logger.info("Data copy complete.")

    if not confirm("Data has been copied. Proceed with initial catalog scan?"):
        sys.exit(0)
    
    # Initial scan
    async def run_scan():
        catalog = CatalogManager(db_path=metadata_dir / "catalog.db", base_path=dest_dir)
        await catalog.connect()
        await catalog.reconcile()
        await catalog.close()

    import asyncio
    asyncio.run(run_scan())
    logger.info("Initial catalog scan complete.")


def phase_3_integration():
    print_header("Phase 3: Service Integration")
    print("""
The migration is nearly complete. Follow these final steps:

1.  **Update `docker-compose.yml`:**
    - Ensure the `device` paths for the `irina_storage_files` and
      `irina_storage_metadata` volumes are correct.
    - Update all services to mount `irina_storage_files` at `/mnt/irina_storage/files`.
    - Remove old volume mounts.

2.  **Update Service Code:**
    - Implement the "write-to-temporary-file-and-rename" pattern for all
      file creation operations to ensure atomicity.
    - Remove all legacy manual `register_file` API calls to Horace.

3.  **Deploy:**
    - Start the new stack with `docker-compose up -d`.
    - Monitor the logs of Horace and other services for any errors.

Congratulations! Your system is now running on the Horace NAS Gateway.
""")

def main():
    parser = argparse.ArgumentParser(description="Horace NAS Gateway Migration Tool")
    parser.add_argument("source_directory", type=Path, help="The source directory of your existing data.")
    parser.add_argument("--files-dataset", default="tank/horace/files", help="Name of the ZFS dataset for files.")
    parser.add_argument("--metadata-dataset", default="tank/horace/metadata", help="Name of the ZFS dataset for metadata.")
    parser.add_argument("--uid", type=int, default=1000, help="User ID for file ownership.")
    parser.add_argument("--gid", type=int, default=1000, help="Group ID for file ownership.")
    args = parser.parse_args()

    phase_0_planning()
    files_mountpoint, metadata_mountpoint = phase_1_infrastructure(args.files_dataset, args.metadata_dataset, args.uid, args.gid)
    phase_2_migration(args.source_directory, files_mountpoint, metadata_mountpoint)
    phase_3_integration()

if __name__ == "__main__":
    main()
```
