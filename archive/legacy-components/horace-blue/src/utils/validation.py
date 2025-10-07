# src/utils/validation.py
from pathlib import Path
from ..config import config
from ..exceptions import InvalidPathError

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
