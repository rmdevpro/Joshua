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
