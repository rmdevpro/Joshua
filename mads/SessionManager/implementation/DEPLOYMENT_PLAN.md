# SessionManager Deployment Plan - Optimal Hardware Distribution

## Hardware Infrastructure Overview

### Available Machines:
1. **Pharaoh** (Current container host - 192.168.1.X)
   - CPU: 4 cores, 8 threads
   - RAM: 32GB
   - GPU: Quadro P1000 (4GB)
   - Storage: 3.7TB
   - Role: Orchestration, lightweight services

2. **Irina** (192.168.1.210)
   - CPU: 4 cores, 8 threads
   - RAM: 62GB
   - GPU: 2x Tesla P4 (16GB total)
   - Storage: 60TB+ tiered (fast + slow)
   - Role: Production, storage-intensive services

3. **M5** (Training server)
   - CPU: 28 cores
   - RAM: 256GB
   - GPU: V100 + 4xP40 (128GB VRAM)
   - Role: Model training, inference (not for containers)

---

## Optimal Container Distribution Strategy

### IRINA (192.168.1.210) - Heavy/Storage Services
**Why:** More RAM (62GB), massive storage (60TB+), production environment

#### Deploy Here:
1. **SessionManager** (NEW)
   - Redis (in-memory cache)
   - MongoDB (document storage)
   - SessionManager API (3 replicas)
   - Requires: High storage for sessions, RAM for Redis

2. **Dewey** (MIGRATE from Pharaoh)
   - Conversation storage/retrieval
   - PostgreSQL database
   - Requires: Storage for conversation history

3. **Horace** (MIGRATE from Pharaoh)
   - File management gateway
   - NAS integration
   - Requires: Direct access to 60TB storage

4. **Godot** (MIGRATE from Pharaoh)
   - Logger with database backend
   - Requires: Storage for logs

5. **Fiedler** (KEEP/MIGRATE)
   - Multi-model orchestration
   - Benefits from more RAM for model coordination

### PHARAOH (Current location) - Lightweight Services
**Why:** Adequate resources for lightweight MCP services

#### Keep Here:
1. **Gates** (KEEP)
   - Document conversion service
   - Lightweight, low resource usage

2. **Playfair** (KEEP)
   - Diagram generation
   - Lightweight, occasional usage

3. **Marco** (KEEP)
   - Browser automation
   - Moderate resource usage

---

## Migration Plan

### Phase 1: Deploy SessionManager on Irina (NEW)
```bash
# On Irina (192.168.1.210)
cd /mnt/projects/Joshua/mads/SessionManager/implementation
docker-compose up -d redis mongodb sessionmanager-blue
```

### Phase 2: Migrate Heavy Services to Irina
```bash
# Stop services on Pharaoh
docker stop dewey-mcp horace-mcp godot-mcp fiedler-mcp

# Deploy on Irina
docker run -d --name dewey-mcp ... (with Irina configs)
docker run -d --name horace-mcp ...
docker run -d --name godot-mcp ...
docker run -d --name fiedler-mcp ...
```

### Phase 3: Update MCP Relay Configuration
```yaml
# backends.yaml - Update URLs
backends:
  # Services on Irina (192.168.1.210)
  dewey:
    url: ws://192.168.1.210:9022
  horace:
    url: ws://192.168.1.210:9070
  godot:
    url: ws://192.168.1.210:9060
  fiedler:
    url: ws://192.168.1.210:9010

  # Services staying on Pharaoh
  gates:
    url: ws://pharaoh:9050  # Keep current
  playfair:
    url: ws://pharaoh:9040  # Keep current
  marco:
    url: ws://pharaoh:9031  # Keep current
```

---

## Resource Allocation Summary

### Irina Resource Usage (After Migration):
- **RAM Usage**: ~40GB/62GB
  - SessionManager: 3GB (3x 1GB containers)
  - Redis: 8GB
  - MongoDB: 4GB
  - PostgreSQL (Dewey): 4GB
  - Other containers: ~20GB
- **Storage**: Primary usage for databases and file storage
- **GPU**: P4s available for inference if needed

### Pharaoh Resource Usage (After Migration):
- **RAM Usage**: ~10GB/32GB
  - Lightweight MCP services only
  - Plenty of headroom for orchestration
- **Storage**: Minimal usage
- **GPU**: P1000 sufficient for remaining services

---

## Benefits of This Distribution

1. **Better Resource Utilization**
   - Storage-intensive services on machine with 60TB+
   - Memory-intensive services on machine with more RAM
   - Balanced load across both machines

2. **Improved Performance**
   - SessionManager close to its databases
   - File operations direct to Irina's storage
   - Reduced network latency for related services

3. **Scalability**
   - Room to grow on both machines
   - Can add more replicas as needed
   - Clear separation of concerns

4. **Maintainability**
   - Logical grouping of services
   - Easier troubleshooting
   - Clear upgrade path

---

## Implementation Steps

1. **Install Docker on Irina** (if not present)
```bash
ssh aristotle9@192.168.1.210
sudo apt-get update
sudo apt-get install docker.io docker-compose
```

2. **Copy SessionManager code to Irina**
```bash
scp -r /mnt/projects/Joshua/mads/SessionManager aristotle9@192.168.1.210:/home/aristotle9/
```

3. **Deploy SessionManager first** (new service)
4. **Test SessionManager** independently
5. **Migrate services one by one** with testing
6. **Update relay configuration** after each migration
7. **Verify all services** are accessible

---

## Rollback Plan

If issues occur:
1. Services remain running on Pharaoh until migration verified
2. Can quickly update relay URLs back to Pharaoh
3. No data loss - databases can be restored from backups
4. Blue/Green deployment allows instant switching