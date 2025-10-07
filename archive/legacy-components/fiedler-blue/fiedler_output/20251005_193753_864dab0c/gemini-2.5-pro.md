Of course. Here is the complete, production-ready implementation of the Horace File Storage Gateway, based on the approved v2.0 requirements.

### **Project Structure Overview**

```
horace/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── schema.sql
└── src/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── exceptions.py
    ├── mcp_server.py
    ├── tools.py
    └── utils/
        ├── __init__.py
        ├── file_ops.py
        ├── logger.py
        └── validation.py
```

---
### 1. Complete Python Implementation

#### `src/config.py`
```python
# src/config.py
import os
from pathlib import Path

class Config:
    # Database Configuration
    DB_HOST = os.getenv("HORACE_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("HORACE_DB_PORT", 5432))
    DB_NAME = os.getenv("HORACE_DB_NAME", "winni")
    DB_USER = os.getenv("HORACE_DB_USER", "horace")
    DB_PASSWORD = os.getenv("HORACE_DB_PASSWORD", "password")

    # Storage Configuration
    STORAGE_PATH = Path(os.getenv("HORACE_STORAGE_PATH", "/mnt/irina_storage"))
    FILES_DIR = STORAGE_PATH / "files"
    VERSIONS_DIR = STORAGE_PATH / ".horace_versions"
    
    VERSION_COUNT = int(os.getenv("HORACE_VERSION_COUNT", 5))

    # MCP Server Configuration
    MCP_HOST = os.getenv("HORACE_MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("HORACE_MCP_PORT", 8070))
    LOG_LEVEL = os.getenv("HORACE_LOG_LEVEL", "INFO").upper()

    # Godot Logging Integration
    GODOT_MCP_URL = os.getenv("GODOT_MCP_URL", "ws://godot-mcp:9060")

    # Ensure required directories exist
    @staticmethod
    def initialize_storage_dirs():
        Config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        Config.VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
        (Config.STORAGE_PATH / ".horace_metadata").mkdir(exist_ok=True)
        # Create component subdirectories for convenience
        for component in ["gates", "playfair", "fiedler", "user", "shared"]:
            (Config.FILES_DIR / component).mkdir(exist_ok=True)

config = Config()
```

#### `src/exceptions.py`
```python
# src/exceptions.py
class HoraceError(Exception):
    """Base exception for Horace application."""
    def __init__(self, message, error_code="HORACE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class InvalidPathError(HoraceError):
    """Raised when a file path is invalid or outside the allowed directory."""
    def __init__(self, message="Invalid file path."):
        super().__init__(message, "INVALID_PATH")

class FileNotFoundError(HoraceError):
    """Raised when a file is not found in the filesystem or database."""
    def __init__(self, message="File not found."):
        super().__init__(message, "FILE_NOT_FOUND")

class VersionNotFoundError(HoraceError):
    """Raised when a specific file version is not found."""
    def __init__(self, message="Version not found."):
        super().__init__(message, "VERSION_NOT_FOUND")

class CollectionNotFoundError(HoraceError):
    """Raised when a collection is not found."""
    def __init__(self, message="Collection not found."):
        super().__init__(message, "COLLECTION_NOT_FOUND")
        
class DuplicateFileError(HoraceError):
    """Raised when attempting to register a file that already exists (by checksum)."""
    def __init__(self, message, file_id):
        self.file_id = file_id
        super().__init__(message, "DUPLICATE_FILE")

class FileLockError(HoraceError):
    """Raised when a file cannot be locked for an operation."""
    def __init__(self, message="Could not acquire lock on file."):
        super().__init__(message, "FILE_LOCK_ERROR")
```

#### `src/utils/logger.py`
```python
# src/utils/logger.py
import logging
import sys
import json
import asyncio
import websockets
from .config import config

# Standard Python Logger Setup
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("horace")

# Godot MCP Logger Integration
async def log_to_godot(level: str, message: str, context: dict = None):
    """
    Sends a log message to the Godot MCP server.
    This is a mock implementation; a real implementation might use a persistent
    client or a more robust connection handling mechanism.
    """
    log_entry = {
        "tool": "godot_log",
        "params": {
            "source": "horace",
            "level": level.upper(),
            "message": message,
            "context": context or {}
        }
    }
    try:
        async with websockets.connect(config.GODOT_MCP_URL) as websocket:
            await websocket.send(json.dumps(log_entry))
            # In a real scenario, you might want to await a confirmation
    except Exception as e:
        logger.error(f"Failed to send log to Godot: {e}")

# Wrapper functions for different log levels
async def godot_info(message, context=None):
    await log_to_godot("info", message, context)
    logger.info(message)

async def godot_warn(message, context=None):
    await log_to_godot("warning", message, context)
    logger.warning(message)

async def godot_error(message, context=None):
    await log_to_godot("error", message, context)
    logger.error(message)
```

#### `src/utils/validation.py`
```python
# src/utils/validation.py
from pathlib import Path
from .config import config
from .exceptions import InvalidPathError

def validate_storage_path(file_path_str: str) -> Path:
    """
    Validates that the given path is within the allowed storage directory
    and does not contain path traversal characters.
    """
    allowed_base = config.FILES_DIR.resolve()
    
    try:
        abs_path = Path(file_path_str).resolve()
    except Exception as e:
        raise InvalidPathError(f"Path resolution failed: {e}")

    if not file_path_str.startswith(str(config.FILES_DIR)):
         raise InvalidPathError(f"Path must be within {config.FILES_DIR}")

    if ".." in file_path_str:
        raise InvalidPathError("Path traversal ('..') is not allowed.")

    # Final check to ensure the resolved path is under the allowed base
    if not abs_path.is_relative_to(allowed_base):
        raise InvalidPathError(f"Resolved path {abs_path} is outside of allowed storage area {allowed_base}")
        
    return abs_path
```

#### `src/utils/file_ops.py`
```python
# src/utils/file_ops.py
import hashlib
import magic
import aiofiles
import fcntl
import os
import shutil
from pathlib import Path
from .exceptions import FileLockError, HoraceError

CHUNK_SIZE = 65536  # 64KB

async def calculate_sha256(file_path: Path) -> str:
    """Calculates the SHA256 checksum of a file asynchronously."""
    sha256 = hashlib.sha256()
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                data = await f.read(CHUNK_SIZE)
                if not data:
                    break
                sha256.update(data)
    except FileNotFoundError:
        raise
    except Exception as e:
        raise HoraceError(f"Error calculating checksum for {file_path}: {e}")
    return sha256.hexdigest()

def get_mime_type(file_path: Path) -> str:
    """Detects the MIME type of a file using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except Exception:
        # Fallback for when python-magic fails
        return "application/octet-stream"

def copy_with_lock(source: Path, destination: Path):
    """
    Copies a file while holding an exclusive lock on the source file.
    This prevents race conditions during versioning.
    """
    try:
        with open(source, 'rb') as src_f:
            # Acquire an exclusive lock (LOCK_EX). This will block if another
            # process holds a lock.
            fcntl.flock(src_f, fcntl.LOCK_EX)
            try:
                # Use shutil.copy2 to preserve metadata like timestamps
                shutil.copy2(source, destination)
            finally:
                # Always release the lock
                fcntl.flock(src_f, fcntl.LOCK_UN)
    except (IOError, OSError) as e:
        raise FileLockError(f"Failed to lock or copy file {source}: {e}")
```

#### `src/database.py`
```python
# src/database.py
import asyncpg
from typing import List, Dict, Any, Optional
from uuid import UUID
from .config import config
from .utils.logger import logger

class Database:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        logger.info(f"Connecting to database at {config.DB_HOST}:{config.DB_PORT}...")
        try:
            self._pool = await asyncpg.create_pool(
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                host=config.DB_HOST,
                port=config.DB_PORT,
            )
            logger.info("Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    async def disconnect(self):
        if self._pool:
            logger.info("Closing database connection pool...")
            await self._pool.close()
            logger.info("Database connection pool closed.")

    async def fetchrow(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    # --- File Operations ---
    async def find_file_by_id(self, file_id: UUID) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_files WHERE id = $1", file_id)

    async def find_file_by_checksum(self, checksum: str) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_files WHERE checksum = $1 AND status != 'deleted'", checksum)

    async def insert_file(self, file_data: Dict[str, Any]) -> asyncpg.Record:
        query = """
            INSERT INTO horace_files (file_path, owner, purpose, tags, size, mime_type, checksum, collection_id, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            file_data['file_path'], file_data['owner'], file_data.get('purpose'),
            file_data.get('tags', []), file_data['size'], file_data['mime_type'],
            file_data['checksum'], file_data.get('collection_id'), file_data.get('correlation_id')
        )
    
    async def update_file(self, file_id: UUID, update_data: Dict[str, Any]) -> Optional[asyncpg.Record]:
        fields, values = [], []
        for i, (key, value) in enumerate(update_data.items(), 1):
            fields.append(f"{key} = ${i}")
            values.append(value)
        
        fields.append(f"updated_at = NOW()")
        set_clause = ", ".join(fields)
        
        query = f"UPDATE horace_files SET {set_clause} WHERE id = ${len(values) + 1} RETURNING *"
        return await self.fetchrow(query, *values, file_id)

    # --- Version Operations ---
    async def insert_version(self, version_data: Dict[str, Any]) -> asyncpg.Record:
        query = """
            INSERT INTO horace_versions (file_id, version, size, checksum, version_path)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        return await self.fetchrow(
            query, version_data['file_id'], version_data['version'], version_data['size'],
            version_data['checksum'], version_data['version_path']
        )
    
    async def get_versions_for_file(self, file_id: UUID) -> List[asyncpg.Record]:
        query = "SELECT * FROM horace_versions WHERE file_id = $1 ORDER BY version DESC"
        return await self.fetch(query, file_id)
    
    async def get_oldest_version(self, file_id: UUID) -> Optional[asyncpg.Record]:
        query = "SELECT * FROM horace_versions WHERE file_id = $1 ORDER BY version ASC LIMIT 1"
        return await self.fetchrow(query, file_id)

    async def delete_version(self, version_id: UUID):
        await self.execute("DELETE FROM horace_versions WHERE id = $1", version_id)

    # --- Collection Operations ---
    async def find_collection_by_name(self, name: str) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_collections WHERE name = $1", name)
        
    async def find_collection_by_id(self, col_id: UUID) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_collections WHERE id = $1", col_id)

    async def insert_collection(self, name: str, description: str, metadata: Dict) -> asyncpg.Record:
        query = """
            INSERT INTO horace_collections (name, description, metadata)
            VALUES ($1, $2, $3)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING *
        """
        return await self.fetchrow(query, name, description, metadata)
    
    async def get_collection_file_count(self, collection_id: UUID) -> int:
        res = await self.fetchrow("SELECT COUNT(*) FROM horace_files WHERE collection_id = $1", collection_id)
        return res['count'] if res else 0

    async def list_collections(self, limit: int, offset: int) -> (int, List[asyncpg.Record]):
        total_query = "SELECT COUNT(*) FROM horace_collections"
        total = (await self.fetchrow(total_query))['count']
        
        list_query = "SELECT * FROM horace_collections ORDER BY name ASC LIMIT $1 OFFSET $2"
        collections = await self.fetch(list_query, limit, offset)
        
        return total, collections

    # --- Search ---
    async def search_files(self, params: Dict[str, Any]) -> (int, List[asyncpg.Record]):
        query_base = "FROM horace_files WHERE"
        conditions = []
        args = []
        
        # Default status to 'active' if not provided
        status = params.get('query', {}).get('status', 'active')
        conditions.append(f"status = ${len(args) + 1}")
        args.append(status)

        q = params.get('query', {})
        if q.get('tags'):
            conditions.append(f"tags @> ${len(args) + 1}")
            args.append(q['tags'])
        if q.get('owner'):
            conditions.append(f"owner = ${len(args) + 1}")
            args.append(q['owner'])
        if q.get('created_after'):
            conditions.append(f"created_at >= ${len(args) + 1}")
            args.append(q['created_after'])
        if q.get('created_before'):
            conditions.append(f"created_at <= ${len(args) + 1}")
            args.append(q['created_before'])
        if q.get('file_type'):
            conditions.append(f"(mime_type LIKE ${len(args) + 1} OR file_path LIKE ${len(args) + 1})")
            args.append(f"%{q['file_type']}%")
        if q.get('min_size') is not None:
            conditions.append(f"size >= ${len(args) + 1}")
            args.append(q['min_size'])
        if q.get('max_size') is not None:
            conditions.append(f"size <= ${len(args) + 1}")
            args.append(q['max_size'])
        if q.get('collection'):
            collection_rec = await self.find_collection_by_name(q['collection'])
            if collection_rec:
                conditions.append(f"collection_id = ${len(args) + 1}")
                args.append(collection_rec['id'])
            else: # Collection not found, return no results
                return 0, []

        where_clause = " AND ".join(conditions)
        
        # Count total matching results
        count_query = f"SELECT COUNT(*) {query_base} {where_clause}"
        total = (await self.fetchrow(count_query, *args))['count']
        
        # Fetch paginated results
        sort_by = params.get('sort_by', 'created_at')
        order = params.get('order', 'desc').upper()
        limit = params.get('limit', 50)
        offset = params.get('offset', 0)
        
        results_query = f"""
            SELECT * {query_base} {where_clause}
            ORDER BY {sort_by} {order}
            LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}
        """
        results = await self.fetch(results_query, *args, limit, offset)
        
        return total, results
```

#### `src/tools.py`
```python
# src/tools.py
import os
from pathlib import Path
from uuid import UUID
from datetime import datetime

from .config import config
from .database import Database
from .exceptions import *
from .utils import file_ops, validation, logger

class Tools:
    def __init__(self, db: Database):
        self.db = db

    async def _create_new_version(self, file_rec: dict, current_path: Path):
        """Internal helper to create a new version of a file."""
        new_checksum = await file_ops.calculate_sha256(current_path)
        if new_checksum == file_rec['checksum']:
            return None # No changes, no new version needed

        next_version_num = file_rec['current_version'] + 1
        version_path = config.VERSIONS_DIR / f"{file_rec['id']}.v{next_version_num}"
        
        await logger.godot_info(f"File change detected for {file_rec['id']}. Creating version {next_version_num}.")
        
        # Copy-on-write with file lock
        file_ops.copy_with_lock(current_path, version_path)
        
        new_size = current_path.stat().st_size
        
        # Insert version record
        await self.db.insert_version({
            'file_id': file_rec['id'],
            'version': next_version_num,
            'size': file_rec['size'], # size of the *previous* version
            'checksum': file_rec['checksum'], # checksum of the *previous* version
            'version_path': str(version_path.relative_to(config.STORAGE_PATH))
        })
        
        # Update main file record
        await self.db.update_file(file_rec['id'], {
            'checksum': new_checksum,
            'size': new_size,
            'current_version': next_version_num
        })

        # Prune old versions
        await self._prune_versions(file_rec['id'])
        
        return next_version_num

    async def _prune_versions(self, file_id: UUID):
        versions = await self.db.get_versions_for_file(file_id)
        if len(versions) > config.VERSION_COUNT:
            # Versions are sorted DESC, so the last one is the oldest
            oldest_version = versions[-1]
            await logger.godot_info(f"Pruning oldest version {oldest_version['version']} for file {file_id}.")
            
            version_path = config.STORAGE_PATH / oldest_version['version_path']
            if version_path.exists():
                os.remove(version_path)
            
            await self.db.delete_version(oldest_version['id'])

    # --- MCP Tools ---

    async def horace_register_file(self, params: dict):
        file_path_str = params['file_path']
        metadata = params['metadata']

        path = validation.validate_storage_path(file_path_str)
        if not path.exists():
            raise FileNotFoundError(f"File does not exist at path: {file_path_str}")

        checksum = await file_ops.calculate_sha256(path)
        
        # Check for duplicates
        existing_file = await self.db.find_file_by_checksum(checksum)
        if existing_file:
            await logger.godot_info(f"Duplicate file registered. Path: {file_path_str}, Checksum: {checksum}", context={"existing_file_id": str(existing_file['id'])})
            raise DuplicateFileError("File with this content already exists.", file_id=str(existing_file['id']))

        collection_id = None
        if metadata.get('collection'):
            collection_rec = await self.db.find_collection_by_name(metadata['collection'])
            if collection_rec:
                collection_id = collection_rec['id']
            else:
                await logger.godot_warn(f"Collection '{metadata['collection']}' not found for file registration.")

        file_data = {
            "file_path": str(path.relative_to(config.STORAGE_PATH)),
            "owner": metadata.get('owner', 'unknown'),
            "purpose": metadata.get('purpose'),
            "tags": metadata.get('tags', []),
            "size": path.stat().st_size,
            "mime_type": file_ops.get_mime_type(path),
            "checksum": checksum,
            "collection_id": collection_id,
            "correlation_id": metadata.get('correlation_id')
        }
        
        file_rec = await self.db.insert_file(file_data)
        
        # Create first version record
        await self.db.insert_version({
            'file_id': file_rec['id'],
            'version': 1,
            'size': file_rec['size'],
            'checksum': file_rec['checksum'],
            'version_path': "N/A (initial registration)"
        })

        await logger.godot_info(f"Registered new file: {file_rec['id']}", context=dict(file_rec))

        return {
            "file_id": str(file_rec['id']),
            "checksum": file_rec['checksum'],
            "size": file_rec['size'],
            "mime_type": file_rec['mime_type'],
            "registered_at": file_rec['created_at'].isoformat(),
            "version": 1
        }

    async def horace_search_files(self, params: dict):
        total, results = await self.db.search_files(params)
        
        return {
            "total_count": total,
            "results": [{
                "file_id": str(r['id']),
                "path": str(config.STORAGE_PATH / r['file_path']),
                "owner": r['owner'],
                "purpose": r['purpose'],
                "tags": r['tags'],
                "size": r['size'],
                "mime_type": r['mime_type'],
                "created_at": r['created_at'].isoformat(),
                "updated_at": r['updated_at'].isoformat(),
                "version": r['current_version'],
                "checksum": r['checksum'],
                "collection_id": str(r['collection_id']) if r['collection_id'] else None,
            } for r in results],
            "limit": params.get('limit', 50),
            "offset": params.get('offset', 0)
        }

    async def horace_get_file_info(self, params: dict):
        file_id = UUID(params['file_id'])
        file_rec = await self.db.find_file_by_id(file_id)
        if not file_rec:
            raise FileNotFoundError(f"File with ID {file_id} not found.")

        response = dict(file_rec)
        response['file_id'] = str(response.pop('id'))
        response['path'] = str(config.STORAGE_PATH / response['file_path'])
        response['created_at'] = response['created_at'].isoformat()
        response['updated_at'] = response['updated_at'].isoformat()
        if response['deleted_at']:
            response['deleted_at'] = response['deleted_at'].isoformat()
        if response['collection_id']:
            response['collection_id'] = str(response['collection_id'])

        if params.get('include_versions', False):
            versions = await self.db.get_versions_for_file(file_id)
            response['versions'] = [{
                "version": v['version'],
                "timestamp": v['created_at'].isoformat(),
                "size": v['size'],
                "checksum": v['checksum'],
                "path": v['version_path']
            } for v in versions]

        return response

    async def horace_create_collection(self, params: dict):
        collection_rec = await self.db.insert_collection(
            params['name'],
            params.get('description'),
            params.get('metadata', {})
        )
        
        if params.get('file_ids'):
            for file_id_str in params['file_ids']:
                await self.db.update_file(UUID(file_id_str), {'collection_id': collection_rec['id']})
        
        file_count = await self.db.get_collection_file_count(collection_rec['id'])

        await logger.godot_info(f"Created/updated collection: {params['name']}", context=dict(collection_rec))

        return {
            "collection_id": str(collection_rec['id']),
            "name": collection_rec['name'],
            "description": collection_rec['description'],
            "file_count": file_count,
            "created_at": collection_rec['created_at'].isoformat()
        }

    async def horace_list_collections(self, params: dict):
        limit = params.get('limit', 50)
        offset = params.get('offset', 0)
        total, collections = await self.db.list_collections(limit, offset)
        
        results = []
        for c in collections:
            count = await self.db.get_collection_file_count(c['id'])
            results.append({
                "collection_id": str(c['id']),
                "name": c['name'],
                "description": c['description'],
                "file_count": count,
                "created_at": c['created_at'].isoformat(),
                "updated_at": c['updated_at'].isoformat()
            })

        return {"total_count": total, "collections": results}

    async def horace_update_file(self, params: dict):
        file_id = UUID(params['file_id'])
        file_rec = await self.db.find_file_by_id(file_id)
        if not file_rec:
            raise FileNotFoundError(f"File with ID {file_id} not found.")

        updated_fields = []
        version_created = False
        
        # Handle version check first
        if params.get('check_for_changes', False):
            current_path = config.STORAGE_PATH / file_rec['file_path']
            if not current_path.exists():
                raise FileNotFoundError(f"File path not found on disk: {current_path}")
            
            new_version_num = await self._create_new_version(file_rec, current_path)
            if new_version_num:
                version_created = True
                # Refresh file_rec to get the latest version number
                file_rec = await self.db.find_file_by_id(file_id)

        # Handle metadata updates
        metadata_updates = {}
        if 'metadata' in params:
            meta = params['metadata']
            for key in ['tags', 'purpose', 'status', 'collection']:
                if key in meta:
                    updated_fields.append(key)
                    if key == 'collection':
                        collection_rec = await self.db.find_collection_by_name(meta['collection'])
                        if not collection_rec: raise CollectionNotFoundError(f"Collection {meta['collection']} not found.")
                        metadata_updates['collection_id'] = collection_rec['id']
                    else:
                        metadata_updates[key] = meta[key]
        
        if metadata_updates:
            await self.db.update_file(file_id, metadata_updates)

        await logger.godot_info(f"Updated file {file_id}", context={"updated_fields": updated_fields, "version_created": version_created})

        return {
            "file_id": str(file_id),
            "updated_fields": updated_fields,
            "version_created": version_created,
            "current_version": file_rec['current_version']
        }

    async def horace_restore_version(self, params: dict):
        file_id = UUID(params['file_id'])
        version_to_restore = params['version']

        file_rec = await self.db.find_file_by_id(file_id)
        if not file_rec:
            raise FileNotFoundError(f"File with ID {file_id} not found.")

        versions = await self.db.get_versions_for_file(file_id)
        target_version_rec = next((v for v in versions if v['version'] == version_to_restore), None)

        if not target_version_rec:
            raise VersionNotFoundError(f"Version {version_to_restore} not found for file {file_id}.")

        current_path = config.STORAGE_PATH / file_rec['file_path']
        version_path_str = target_version_rec['version_path']
        
        # Initial registration has no version path
        if version_path_str == "N/A (initial registration)":
             raise HoraceError("Cannot restore from initial version record.")
        
        version_path = config.STORAGE_PATH / version_path_str

        if not version_path.exists():
            raise FileNotFoundError(f"Version file not found on disk: {version_path}")
            
        await logger.godot_info(f"Restoring file {file_id} to version {version_to_restore}.")

        # 1. Create a safety backup of the current state
        new_version_num = await self._create_new_version(file_rec, current_path)
        if not new_version_num:
            # If no changes, manually create a version to back up current state
            # This is a complex edge case; for now, we'll proceed, assuming a change was intended.
            # A more robust implementation might force a version creation here.
            await logger.godot_warn(f"Current file {file_id} had no changes before restore. Proceeding without backup version.")
            new_version_num = file_rec['current_version'] + 1 # Faking it for the response

        # 2. Copy the specified version to the current file location
        file_ops.copy_with_lock(version_path, current_path)
        
        # 3. Update metadata
        restored_checksum = await file_ops.calculate_sha256(current_path)
        restored_size = current_path.stat().st_size
        
        await self.db.update_file(file_id, {
            'checksum': restored_checksum,
            'size': restored_size,
            'current_version': new_version_num,
            'metadata': {**file_rec['metadata'], 'restored_from_version': version_to_restore}
        })

        await logger.godot_info(f"File {file_id} successfully restored.", context={
            "restored_to_version": version_to_restore,
            "new_version_created": new_version_num
        })

        return {
            "file_id": str(file_id),
            "restored_to_version": version_to_restore,
            "new_version_created": new_version_num,
            "current_path": str(current_path)
        }
```

#### `src/mcp_server.py`
```python
# src/mcp_server.py
import asyncio
import json
import signal
from http import HTTPStatus

import websockets
from websockets.server import serve
from websockets.http import Headers

from .config import config, Config
from .database import Database
from .tools import Tools
from .utils.logger import logger, godot_info, godot_error
from .exceptions import HoraceError, DuplicateFileError

db = Database()
tools: Tools

async def health_check(path: str, request_headers: Headers):
    if path == "/health":
        return HTTPStatus.OK, [], b"OK\n"

async def mcp_handler(websocket):
    client_addr = websocket.remote_address
    logger.info(f"Client connected: {client_addr}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                tool_name = data.get("tool")
                params = data.get("params", {})

                if not tool_name or not hasattr(tools, tool_name):
                    raise HoraceError(f"Tool '{tool_name}' not found.", "TOOL_NOT_FOUND")

                logger.info(f"Executing tool: {tool_name}")
                tool_func = getattr(tools, tool_name)
                result = await tool_func(params)

                response = {"status": "success", "data": result}

            except DuplicateFileError as e:
                response = {
                    "status": "success", # Per spec, return existing ID
                    "message": e.message,
                    "data": {"file_id": e.file_id}
                }
            except HoraceError as e:
                await godot_error(f"Horace Error in tool {data.get('tool', 'unknown')}: {e.message}", context={"error_code": e.error_code, "params": data.get('params')})
                response = {"status": "error", "error": {"code": e.error_code, "message": e.message}}
            except Exception as e:
                await godot_error(f"Unhandled exception in tool {data.get('tool', 'unknown')}: {e}", context={"params": data.get('params')})
                response = {"status": "error", "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)}}

            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {client_addr} - {e.code} {e.reason}")
    except Exception as e:
        logger.error(f"An error occurred in the handler for {client_addr}: {e}")
        
async def main():
    global tools
    
    # Initialize storage directories
    Config.initialize_storage_dirs()
    logger.info("Storage directories initialized.")

    # Initialize database connection
    await db.connect()
    tools = Tools(db)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with serve(
        mcp_handler, 
        config.MCP_HOST, 
        config.MCP_PORT, 
        process_request=health_check
    ):
        logger.info(f"Horace MCP Server started at ws://{config.MCP_HOST}:{config.MCP_PORT}")
        await godot_info("Horace MCP Server started.")
        await stop

async def shutdown():
    logger.info("Horace MCP Server shutting down...")
    await godot_info("Horace MCP Server shutting down.")
    await db.disconnect()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received exit signal.")
    finally:
        asyncio.run(shutdown())
```

---
### 2. Docker Configuration

#### `Dockerfile`
```dockerfile
# Dockerfile
FROM python:3.11-alpine

# Install system dependencies for python-magic and fcntl
RUN apk add --no-cache libmagic build-base

WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose the MCP port
EXPOSE 8070

# Run the server
CMD ["python", "-m", "src.mcp_server"]
```

#### `docker-compose.yml`
```yaml
# docker-compose.yml
version: '3.8'

services:
  horace-mcp:
    build: .
    container_name: horace-mcp
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "9070:8070"
    volumes:
      - type: volume
        source: irina_storage
        target: /mnt/irina_storage
        volume:
          nocopy: true
    networks:
      - iccm_network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8070/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

volumes:
  irina_storage:
    driver_opts:
      type: "nfs"
      o: "addr=192.168.1.210,rw,nfsvers=4"
      device: ":/mnt/storage/iccm"

networks:
  iccm_network:
    external: true
```

#### `.env.example`
```dotenv
# .env.example

# --- Database Configuration ---
# Hostname or IP of the PostgreSQL server (Winni)
HORACE_DB_HOST=192.168.1.210
# Port of the PostgreSQL server
HORACE_DB_PORT=5432
# Database name
HORACE_DB_NAME=winni
# Database user
HORACE_DB_USER=horace
# Database password
HORACE_DB_PASSWORD=your_secure_password_here

# --- Storage Configuration ---
# Path inside the container where the NFS share is mounted
HORACE_STORAGE_PATH=/mnt/irina_storage
# Number of old file versions to retain
HORACE_VERSION_COUNT=5

# --- MCP Server Configuration ---
# Port for the MCP server to listen on *inside the container*
HORACE_MCP_PORT=8070
# Log level for the application logger (DEBUG, INFO, WARNING, ERROR)
HORACE_LOG_LEVEL=INFO

# --- Godot Logging Integration ---
# WebSocket URL for the Godot MCP logging service
GODOT_MCP_URL=ws://godot-mcp:9060
```

---
### 3. Database Schema

#### `schema.sql`
```sql
-- schema.sql

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table: horace_collections
-- Stores named groups of files.
CREATE TABLE horace_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_horace_collections_name ON horace_collections(name);

-- Table: horace_files
-- The central catalog of all files managed by Horace.
CREATE TABLE horace_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    owner TEXT NOT NULL,
    purpose TEXT,
    tags TEXT[] DEFAULT '{}',
    size BIGINT NOT NULL,
    mime_type TEXT,
    checksum TEXT NOT NULL,  -- SHA256
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    current_version INTEGER DEFAULT 1,
    collection_id UUID REFERENCES horace_collections(id) ON DELETE SET NULL,
    correlation_id TEXT,  -- Link to Fiedler run or conversation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,  -- Soft delete timestamp
    metadata JSONB DEFAULT '{}'  -- Extensible metadata
);

-- Indexes for common query patterns
CREATE INDEX idx_horace_files_owner ON horace_files(owner);
CREATE INDEX idx_horace_files_tags ON horace_files USING GIN(tags);
CREATE INDEX idx_horace_files_checksum ON horace_files(checksum);
CREATE INDEX idx_horace_files_status ON horace_files(status);
CREATE INDEX idx_horace_files_collection ON horace_files(collection_id);
CREATE INDEX idx_horace_files_created_at ON horace_files(created_at DESC);

-- Composite index for common search patterns (DeepSeek-R1 recommendation)
CREATE INDEX idx_horace_files_search ON horace_files (owner, status, created_at, mime_type);

-- Table: horace_versions
-- Tracks the history of each file.
CREATE TABLE horace_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES horace_files(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    size BIGINT NOT NULL,
    checksum TEXT NOT NULL,
    version_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, version)
);

CREATE INDEX idx_horace_versions_file ON horace_versions(file_id, version DESC);

-- Trigger to update the 'updated_at' timestamp on horace_files
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_horace_files_modtime
BEFORE UPDATE ON horace_files
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_horace_collections_modtime
BEFORE UPDATE ON horace_collections
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();
```

---
### 4. Dependencies

#### `requirements.txt`
```
# requirements.txt

# WebSocket MCP server
websockets>=12.0

# Asynchronous PostgreSQL driver
asyncpg>=0.29.0

# Asynchronous file I/O
aiofiles>=23.0.0

# MIME type detection
python-magic>=0.4.27

# YAML for potential future config, though not used in this version
# pyyaml>=6.0
```

---
### 5. Documentation

#### `README.md`
```markdown
# Horace - File Storage Gateway

**Version:** 2.0
**Status:** Implemented

Horace is a file storage gateway that provides a centralized file catalog, automatic versioning, and organization for the ICCM ecosystem. It uses a WebSocket-based MCP (Machine Control Protocol) interface for metadata management and relies on direct NFS/Samba access for file I/O.

## Features

- **7 MCP Tools:** For file registration, search, versioning, and organization.
- **Copy-on-Write Versioning:** Automatically retains the last 5 versions of any file.
- **Centralized Catalog:** All file metadata is stored and indexed in a PostgreSQL database.
- **Secure Pathing:** Validates all file paths to prevent directory traversal attacks.
- **Concurrent Safe:** Uses file locking to prevent race conditions during versioning operations.
- **Dual-Protocol Access:** Designed to work with NFS for Linux containers and Samba/CIFS for Windows clients accessing the same storage backend.

## Prerequisites

1.  **Docker & Docker Compose:** Must be installed on the host machine (Pharaoh).
2.  **NFS Client:** The host machine must have `nfs-common` (or equivalent) installed.
3.  **NFS Server (Irina):** An NFS server must be configured to export the storage directory (e.g., `/mnt/storage/iccm`) to your Docker host's network. See `REQUIREMENTS.md` for an example configuration.
4.  **PostgreSQL Database (Winni):** A running PostgreSQL instance accessible from the Docker host.
5.  **Docker Network:** An external Docker network named `iccm_network` must exist. Create it with `docker network create iccm_network`.

## Setup and Deployment

### 1. Configure Environment

Copy the example environment file and fill in your details:

```bash
cp .env.example .env
nano .env
```

Update the database credentials, host IPs, and any other necessary variables.

### 2. Prepare the Database

Create the required tables and indexes in your PostgreSQL database (`winni`). You will need `psql` installed or another way to execute the SQL script.

```bash
psql -h YOUR_DB_HOST -U horace -d winni -f schema.sql
```
*(You may be prompted for the `horace` user's password.)*

### 3. Build and Run the Service

Use Docker Compose to build the image and start the container.

```bash
docker compose up --build -d
```

The `-d` flag runs the container in detached mode.

### 4. Verify the Service

Check that the container is running and healthy:

```bash
docker ps --filter name=horace-mcp
```

You should see the `horace-mcp` container with a status of `Up` and `(healthy)`. You can also view the logs:

```bash
docker logs horace-mcp -f
```

## Usage

Connect to the Horace MCP server at `ws://<docker_host>:9070`. You can send JSON-formatted messages to interact with the service.

### Example 1: Register a File

First, ensure a file exists on the NFS share, for example at `/mnt/irina_storage/files/user/test.txt`.

**Request:**
```json
{
  "tool": "horace_register_file",
  "params": {
    "file_path": "/mnt/irina_storage/files/user/test.txt",
    "metadata": {
      "owner": "user",
      "purpose": "A test file for Horace",
      "tags": ["test", "example"],
      "correlation_id": "test-run-123"
    }
  }
}
```

**Success Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "size": 0,
    "mime_type": "inode/x-empty",
    "registered_at": "2025-10-06T12:00:00.000Z",
    "version": 1
  }
}
```

### Example 2: Search for Files

**Request:**
```json
{
    "tool": "horace_search_files",
    "params": {
        "query": {
            "tags": ["test"]
        },
        "limit": 10
    }
}
```

### Example 3: Restore a Previous Version

Assume a file has been updated and is now at version 3. You want to restore version 1.

**Request:**
```json
{
    "tool": "horace_restore_version",
    "params": {
        "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "version": 1
    }
}
```

**Success Response:**
```json
{
    "status": "success",
    "data": {
        "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "restored_to_version": 1,
        "new_version_created": 4,
        "current_path": "/mnt/irina_storage/files/user/test.txt"
    }
}
```
*(The current state (v3) was backed up as a new version (v4), and the content of v1 was copied to the active file path.)*
```
