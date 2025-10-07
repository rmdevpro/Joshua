Of course. Here is the revised v2.1 requirements document, incorporating all the feedback from both DeepSeek and GPT-4o. The changes are substantial, particularly regarding the versioning strategy, ZFS configuration, security, and handling of edge cases.

---

# Horace: NAS Gateway Requirements

**Version:** 2.1
**Date:** 2025-10-07
**Status:** REVISED DRAFT

---

## Executive Summary

Horace is the **centralized NAS gateway** for the ICCM ecosystem, providing a file system abstraction backed by ZFS. All services mount `/mnt/irina_storage/files` and treat it as a standard POSIX filesystem. Horace automatically catalogs file changes, provides robust content-based versioning, and leverages periodic ZFS snapshots for disaster recovery. This revision addresses critical feasibility, security, and concurrency issues identified in v2.0.

---

## 1. Core Principles

### 1.1 NAS Gateway Pattern
- **Services write directly** to a shared mount using standard file operations.
- **Horace watches automatically** and catalogs all changes without manual intervention.
- **Transparent to applications** - services do not require special libraries or knowledge of the underlying storage management.

### 1.2 ZFS Backing Store
- **Copy-on-write** provides a robust foundation for data integrity.
- **Periodic Snapshots** for system-wide, point-in-time disaster recovery.
- **Checksums** (SHA-256) for end-to-end data integrity verification.
- **Tiered storage** (cache → SSD → HDD) for future performance scaling.
- **Compression** (lz4) enabled by default to save space.

---

## 2. Architecture

### 2.1 Storage Layout and Security Isolation

To prevent services from accessing or corrupting Horace's internal state, the storage is split into two isolated ZFS datasets.

```
# ZFS Datasets
tank/horace/             # Parent dataset
├── files/               # Mounted by ALL services (read/write)
└── metadata/            # Mounted ONLY by Horace (exclusive access)

# Mount points inside containers
/mnt/irina_storage/
├── files/               # Active file tree
│   ├── fiedler/
│   ├── playfair/
│   └── shared/
└── .horace/             # Horace's private mount point
    ├── catalog.db       # SQLite catalog
    ├── indexes/
    └── log/
```

### 2.2 Versioning Strategy: Catalog-based Versioning + Periodic Snapshots

The infeasible per-write ZFS snapshot strategy is **REPLACED**. The new model uses two complementary systems:

1.  **Catalog-based Versioning (for fine-grained history):**
    - On file modification (`CLOSE_WRITE`), Horace computes the file's SHA-256 checksum.
    - If the checksum is new for that file path, a new version entry is recorded in the SQLite `file_versions` table.
    - This provides a lightweight, efficient history of every saved version of a file without performance degradation.

2.  **Periodic ZFS Snapshots (for disaster recovery):**
    - ZFS snapshots of the `tank/horace/files` dataset are taken automatically on a schedule (e.g., hourly, daily).
    - These are used for system-wide recovery from catastrophic events (e.g., accidental mass deletion, database corruption), not for per-file versioning.

### 2.3 Horace's Role

**File System Watcher:**
- Uses `inotify` (via Python's `watchdog`) to monitor `/mnt/irina_storage/files/`.
- Listens for `CLOSE_WRITE` and `MOVED_TO` events to ensure it only processes complete files.
- Queues events for asynchronous, batched processing to handle high load.

**Catalog Management:**
- On file change, computes SHA-256 checksum.
- Extracts metadata (size, mime-type, owner from path).
- Creates or updates entries in the `files` and `file_versions` tables in SQLite.

**Query Interface (MCP):**
- `horace_search_files` - query the catalog.
- `horace_get_file_info` - get metadata and detailed version history from the catalog.
- `horace_restore_version` - **(Modified)** Restores a specific version by retrieving the content associated with a historical checksum. The primary mechanism for this is out of scope for this document but will likely involve a content-addressable store or searching ZFS snapshots.
- `horace_list_collections` - logical groupings.

---

## 3. ZFS Configuration

### 3.1 Dataset Properties
```bash
# Create parent dataset
zfs create tank/horace

# Create dataset for files shared with services
zfs create -o compression=lz4 \
           -o checksum=sha256 \
           -o atime=off \
           tank/horace/files

# Create isolated dataset for Horace's internal metadata
zfs create -o compression=lz4 \
           -o checksum=sha256 \
           -o atime=off \
           tank/horace/metadata

# DEDUPLICATION IS DISABLED BY DEFAULT
# NOTE: ZFS deduplication requires ~5GB of RAM per 1TB of storage.
# It is set to 'dedup=off' to ensure feasibility on standard hardware.
# Enable it only if the host has sufficient dedicated RAM.
# zfs set dedup=on tank/horace/files
```

### 3.2 Snapshot Schedule
- **Hourly:** Retained for 24 hours.
- **Daily:** Retained for 14 days.
- **Weekly:** Retained for 3 months.
- **Monthly:** Retained for 1 year.

---

## 4. Implementation Requirements

### 4.1 Docker Compose Integration

**Shared ZFS volumes:**
```yaml
volumes:
  irina_storage_files:
    driver: local
    driver_opts:
      type: none
      device: /path/to/zfs/tank/horace/files # Host path
      o: bind
  irina_storage_metadata:
    driver: local
    driver_opts:
      type: none
      device: /path/to/zfs/tank/horace/metadata # Host path
      o: bind
```

**Service volume mounts:**
```yaml
services:
  playfair-mcp:
    user: "1000:1000" # Run as non-root user
    volumes:
      - irina_storage_files:/mnt/irina_storage/files

  horace-mcp:
    user: "1000:1000" # Run as same non-root user
    volumes:
      # Mounts both volumes
      - irina_storage_files:/mnt/irina_storage/files
      - irina_storage_metadata:/mnt/irina_storage/.horace
```

### 4.2 Horace Service Requirements

**Initial Filesystem Scan:**
- On startup, Horace **must** perform a full scan of `/mnt/irina_storage/files` to discover and catalog any files that were created or modified while it was offline, ensuring state consistency.

**Concurrency and Locking:**
- **Atomic Writes:** Services **must** adopt a "write-to-temporary-file-and-rename" pattern. This is an atomic operation that prevents Horace from cataloging partially written or corrupt files.
- **Event Handling:** The file watcher **must** prioritize `CLOSE_WRITE` and `MOVED_TO` events as the trigger for cataloging, ignoring intermediate `MODIFY` events.
- **Advisory Locking:** For files that require true concurrent access (e.g., databases, logs), services should implement their own advisory locking (`flock`). Horace's scope is limited to managing immutable file artifacts.

**Permissions and Ownership:**
- All services, including Horace, **must** run under a common, non-root `uid:gid` (e.g., `1000:1000`).
- The ZFS datasets on the host system **must** be owned by this same `uid:gid` to ensure correct permissions.

**Catalog Schema (Revised):**
```sql
CREATE TABLE files (
    file_id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    current_checksum TEXT, -- FK to file_versions
    created_at TIMESTAMP,
    -- Other metadata: owner, size, mime_type, etc.
);

CREATE TABLE file_versions (
    checksum TEXT PRIMARY KEY, -- SHA-256 of file content
    file_id TEXT NOT NULL,     -- Which file this version belongs to
    size_bytes INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(file_id) REFERENCES files(file_id)
);
```

### 4.3 Handling File System Edge Cases

- **Renames/Moves:** Horace will detect `MOVED_FROM`/`MOVED_TO` events and update the `path` in the `files` table, preserving the `file_id` and its entire version history.
- **Deletions:** On a `DELETE` event, the file's entry in the `files` table will be marked as deleted (e.g., setting `path` to NULL or using a status flag). The version history in `file_versions` is retained. Data remains recoverable from ZFS snapshots.
- **Symbolic & Hard Links:** Symbolic links will be ignored by the watcher. Hard links are unsupported and will result in undefined behavior. The system is designed for regular files and directories only.

---

## 5. Reliability and Error Handling

### 5.1 Recovery Processes
- **Watcher Service Crash:** Upon restart, the "Initial Filesystem Scan" will reconcile any changes missed while the service was down.
- **Catalog Database Corruption:** The `catalog.db` file must be backed up regularly. In a total loss scenario, the catalog can be rebuilt by rescanning the filesystem, but fine-grained version history (checksums and timestamps) will be lost unless recovered from a backup. The file content itself remains safe on ZFS.
- **ZFS Pool Failure:** Recovery from ZFS pool degradation or failure is a standard system administration task and relies on ZFS's built-in redundancy (RAID-Z) and monitoring tools (`zpool status`).

### 5.2 Error Handling
- **I/O Errors:** Services writing to the filesystem are responsible for their own I/O error handling (e.g., disk full, permission denied).
- **Cataloging Failures:** Horace must implement a retry queue for failed cataloging operations and log persistent errors for manual intervention.

---

## 6. Migration Path

### Phase 0: Planning and Validation
- **Backup:** Perform a full backup of all existing data before migration.
- **Test Environment:** Create a staging environment to validate the new architecture and migration scripts.
- **Rollback Plan:** Define clear criteria for a rollback (e.g., data corruption, >10% performance degradation) and document the procedure to revert to the previous system.

### Phase 1: Infrastructure Setup
- Create and configure the `tank/horace/files` and `tank/horace/metadata` ZFS datasets with the correct permissions.
- Deploy the revised Horace service with its new isolated volume mounts.

### Phase 2: Data Migration and Initial Scan
- Copy existing production data into `/path/to/zfs/tank/horace/files`.
- Run the Horace service for the first time to perform the initial filesystem scan and populate the catalog.

### Phase 3: Service Integration
- Incrementally update service `docker-compose.yml` files to mount `irina_storage_files` and write to the new paths.
- Update service code to use the "write-to-temp-and-rename" pattern for all file outputs.
- Remove legacy manual `register_file` calls from service codebases.

---

## 7. Benefits

1.  **Zero-touch cataloging** - Services just write files.
2.  **Automatic file versioning** - Every unique file save is captured via content hashing, providing a complete and efficient history.
3.  **Content verification** - ZFS and application-level checksums provide multiple layers of integrity checks.
4.  **Point-in-time recovery** - ZFS snapshots provide robust disaster recovery for the entire filesystem.
5.  **Efficient storage** - LZ4 compression reduces storage footprint.
6.  **Secure by Design** - Isolation of Horace's metadata prevents tampering by other services.

---

## 8. Example Workflows

### Playfair creates a diagram:
```python
# Playfair writes to a temporary file, then renames it
temp_path = Path("/mnt/irina_storage/files/playfair/temp_diag.svg")
final_path = Path("/mnt/irina_storage/files/playfair/paper_00_quaternary.svg")

temp_path.write_text(svg_content)
temp_path.rename(final_path) # Atomic operation

# Done! Horace detects the 'MOVED_TO' event for final_path and:
# - Computes its checksum
# - Creates a new version entry in the catalog
# - Makes it searchable
```

### User retrieves version history:
```bash
# Via Horace MCP API
horace_get_file_info(path="/mnt/irina_storage/files/playfair/paper_00_quaternary.svg")

# Returns a JSON object with version history from the catalog:
# {
#   "file_id": "...",
#   "path": "...",
#   "versions": [
#     { "checksum": "sha256:abc...", "timestamp": "2025-10-06T10:00:00", "size": 15320 },
#     { "checksum": "sha256:def...", "timestamp": "2025-10-06T11:30:00", "size": 15480 },
#     { "checksum": "sha256:123...", "timestamp": "2025-10-06T15:45:00", "size": 16100 }
#   ]
# }
```
