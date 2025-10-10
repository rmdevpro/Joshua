# horace/zfs_ops.py

import asyncio
import subprocess
from datetime import datetime
from typing import List, Optional

from joshua_logger import Logger

logger = Logger()

async def _run_command(command: List[str]) -> Optional[str]:
    """
    Executes a shell command and returns its stdout.
    Logs errors and returns None on failure.
    """
    try:
        await logger.log("DEBUG", f"Executing ZFS command: {' '.join(command)}", "horace-zfs")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        await logger.log("ERROR", f"ZFS command not found: '{command[0]}'. Is ZFS installed and in the system's PATH?", "horace-zfs")
        return None
    except subprocess.CalledProcessError as e:
        await logger.log("ERROR", f"Error executing ZFS command: {' '.join(command)}", "horace-zfs")
        await logger.log("ERROR", f"Return code: {e.returncode}", "horace-zfs")
        await logger.log("ERROR", f"Stderr: {e.stderr.strip()}", "horace-zfs")
        return None

async def create_snapshot(dataset: str, prefix: str) -> Optional[str]:
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

    if await _run_command(command) is not None:
        await logger.log("INFO", f"Successfully created ZFS snapshot: {snapshot_name}", "horace-zfs")
        return snapshot_name
    return None

async def list_snapshots(dataset: str) -> List[str]:
    """
    Lists all snapshots for a given dataset.

    Args:
        dataset: The name of the ZFS dataset.

    Returns:
        A list of snapshot names.
    """
    command = ["zfs", "list", "-t", "snapshot", "-o", "name", "-s", "creation", "-r", dataset]
    output = await _run_command(command)
    if output:
        # First line is the header 'NAME', so we skip it.
        return output.splitlines()[1:]
    return []

async def destroy_snapshot(snapshot_name: str) -> bool:
    """
    Destroys a ZFS snapshot.

    Args:
        snapshot_name: The full name of the snapshot to destroy.

    Returns:
        True on success, False on failure.
    """
    command = ["zfs", "destroy", snapshot_name]
    if await _run_command(command) is not None:
        await logger.log("INFO", f"Successfully destroyed ZFS snapshot: {snapshot_name}", "horace-zfs")
        return True
    return False

async def prune_snapshots(dataset: str, retention_rules: dict):
    """
    Prunes old snapshots based on a retention policy.

    Example retention_rules:
    {
        "hourly": 24, # keep 24 hourly snapshots
        "daily": 14,
    }
    """
    await logger.log("INFO", f"Pruning snapshots for dataset '{dataset}'...", "horace-zfs")
    all_snapshots = await list_snapshots(dataset)

    for prefix, keep_count in retention_rules.items():
        # Filter snapshots matching the current prefix, sorted oldest to newest
        prefix_snapshots = sorted([s for s in all_snapshots if f"@{prefix}-" in s])

        to_delete_count = len(prefix_snapshots) - keep_count
        if to_delete_count > 0:
            await logger.log("INFO", f"Found {len(prefix_snapshots)} '{prefix}' snapshots. "
                        f"Keeping {keep_count}, deleting {to_delete_count}.", "horace-zfs")
            for snapshot in prefix_snapshots[:to_delete_count]:
                await destroy_snapshot(snapshot)
