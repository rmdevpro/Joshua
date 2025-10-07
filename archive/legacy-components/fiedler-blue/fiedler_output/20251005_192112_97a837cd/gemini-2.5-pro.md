## Overall Verdict
**APPROVE WITH MINOR CHANGES**

The Horace requirements are exceptionally well-defined, pragmatic, and perfectly aligned with the stated goals of simplicity and rapid implementation for a personal development environment. The architecture is sound, the scope is tightly controlled, and the technology choices are appropriate for the scale and context. The plan is a textbook example of building the simplest thing that could possibly work, while leaving clear and logical paths for future enhancements.

The proposed changes are minor and aimed at improving API clarity and ensuring the MVP is fully usable.

---

## Section 1: Architecture Decision
**Assessment:** Approve

**Reasoning:** Option A (MCP control + direct NFS) is unequivocally the correct choice for this environment.
-   **Simplicity:** It leverages the OS's mature and highly optimized file handling capabilities. The alternative (streaming files through the MCP) would introduce immense complexity in both the client and server for handling chunking, encoding (base64 is inefficient), and error recovery, all for zero benefit in this context.
-   **Performance:** Direct filesystem access will always be faster than serializing, sending over WebSocket, deserializing, and writing to disk. This is especially true for larger files. Horace remains a lightweight control plane, not a data-plane bottleneck.
-   **Separation of Concerns:** This design correctly separates the role of the catalog (Horace) from the role of the file transport layer (NFS/Samba). This is a clean and maintainable architecture.

**Concerns:** The only minor risk is a race condition or failure where a component writes a file but fails to call `horace_register_file`. However, for a 1-3 developer environment, this is an acceptable risk. The planned manual discovery tool (`REQ-FR-002`) is a perfect and pragmatic mitigation for this.

**Suggestions:** None. This is the right call.

---

## Section 2: Versioning Strategy
**Assessment:** Approve

**Reasoning:** The proposed copy-on-write strategy is ideal.
-   **Implementation Speed:** This is trivial to implement using standard library functions (`shutil.copy2`). It can be coded and tested in hours, not days.
-   **Sufficiency:** For the specified file types (documents, diagrams, text), which are typically small (KB to low MB), the disk space overhead of 5 full copies is negligible on a 44TB array. The value of simple, reliable versioning far outweighs the cost of a few megabytes of storage.
-   **Simplicity:** Restoring a version is just another file copy. Browsing versions is a simple directory listing. There is no complex logic, special format, or external dependency.

**Concerns:** None. More sophisticated approaches like delta storage (Git-style) or ZFS snapshots would be gross over-engineering, violating the core principle of "days not weeks".

**Suggestions:** The "never delete if file was created within last 7 days" safety rule is a nice touch. Consider making this configurable via an environment variable (`HORACE_VERSION_PRUNE_MIN_AGE_DAYS=7`), but it's not critical for Phase 1.

---

## Section 3: Storage Technology
**Assessment:** Approve

**Reasoning:** NFS + Samba is the most pragmatic and direct solution.
-   **Low Overhead:** It uses existing, stable, and well-understood technologies that are likely already running or are trivial to configure on the Irina server. It adds zero new long-running services to maintain, monitor, or debug.
-   **Native Integration:** Docker's NFS volume driver makes mounting the storage into containers seamless. Windows' native support for SMB/CIFS means mapping a network drive is a one-click operation for users.
-   **Fast Implementation:** The setup described in `REQUIREMENTS.md` can be completed in under 30 minutes. An alternative like MinIO would require setting up the service, managing its users/buckets, and, most importantly, refactoring *all client components* (Gates, Playfair, Fiedler) to use an S3 SDK instead of simple filesystem writes. This would blow the timeline out of the water.

**Concerns:** NFS/Samba permissions can sometimes be fiddly. However, the proposed configuration (`no_root_squash` for NFS, `guest ok` for Samba) is a perfect, pragmatic solution for a trusted local network, correctly prioritizing ease-of-use over enterprise-grade security for Phase 1.

**Suggestions:** None. This is the right tool for the job.

---

## Section 4: MCP Tools Design
**Assessment:** Needs Changes

**Reasoning:** The 6 proposed tools are a strong, logical set that covers 95% of the required functionality. The registration, search, and collection management workflows are well-supported.

**Concerns:** There is a missing piece in the user workflow for versioning. While the system *creates* versions automatically and `horace_get_file_info` can *list* them, there is no explicit MCP tool to *restore* a previous version. The pseudocode exists in section 5.3, but it needs to be exposed as a tool. A user shouldn't have to manually `cp` a file from the `.horace_versions` directory.

**Suggestions:** Add a seventh tool for Phase 1:
-   **`horace_restore_version`**
    -   **Description:** Restores a file to a previous version.
    -   **Parameters:**
        ```json
        {
          "file_id": {"type": "string", "required": true},
          "version": {"type": "integer", "required": true}
        }
        ```
    -   **Behavior:** Implements the logic from the `restore_version` pseudocode: creates a new version of the current state, then copies the specified version over the current file.
    -   **Returns:**
        ```json
        {
          "file_id": "uuid",
          "restored_to_version": 2,
          "new_version_created": 4
        }
        ```

This makes the versioning feature complete and user-friendly from the MCP layer.

---

## Section 5: Metadata Schema
**Assessment:** Approve

**Reasoning:** The PostgreSQL schema is excellent. It is clean, normalized, and well-indexed for the specified query patterns.
-   **Scalability:** This schema will perform exceptionally well for the 10K-100K file range. PostgreSQL can handle millions of rows in these tables with the specified indexes without breaking a sweat.
-   **Query Performance:** The GIN index on `tags` is critical and correctly identified. The other B-tree indexes on foreign keys and common filter columns (`owner`, `status`, `created_at`) will ensure that all search operations specified in `horace_search_files` are fast.
-   **Extensibility:** The use of `JSONB` for `metadata` is a smart, pragmatic choice that allows for future flexibility without requiring schema migrations.

**Concerns:** None. This is a production-quality schema for this application's scale.

**Suggestions:** None needed.

---

## Section 6: Phase 1 Scope
**Assessment:** Approve

**Reasoning:** The scope is perfectly calibrated for the "working in days" goal.
-   **High-Value Focus:** The included features solve the core problems identified in the executive summary: network access, organization, search, and versioning.
-   **Ruthless Prioritization:** The list of excluded features is just as important as the included list. Excluding authentication, full-text content search, and an HTTP file serving API are exactly the right cuts to make. Each of those would add significant complexity and development time, pushing the project from "days" to "weeks" or "months".

**Concerns:** None. This is a model of good MVP scoping.

**Suggestions:** Stick to this scope rigorously. The temptation to add "just one more thing" from the Phase 2 list will be the biggest threat to the timeline.

---

## Section 7: Performance Targets
**Assessment:** Approve

**Reasoning:** The performance targets are realistic and achievable with the proposed architecture and specified hardware (spinning disk RAID on a 1Gbps network).
-   **Registration (<500ms for <10MB):** The bottleneck will be the SHA256 checksum calculation, which is I/O bound. Reading 10MB from a local network share and hashing it will be very fast, well within the 500ms budget. The database insert is negligible.
-   **Search (<2s for 100K files):** With proper indexing, PostgreSQL will return these queries in milliseconds, not seconds. The 2-second target is very conservative and easily met.
-   **Versioning (<1s for <10MB):** A file copy over NFS on a local gigabit network will be nearly instantaneous for a 10MB file.

**Concerns:** Performance on very large files (1GB+) will be slower, but the targets are correctly specified for the common case (<100MB). For this environment, slower handling of rare, huge files is an acceptable trade-off.

**Suggestions:** None. The targets are well-reasoned.

---

## Additional Recommendations

1.  **Concurrency:** For 1-3 developers, "last write wins" is perfectly acceptable. Implementing file locking is unnecessary complexity for Phase 1. The automatic versioning already mitigates the most destructive outcome of a race condition (data loss).
2.  **Error Handling:** The approach of failing gracefully and logging verbosely to Godot is consistent with the ICCM ecosystem. This is the correct strategy.
3.  **Health Checks:** A simple `http://localhost:8070/health` endpoint that returns a `200 OK` is sufficient for Docker's health check mechanism and simple monitoring.
4.  **Backup Strategy:** Correctly identify this as an external concern. Horace should not be responsible for backups. This is the responsibility of the Irina host's backup strategy (e.g., filesystem snapshots, `rsync` jobs, etc.).
5.  **Migration Path:** The architecture's decoupling of catalog and storage provides a reasonable migration path. If you move to object storage later, the core change is in the client components and the `file_path` field, which might become an S3 URI. The Horace database and MCP logic would remain largely intact.

---

## Critical Issues

1.  **Missing Restore Functionality:** The lack of a `horace_restore_version` MCP tool is the only critical issue. The versioning feature is incomplete without a simple, programmatic way to restore a file. This tool **must** be added to the Phase 1 scope.
