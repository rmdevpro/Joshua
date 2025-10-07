# Horace NAS Gateway v2.1

**Status**: ✅ **DEPLOYED** - WebSocket MCP server active on port 9070

**Recent Updates (2025-10-07)**:
- Added WebSocket MCP server using iccm-network library
- Provides MCP tools on port 9070 alongside HTTP REST API on port 8000
- Fixed PostgreSQL authentication (database: horace, correct credentials)
- Relay successfully connected and tools verified working

## Overview

Horace NAS Gateway is a ZFS-backed file versioning and cataloging system. Services write directly to a shared POSIX filesystem mount, and Horace automatically catalogs all changes with SHA-256 checksums.

## Key Features

- **Transparent NAS Gateway**: Services see a normal POSIX filesystem
- **Automatic Versioning**: Catalog-based versioning with SHA-256 checksums
- **Periodic ZFS Snapshots**: Hourly, daily, weekly, monthly (configurable)
- **Fast Search**: SQLite catalog with indexed file paths
- **Version History**: Complete history with checksums and timestamps
- **Atomic Writes**: Handles temp-file-and-rename pattern
- **Initial Reconciliation**: Full filesystem scan on startup

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Playfair   │  │    Gates    │  │   Other     │
│     MCP     │  │     MCP     │  │  Services   │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
            ┌───────────▼───────────┐
            │   Shared ZFS Volume   │
            │  /mnt/irina_storage/  │
            │        files/         │
            └───────────┬───────────┘
                        │
              ┌─────────▼─────────┐
              │   Horace Watcher  │
              │   (inotify/       │
              │    watchdog)      │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │  Catalog Manager  │
              │   (SQLite + WAL)  │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │   ZFS Snapshots   │
              │  (periodic cron)  │
              └───────────────────┘
```

## Implementation Status

### ✅ Code Complete
- [x] catalog.py - File versioning and SQLite catalog
- [x] watcher.py - Filesystem event monitoring
- [x] zfs_ops.py - ZFS snapshot operations
- [x] mcp_server.py - FastAPI REST endpoints
- [x] main.py - Service orchestration
- [x] Dockerfile - Production container image
- [x] docker-compose.yml - Multi-service deployment
- [x] migration/migrate_to_nas.py - Migration tool

### 📋 Review Status
- **Requirements v2.1**: Unanimous approval (DeepSeek-R1 + GPT-4o)
  - Round 1: NEEDS REVISION (per-write snapshots, deduplication issues)
  - Round 2: APPROVED (catalog versioning + periodic snapshots)
- **Code Implementation Round 1**: Unanimous approval (DeepSeek-R1 + GPT-4o)
  - Both reviewers: APPROVED with minor non-blocking recommendations

### 🚀 Next Steps
1. Set up ZFS datasets (see below)
2. Build and test the implementation
3. Run migration if needed
4. Deploy to production

---

## Usage Patterns

### For Ecosystem Components (Internal)

**Components write directly to the shared filesystem:**

```python
from pathlib import Path

# Playfair writing a diagram
output_path = Path("/mnt/irina_storage/files/playfair/diagram.svg")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(svg_content)
# Done! Horace automatically catalogs this file

# Fiedler writing LLM outputs
output_dir = Path("/mnt/irina_storage/files/temp/fiedler")
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "response.md").write_text(response)
# Automatically versioned and cataloged

# Gates creating documents
doc_path = Path("/mnt/irina_storage/files/gates/output.odt")
doc_path.parent.mkdir(parents=True, exist_ok=True)
doc_path.write_bytes(odt_bytes)
# Tracked by Horace with checksum verification
```

**Best practices for components:**
1. Use the **write-to-temp-and-rename pattern** for atomic writes:
   ```python
   temp_path = output_path.with_suffix('.tmp')
   temp_path.write_text(content)
   temp_path.rename(output_path)  # Atomic operation
   ```
2. Create subdirectories under `/mnt/irina_storage/files/` for your component
3. No need to call `horace_register_file` - Horace watches automatically
4. Use `/mnt/irina_storage/files/temp/` for temporary/transient outputs
5. Horace catalogs `CLOSE_WRITE` and `MOVED_TO` events - ignore intermediate writes

### For External Users (Claude Code, Scripts, etc.)

**Access the filesystem via SSHFS mount:**

```bash
# One-time setup: Mount the ZFS filesystem locally
sudo mkdir -p /mnt/irina_storage
echo "password" | sudo -S sshfs -o password_stdin,allow_other,default_permissions \
    user@server:/mnt/irina_storage /mnt/irina_storage

# Now read/write files directly
echo "test" > /mnt/irina_storage/files/test.txt

# Read component outputs
ls -la /mnt/irina_storage/files/temp/fiedler/
cat /mnt/irina_storage/files/playfair/diagram.svg

# Write input files for components
cp my_document.md /mnt/irina_storage/files/input/
```

**Claude Code usage:**
```python
from pathlib import Path

# Read Fiedler output
fiedler_output = Path("/mnt/irina_storage/files/temp/fiedler/20251007_123456/response.md")
content = fiedler_output.read_text()

# Write input for Playfair
diagram_spec = Path("/mnt/irina_storage/files/input/diagram.dot")
diagram_spec.write_text(dot_content)

# All files automatically cataloged by Horace
```

**MCP Tool Access:**
```python
# Search for files via Horace MCP
mcp__iccm__horace_search_files(file_type="svg")

# Get file info and version history
mcp__iccm__horace_get_file_info(path="playfair/diagram.svg")

# List collections (top-level directories)
mcp__iccm__horace_list_collections()
```

**File Organization:**
- `/mnt/irina_storage/files/temp/` - Temporary outputs from components
- `/mnt/irina_storage/files/input/` - Input files for processing
- `/mnt/irina_storage/files/{component}/` - Component-specific directories
- `/mnt/irina_storage/files/fiedler/` - Fiedler LLM outputs
- `/mnt/irina_storage/files/playfair/` - Playfair diagrams
- `/mnt/irina_storage/files/gates/` - Gates documents
- `/mnt/irina_storage/files/shared/` - Shared workspace

**External mount instructions:**
See CLAUDE.md for the full SSHFS mount command and troubleshooting.

---

## Quick Start

### Prerequisites
- ZFS installed on host (`sudo apt install zfsutils-linux`)
- Docker and Docker Compose
- A ZFS pool (e.g., `tank`)

### 1. Create ZFS Datasets
```bash
# Create parent dataset
sudo zfs create tank/horace

# Create files dataset (shared with all services)
sudo zfs create -o compression=lz4 \
                -o checksum=sha256 \
                -o atime=off \
                -o dedup=off \
                -o mountpoint=/mnt/tank/horace/files \
                tank/horace/files

# Create metadata dataset (private to Horace)
sudo zfs create -o compression=lz4 \
                -o atime=off \
                -o mountpoint=/mnt/tank/horace/metadata \
                tank/horace/metadata

# Set ownership (UID/GID 1000 matches Docker container user)
sudo chown -R 1000:1000 /mnt/tank/horace/files
sudo chown -R 1000:1000 /mnt/tank/horace/metadata

# Verify
ls -ld /mnt/tank/horace/*
```

### 2. Update docker-compose.yml
Edit the volume device paths in `docker-compose.yml` to match your ZFS mountpoints:
```yaml
volumes:
  irina_storage_files:
    driver: local
    driver_opts:
      type: none
      device: /mnt/tank/horace/files  # <-- Your path here
      o: bind

  irina_storage_metadata:
    driver: local
    driver_opts:
      type: none
      device: /mnt/tank/horace/metadata  # <-- Your path here
      o: bind
```

### 3. Build and Run
```bash
# Build the container
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f horace-mcp

# Test health endpoint
curl http://localhost:8000/health
```

## API Endpoints

### GET /health
Health check endpoint.

### GET /search?q={query}
Search for files by path.
```bash
curl "http://localhost:8000/search?q=test"
```

### GET /info?path={relative_path}
Get file info and version history.
```bash
curl "http://localhost:8000/info?path=playfair/diagram.svg"
```

### GET /collections
List top-level directories.
```bash
curl http://localhost:8000/collections
```

### POST /restore_version
Placeholder for version restoration (not implemented in v2.1).

## Configuration

Environment variables in `docker-compose.yml`:
- `HORACE_FILES_PATH`: Base path for files (default: `/mnt/irina_storage/files`)
- `HORACE_METADATA_PATH`: Path for metadata (default: `/mnt/irina_storage/.horace`)
- `ENABLE_ZFS_SNAPSHOTS`: Enable/disable snapshots (default: `true`)
- `ZFS_DATASET`: ZFS dataset to snapshot (default: `tank/horace/files`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## ZFS Snapshot Schedule

When `ENABLE_ZFS_SNAPSHOTS=true`:
- **Hourly**: Every hour, keep 24 (1 day)
- **Daily**: 00:05, keep 14 (2 weeks)
- **Weekly**: Sunday 01:05, keep 12 (~3 months)
- **Monthly**: 1st day 02:05, keep 12 (1 year)
- **Pruning**: Daily at 03:00

### Security Note
For production, consider disabling Docker-based snapshots (`ENABLE_ZFS_SNAPSHOTS=false`) and using host-based cron jobs instead to avoid giving containers elevated privileges.

## Migration

Use the migration script to move from legacy Horace:
```bash
python migration/migrate_to_nas.py /path/to/legacy/data \
    --files-dataset tank/horace/files \
    --metadata-dataset tank/horace/metadata \
    --uid 1000 \
    --gid 1000
```

The script guides through:
1. Planning and validation
2. ZFS infrastructure setup
3. Data migration and initial scan
4. Service integration

## Monitoring

```bash
# View logs
docker-compose logs -f horace-mcp

# Check catalog database
docker exec -it horace-nas-v2-horace-mcp-1 sqlite3 /mnt/irina_storage/.horace/catalog.db
sqlite> SELECT COUNT(*) FROM files WHERE is_deleted = 0;

# List ZFS snapshots
sudo zfs list -t snapshot -r tank/horace/files
```

## Troubleshooting

### Watcher not detecting changes
- Check file ownership matches container UID/GID (1000:1000)
- Verify `.horace` directory is not in the watched path
- Check logs for errors: `docker-compose logs horace-mcp`

### ZFS snapshots not working
- Ensure `zfs` command is available in container
- Check `ENABLE_ZFS_SNAPSHOTS` environment variable
- Review security implications of container ZFS access
- Consider host-based cron as alternative

### Initial reconciliation slow
- Normal for large datasets (batched processing)
- Monitor progress in logs
- One-time operation on startup

## Development

### Running tests
```bash
# Install dev dependencies
pip install -r requirements.txt

# Run integration tests (TODO)
pytest tests/
```

### Code structure
```
horace-nas-v2/
├── horace/
│   ├── __init__.py
│   ├── catalog.py      # Database and versioning
│   ├── watcher.py      # Filesystem monitoring
│   ├── zfs_ops.py      # ZFS operations
│   ├── mcp_server.py   # REST API
│   └── main.py         # Service entry point
├── migration/
│   └── migrate_to_nas.py  # Migration tool
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## References

- [Requirements v2.1](../architecture/horace_nas_gateway_requirements_v2.1.md)
- [Implementation Round 1](nas_gateway_impl_round1/implementation.md)
- [DeepSeek Review](../fiedler-blue/fiedler_output/20251006_195353_23257290/deepseek-ai_DeepSeek-R1.md)
- [GPT-4o Review](../fiedler-blue/fiedler_output/20251006_195353_23257290/gpt-4o.md)

## License

Part of the ICCM project.
