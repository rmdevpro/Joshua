# Horace - File Storage Gateway

**Version:** 2.0
**Status:** ✅ DEPLOYED - Using iccm-network library v1.1.0
**Deployed:** 2025-10-05

Horace is a file storage gateway that provides a centralized file catalog, automatic versioning, and organization for the ICCM ecosystem. It uses a WebSocket-based MCP (Machine Control Protocol) interface for metadata management and relies on direct NFS/Samba access for file I/O.

## Features

- **7 MCP Tools:** For file registration, search, versioning, and organization.
- **Copy-on-Write Versioning:** Automatically retains the last 5 versions of any file.
- **Centralized Catalog:** All file metadata is stored and indexed in a PostgreSQL database.
- **Secure Pathing:** Validates all file paths to prevent directory traversal attacks.
- **Concurrent Safe:** Uses file locking to prevent race conditions during versioning operations.
- **Dual-Protocol Access:** Designed to work with NFS for Linux containers and Samba/CIFS for Windows clients accessing the same storage backend.

## Prerequisites

1.  **Docker & Docker Compose:** Must be installed on the host machine (Pharaoh).
2.  **NFS Client:** The host machine must have `nfs-common` (or equivalent) installed.
3.  **NFS Server (Irina):** An NFS server must be configured to export the storage directory (e.g., `/mnt/storage/iccm`) to your Docker host's network. See `REQUIREMENTS.md` for an example configuration.
4.  **PostgreSQL Database (Winni):** A running PostgreSQL instance accessible from the Docker host.
5.  **Docker Network:** An external Docker network named `iccm_network` must exist. Create it with `docker network create iccm_network`.

## Deployment Status

**✅ Horace is deployed and operational:**

- **MCP Server:** Running on ws://localhost:9070 (container port 8070)
- **Tools Available:** 7 (horace_register_file, horace_search_files, horace_get_file_info, horace_create_collection, horace_list_collections, horace_update_file, horace_restore_version)
- **Database:** Connected to PostgreSQL on Winni (192.168.1.210)
- **Networking:** Using iccm-network v1.1.0 standard library
- **Logging:** Using standard MCP-based Godot logging (godot/mcp_logger.py)
- **Relay Integration:** Connected to MCP relay, all tools discoverable

## Setup and Deployment

### 1. Configure Environment

Copy the example environment file and fill in your details:

