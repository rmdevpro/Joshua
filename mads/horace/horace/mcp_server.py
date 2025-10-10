# horace/mcp_server.py

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from joshua_logger import Logger

from horace.catalog import CatalogManager

logger = Logger()

app = FastAPI(
    title="Horace NAS Gateway MCP",
    description="Provides cataloging, versioning, and search for the Irina Storage.",
    version="2.1.0",
)

# This will be replaced by the actual instance in main.py
catalog: Optional[CatalogManager] = None

@app.on_event("startup")
async def startup_event():
    # In a real app, you might use dependency injection (e.g., FastAPI's Depends)
    # but for simplicity, we use a global-like module variable.
    # The actual instance is created and assigned in main.py
    if catalog is None:
        raise RuntimeError("CatalogManager not initialized. Run through main.py.")
    await catalog.connect()

@app.on_event("shutdown")
async def shutdown_event():
    if catalog:
        await catalog.close()

@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

@app.get("/search", response_model=List[Dict[str, Any]], tags=["Files"])
async def search_files(
    q: str = Query(..., min_length=1, description="Search query for file paths.")
):
    """
    Searches the catalog for files with paths matching the query.
    """
    if not catalog:
        raise HTTPException(status_code=503, detail="Service not initialized")
    results = await catalog.search_files(query=q)
    return results

@app.get("/info", response_model=Dict[str, Any], tags=["Files"])
async def get_file_info(
    path: str = Query(..., description="The relative path to the file within the storage.")
):
    """
    Retrieves detailed metadata and version history for a specific file.
    """
    if not catalog:
        raise HTTPException(status_code=503, detail="Service not initialized")

    info = await catalog.get_file_info(file_path=path)
    if info is None:
        raise HTTPException(status_code=404, detail=f"File not found in catalog: {path}")
    return info

@app.post("/restore_version", tags=["Files"])
async def restore_version(path: str, checksum: str):
    """
    Restores a specific version of a file.

    NOTE: The v2.1 requirements state the primary mechanism for this is out of scope.
    This endpoint serves as a placeholder for a future implementation that would
    search ZFS snapshots or a content-addressable store to retrieve the file
    content associated with the given checksum and write it to the specified path.
    """
    await logger.log(
        "WARN",
        f"Placeholder RESTORE request for path='{path}' with checksum='{checksum}'. "
        "Actual restoration logic is not implemented in this version.",
        "horace-mcp-rest"
    )
    # 1. Validate that the checksum is a known historical version for the path.
    # 2. Search ZFS snapshots for a file with this content hash.
    # 3. If found, copy it to the destination path.
    # 4. The watcher will automatically pick up the change and update the catalog.
    raise HTTPException(
        status_code=501,
        detail="File content restoration from checksum is not implemented. "
               "This is a placeholder for a future feature. "
               "For disaster recovery, use ZFS snapshot restoration."
    )

@app.get("/collections", tags=["Collections"])
async def list_collections():
    """
    (Placeholder) Lists logical collections.

    In this NAS gateway model, collections are simply the top-level directories.
    """
    if not catalog or not catalog.base_path.exists():
        raise HTTPException(status_code=503, detail="Storage path not accessible")

    collections = [
        d.name for d in catalog.base_path.iterdir() if d.is_dir()
    ]
    return {"collections": collections}
