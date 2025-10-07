# Horace File Storage Gateway - Triplet Review Package

**Date:** 2025-10-05
**Component:** Horace (File Storage Gateway)
**Review Type:** Requirements Approval
**Models:** Fiedler's default triplet

---

## Environmental Context

**CRITICAL: Read this first to calibrate your review**

### Development Environment

- **Team Size:** 1-3 developers (not enterprise team)
- **Deployment:** Single host (Pharaoh) with network storage (Irina)
- **Use Case:** Personal AI research and development tooling
- **Scale:** Thousands of files, not millions
- **Users:** Developers on local network, not public internet
- **Timeline:** Days to implement, not months
- **Maintenance:** Minimal - must be simple and reliable

### NOT Enterprise-Grade (Yet)

This is **Phase 1 MVP** for a personal development environment:

❌ **We are NOT building:**
- Enterprise authentication/authorization (Phase 2)
- Multi-datacenter replication
- 99.99% uptime SLA requirements
- Compliance frameworks (SOC2, HIPAA, etc.)
- Microservices architecture
- Kubernetes orchestration
- Advanced monitoring/alerting

✅ **We ARE building:**
- Simple, functional file catalog for local network
- Good enough reliability (Docker auto-restart is fine)
- Pragmatic solutions (NFS mount vs. object storage)
- Fast time-to-value (working in days, not weeks)
- Easy to understand and maintain
- Room to grow (Phase 2+ for advanced features)

### ICCM Architecture Principles

1. **Simplicity over sophistication** - Working code beats perfect architecture
2. **MCP protocol layer** - All components expose WebSocket MCP tools
3. **PostgreSQL for metadata** - Winni database on Irina (44TB RAID 5)
4. **Docker containers on single host** - Not distributed systems (yet)
5. **Component separation** - Godot (write), Dewey (read), Fiedler (LLM), etc.
6. **Triplet-driven development** - You review, we synthesize, then implement

---

## Review Scope

Please review the Horace requirements document (`REQUIREMENTS.md`) and provide feedback on:

### 1. Architecture Decision: MCP Control Layer vs. File Streaming

**Proposed Approach (Option A):**
- Components write files directly to NFS-mounted storage (`/mnt/irina_storage/`)
- Horace provides **catalog/metadata layer** via MCP tools
- File transfer happens via filesystem (NFS/Samba), NOT through Horace

**Alternative (Option B - Rejected):**
- Components send files to Horace via MCP (base64-encoded)
- Horace writes to storage
- All file I/O flows through Horace

**Question:** Is Option A the right choice for this environment, or should we reconsider Option B?

**Evaluation Criteria:**
- Simplicity of implementation
- Performance for typical workloads (10KB-100MB files)
- Maintainability
- Alignment with ICCM architecture (separation of concerns)

---

### 2. Versioning Strategy: Copy-on-Write vs. Alternatives

**Proposed Approach:**
- When file updated: Copy current file to `.horace_versions/<file_id>.vN`
- Keep last N versions (default: 5, configurable)
- Full file copies, not deltas/diffs
- Automatic pruning when limit exceeded

**Alternative Approaches:**
- Git-style delta storage (more space-efficient, more complex)
- ZFS snapshots (instant, but requires ZFS filesystem)
- Time-based retention (keep daily/weekly/monthly versions)

**Question:** Is simple copy-on-write with fixed version count sufficient, or should we use a more sophisticated approach?

**Evaluation Criteria:**
- Implementation complexity
- Disk space usage (files typically 10KB-100MB)
- Restore speed
- Developer time to implement

---

### 3. Storage Technology: NFS + Samba vs. Object Storage

**Proposed Approach:**
- **NFS v4** for Linux containers (fast, native)
- **Samba/CIFS** for Windows workstations (network drive)
- **Backend:** Irina's existing ext4 filesystem on 44TB RAID 5

**Alternative:**
- **MinIO** (S3-compatible object storage)
- Unified API for all clients
- Versioning built-in
- More "modern" architecture

**Question:** Is NFS+Samba the right choice for a single-host environment with network storage, or should we use object storage?

**Evaluation Criteria:**
- Setup complexity (time to get working)
- Performance for local network access
- Windows compatibility
- Operational overhead (what breaks, how do we fix it)

---

### 4. MCP Tools Design: 6 Tools Sufficient?

**Proposed Tools:**
1. `horace_register_file` - Register file with metadata
2. `horace_search_files` - Search by tags, owner, date, type, size
3. `horace_get_file_info` - Get metadata + version history
4. `horace_create_collection` - Group files into named collections
5. `horace_list_collections` - Browse collections
6. `horace_update_file` - Update metadata or trigger versioning

**Question:** Are these 6 tools the right set for Phase 1, or are we missing critical operations?

**Considerations:**
- Gates will write ODT documents and register them
- Playfair will write diagrams and register them
- Fiedler will write LLM outputs and register them
- Users will search for files by tags/purpose
- Users will view version history and restore

---

### 5. Metadata Schema: PostgreSQL Tables

**Proposed Schema:**
- `horace_files` table (id, path, owner, tags, checksum, version, metadata JSONB)
- `horace_versions` table (file_id, version, checksum, path, timestamp)
- `horace_collections` table (id, name, description, metadata JSONB)

**Indexes:**
- GIN index on `tags` array (full-text search on tags)
- B-tree on `owner`, `created_at`, `checksum`

**Question:** Is this schema sufficient for 10,000-100,000 files with fast search (<2s)?

**Considerations:**
- Typical queries: "Find all Gates documents from last week"
- Typical queries: "Find files tagged with 'paper' AND 'v3'"
- Typical queries: "Show me all versions of this file"

---

### 6. Phase 1 Scope: Too Much or Too Little?

**Included in Phase 1:**
✅ File registration and cataloging
✅ Automatic versioning (last 5 versions)
✅ Metadata search (tags, owner, date, type, size)
✅ Collections (grouping related files)
✅ NFS + Samba dual-protocol access
✅ PostgreSQL metadata storage
✅ Component integration (Gates, Playfair, Fiedler)

**Explicitly Excluded (Phase 2):**
❌ Authentication/authorization
❌ HTTP file serving/download API
❌ Full-text content search (search inside documents)
❌ Advanced retention policies (time-based deletion)
❌ File preview generation (thumbnails)
❌ Scheduled scans/indexing

**Question:** Is Phase 1 scope appropriate for "get it working in days" goal, or should we add/remove features?

---

### 7. Performance Targets: Realistic?

**Proposed Targets:**
- File registration: <500ms for files <10MB
- Search: <2s for 10,000+ files
- Version creation: <1s for files <10MB
- Version restoration: <2s

**Environment:**
- Network: 1 Gbps local network (Pharaoh ↔ Irina)
- Storage: 44TB RAID 5 (spinning disks, not SSD)
- Database: PostgreSQL on same Irina server

**Question:** Are these targets achievable with proposed architecture, or should we adjust expectations?

---

## Specific Questions for You

For each of the above sections, please provide:

1. **Overall Assessment:** Approve / Needs Changes / Reject
2. **Reasoning:** Why this approach works or doesn't work for this environment
3. **Concerns:** Any risks or gotchas we should address
4. **Suggestions:** Specific improvements (keep in mind: simplicity, fast implementation)

### Additional Open Questions

1. **Concurrency:** Do we need file locking in Phase 1, or is "last write wins" acceptable for 1-3 developers?

2. **Error Handling:** Should Horace fail gracefully and log errors, or fail loudly to alert developers immediately?

3. **Health Checks:** Is a simple HTTP `/health` endpoint sufficient, or do we need more sophisticated monitoring?

4. **Backup Strategy:** Should Horace handle backups, or is that the responsibility of the filesystem/RAID layer?

5. **Migration Path:** If we outgrow NFS in Phase 2+, is it easy to migrate to object storage without breaking clients?

---

## Success Criteria

Phase 1 is successful if:

✅ All ICCM components (Gates, Playfair, Fiedler) write files to Horace-managed storage
✅ Developers can search for files via MCP tools
✅ Versioning prevents accidental overwrites (last 5 versions retained)
✅ Windows workstations can access files via network drive
✅ Implementation takes <1 week (not months)
✅ System is maintainable by 1-3 developers without enterprise ops team

---

## Review Format

Please structure your response as:

```
## Overall Verdict
[APPROVE / NEEDS CHANGES / REJECT]

## Section 1: Architecture Decision
[Your assessment]

## Section 2: Versioning Strategy
[Your assessment]

## Section 3: Storage Technology
[Your assessment]

## Section 4: MCP Tools Design
[Your assessment]

## Section 5: Metadata Schema
[Your assessment]

## Section 6: Phase 1 Scope
[Your assessment]

## Section 7: Performance Targets
[Your assessment]

## Additional Recommendations
[Any other feedback]

## Critical Issues
[Anything that MUST be addressed before implementation]
```

---

## Context: Similar ICCM Components

For reference, here are similar components in ICCM:

**Godot (Logging):**
- Architecture: Write specialist, all logs flow through Godot → PostgreSQL
- Complexity: Medium (Redis queue + worker + MCP server)
- Implementation time: ~1 week (with triplet review)
- Success: ✅ Working reliably

**Dewey (Conversation Storage):**
- Architecture: Read specialist, query-only access to PostgreSQL
- Complexity: Low (async PostgreSQL client + MCP server)
- Implementation time: ~3 days
- Success: ✅ Working reliably

**Gates (Document Generation):**
- Architecture: WebSocket MCP server + LibreOffice headless
- Complexity: Medium (Markdown parsing + Playfair integration)
- Implementation time: ~2 hours (estimated 4 weeks by triplets, actual: <4 hours)
- Success: ✅ Working reliably

**Playfair (Diagram Generation):**
- Architecture: WebSocket MCP server + Graphviz + Mermaid
- Complexity: Medium (rendering engines + theming)
- Implementation time: ~1 day
- Success: ✅ Working reliably

**Pattern:** Simple, focused components with clear responsibilities, implemented quickly, working reliably.

---

## Files to Review

1. **REQUIREMENTS.md** (main document, ~19,000 words)
   - Full technical specification
   - All 6 MCP tools detailed
   - Storage strategy explained
   - Phase 1 scope clearly defined

This review package provides the focused questions and context for your evaluation.

Thank you for your review!
