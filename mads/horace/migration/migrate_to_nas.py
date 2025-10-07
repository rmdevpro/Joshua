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
