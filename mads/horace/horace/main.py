# horace/main.py

import asyncio
import os
from pathlib import Path

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from joshua_logger import Logger

import horace.mcp_server as mcp_server
import horace.mcp_websocket_server as mcp_websocket_server
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
logger = Logger()


async def run_snapshot_task(prefix: str):
    """Async wrapper to run snapshot creation."""
    await create_snapshot(ZFS_DATASET, prefix)

async def run_prune_task():
    """Async wrapper to run snapshot pruning."""
    await prune_snapshots(ZFS_DATASET, ZFS_RETENTION)

async def main():
    """Main function to initialize and run all services."""
    await logger.log("INFO", "Starting Horace NAS Gateway v2.1", "horace-main")

    # 1. Initialize Catalog Manager
    catalog = CatalogManager(db_path=DB_PATH, base_path=FILES_PATH)
    await catalog.connect()

    # Make catalog instance available to the web servers
    mcp_server.catalog = catalog
    mcp_websocket_server.catalog = catalog

    # 2. Perform Initial Filesystem Scan (Reconciliation)
    await catalog.reconcile()

    # 3. Initialize Watcher Service
    watcher = WatcherService(catalog_manager=catalog, watch_path=FILES_PATH)

    # 4. Initialize HTTP REST API Server
    config = uvicorn.Config(mcp_server.app, host=API_HOST, port=API_PORT, log_level=LOG_LEVEL.lower())
    http_server = uvicorn.Server(config)

    # 5. Initialize WebSocket MCP Server
    from joshua_network import Server
    websocket_server = Server(
        name="horace",
        version="2.1.0",
        port=9070,
        tool_definitions=mcp_websocket_server.TOOLS,
        tool_handlers=mcp_websocket_server.HANDLERS
    )

    # 6. Initialize ZFS Snapshot Scheduler
    scheduler = AsyncIOScheduler()
    if ENABLE_ZFS_SNAPSHOTS:
        await logger.log("INFO", f"ZFS snapshotting enabled for dataset '{ZFS_DATASET}'", "horace-main")
        scheduler.add_job(run_snapshot_task, CronTrigger(minute=0), args=["hourly"])
        scheduler.add_job(run_snapshot_task, CronTrigger(hour=0, minute=5), args=["daily"])
        scheduler.add_job(run_snapshot_task, CronTrigger(day_of_week='sun', hour=1, minute=5), args=["weekly"])
        scheduler.add_job(run_snapshot_task, CronTrigger(day=1, hour=2, minute=5), args=["monthly"])
        scheduler.add_job(run_prune_task, CronTrigger(hour=3, minute=0)) # Prune daily
        scheduler.start()
    else:
        await logger.log("WARN", "ZFS snapshotting is disabled", "horace-main")

    # Run watcher, HTTP server, and WebSocket MCP server concurrently
    try:
        await asyncio.gather(
            watcher.run(),
            http_server.serve(),
            websocket_server.start()
        )
    except asyncio.CancelledError:
        await logger.log("INFO", "Main task cancelled - shutting down", "horace-main")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await catalog.close()
        await logger.log("INFO", "Horace NAS Gateway shut down gracefully", "horace-main")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Shutdown message logged in main() finally block
