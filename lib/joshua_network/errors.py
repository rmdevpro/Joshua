from typing import Any

class ToolError(Exception):
    """
    Custom exception for tool-specific errors.

    Provides standardized error responses following the JSON-RPC 2.0 spec.

    Args:
        message: A human-readable string describing the error.
        code: A number that indicates the error type that occurred.
              Defaults to -32000 for generic server errors.
        data: Optional additional data about the error.
    """
    def __init__(self, message: str, code: int = -32000, data: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

    def to_json_rpc_error(self):
        """Converts the error to a JSON-RPC error format."""
        error = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return error
