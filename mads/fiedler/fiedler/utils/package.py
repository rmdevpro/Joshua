"""Document package compilation utilities."""
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from .logger import ProgressLogger


def _validate_file_access(file_path: Path) -> None:
    """
    Validate file access against security controls.

    Checks:
    - File is within allowed roots (if FIEDLER_ALLOWED_FILE_ROOTS is set)

    Args:
        file_path: Resolved absolute path to file

    Raises:
        PermissionError: If file is outside allowed roots
    """
    allowed_roots_env = os.getenv("FIEDLER_ALLOWED_FILE_ROOTS")
    if not allowed_roots_env:
        # No allowlist configured - allow all files
        return

    # Parse comma-separated roots
    allowed_roots = [
        Path(root.strip()).expanduser().resolve()
        for root in allowed_roots_env.split(",")
        if root.strip()
    ]

    # Check if file is under any allowed root
    for allowed_root in allowed_roots:
        try:
            file_path.relative_to(allowed_root)
            return  # File is under this allowed root
        except ValueError:
            continue  # Not under this root, try next

    # File not under any allowed root
    raise PermissionError(
        f"File access denied: {file_path} is not under any allowed root. "
        f"Allowed roots: {', '.join(str(r) for r in allowed_roots)}"
    )


def _validate_package_limits(
    num_files: int,
    total_bytes: int,
    total_lines: int
) -> None:
    """
    Validate package size limits.

    Args:
        num_files: Number of files in package
        total_bytes: Total bytes in package
        total_lines: Total lines in package

    Raises:
        ValueError: If any limit is exceeded
    """
    # File count limit
    max_files = int(os.getenv("FIEDLER_MAX_FILE_COUNT", "100"))
    if num_files > max_files:
        raise ValueError(
            f"Package exceeds file count limit: {num_files} > {max_files}. "
            f"Set FIEDLER_MAX_FILE_COUNT to increase."
        )

    # Package size limit (bytes)
    max_bytes = int(os.getenv("FIEDLER_MAX_PACKAGE_BYTES", str(20 * 1024 * 1024)))  # 20MB default
    if total_bytes > max_bytes:
        raise ValueError(
            f"Package exceeds size limit: {total_bytes:,} bytes > {max_bytes:,} bytes ({max_bytes // (1024*1024)}MB). "
            f"Set FIEDLER_MAX_PACKAGE_BYTES to increase."
        )

    # Line count limit
    max_lines = int(os.getenv("FIEDLER_MAX_LINES", "100000"))
    if total_lines > max_lines:
        raise ValueError(
            f"Package exceeds line count limit: {total_lines:,} > {max_lines:,}. "
            f"Set FIEDLER_MAX_LINES to increase."
        )


def compile_package(files: List[str], logger: ProgressLogger) -> Tuple[str, Dict[str, int], List[str]]:
    """
    Compile list of files into a single package string.
    Binary files are separated and returned for attachment handling.

    Args:
        files: List of file paths
        logger: Progress logger

    Returns:
        Tuple of (package_string, metadata_dict, binary_files_list)

    Raises:
        FileNotFoundError: If any file doesn't exist
    """
    if not files:
        logger.log("No files provided")
        return "", {"num_files": 0, "total_size": 0, "total_lines": 0}, []

    # Validate file count limit upfront
    _validate_package_limits(len(files), 0, 0)

    logger.log(f"Compiling package from {len(files)} files...")

    contents = []
    binary_files = []
    total_bytes = 0
    total_lines = 0

    for i, file_path_str in enumerate(files):
        file_path = Path(file_path_str).expanduser().resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Security: Validate file access
        _validate_file_access(file_path)

        logger.log(f"Adding file {i+1}/{len(files)}: {file_path.name}")

        # Try to read as text, skip binary files for attachment handling
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Successfully read as text
            contents.append(f"--- {file_path.name} ---\n{content}")
            total_bytes += len(content.encode("utf-8"))
            total_lines += content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        except UnicodeDecodeError:
            # Binary file - skip text package, add to binary list for multimodal handling
            logger.log(f"📎 Binary file detected, will handle as attachment: {file_path.name}")
            binary_files.append(str(file_path))
            # Don't count binary files in package size limits
            continue

        # Validate limits after each text file
        _validate_package_limits(len(files), total_bytes, total_lines)

    package = "\n\n".join(contents) if contents else ""

    if package:
        logger.log(f"✅ Package compiled: {total_bytes:,} bytes, {total_lines:,} lines")
    if binary_files:
        logger.log(f"📎 {len(binary_files)} binary file(s) for attachment handling")

    return package, {
        "num_files": len(files),
        "total_size": total_bytes,
        "total_lines": total_lines,
        "text_files": len(contents),
        "binary_files": len(binary_files)
    }, binary_files
