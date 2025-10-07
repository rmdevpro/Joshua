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
