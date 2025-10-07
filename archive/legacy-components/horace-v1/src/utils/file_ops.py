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
