# SessionManager Implementation Requirements

**Component:** SessionManager
**Priority:** First component to build (core of system)
**Language:** Python 3.11+
**Framework:** FastAPI (for async REST API)

---

## Functional Requirements

### Core APIs to Implement:

1. **create_session(user_id: str)**
   - Create new session with unique ID
   - Initialize version: 1
   - Store in both Redis (hot) and MongoDB (full)
   - Return session_id

2. **get_session(session_id: str, user_token: str)**
   - Verify RBAC (user owns session or is authorized)
   - Check Redis first (hot cache)
   - If miss, check MongoDB (warm storage)
   - If archived (stub), restore from S3
   - Return session object

3. **update_session(session_id: str, patch: dict, expected_version: int, user_token: str)**
   - Verify RBAC
   - Implement optimistic locking with version check
   - Use Redis WATCH/MULTI/EXEC transaction
   - On success: increment version, update Redis, async write to MongoDB
   - On conflict: raise ConcurrencyConflict

4. **add_participant(session_id: str, mad_name: str)**
   - Add MAD to session.active_mads
   - Create lease key in Redis (30s TTL)
   - Update ACL

5. **suspend_session(session_id: str)**
   - Flush Redis data to MongoDB
   - Set state to "dormant"
   - Clear Redis hot cache

---

## Technical Requirements

### Storage Integration:
- **Redis**: Connection pool, hash operations for partial updates
- **MongoDB**: Async motor driver, atomic operations
- **S3**: Boto3 for archive operations

### Concurrency Control:
```python
# Pseudocode for optimistic locking
async def update_session(session_id, patch, expected_version):
    async with redis.pipeline(transaction=True) as pipe:
        await pipe.watch(f"session_hot:{session_id}")
        current_version = await pipe.hget(f"session_hot:{session_id}", "version")

        if int(current_version) != expected_version:
            raise ConcurrencyConflict()

        pipe.multi()
        pipe.hset(f"session_hot:{session_id}", "version", expected_version + 1)
        pipe.hset(f"session_hot:{session_id}", mapping=patch)
        await pipe.execute()
```

### Session Data Model:
```python
class Session(BaseModel):
    id: str
    version: int
    state: Literal["active", "dormant", "archived"]
    owner_id: str
    acl: List[str]
    created_at: datetime
    last_active: datetime
    participants: Dict
    work_in_progress: Dict
    context_summary: Dict  # Hot - Redis
    recent_timeline: List[Dict]  # Hot - Redis (last 20)
    # full_context and full_timeline in MongoDB only
```

### Deployment:
- Kubernetes Deployment manifest
- 3 replicas minimum
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics` (Prometheus format)
- Environment variables for Redis/MongoDB/S3 connections

---

## Non-Functional Requirements

### Performance:
- Session creation: <100ms
- Hot cache retrieval: <10ms
- Warm retrieval (MongoDB): <200ms
- Cold retrieval (S3): <2s
- Support 1000 concurrent sessions

### Security:
- JWT validation on all endpoints
- RBAC enforcement before any data access
- TLS for all external connections
- No credentials in code (use env vars/secrets)

### Reliability:
- Graceful degradation if Redis unavailable (read-only mode)
- Retry logic for transient failures
- Circuit breaker for external services
- Comprehensive error logging

---

## Testing Requirements

### Unit Tests:
- Mock Redis/MongoDB/S3
- Test optimistic locking conflicts
- Test RBAC enforcement
- Test rehydration flows

### Integration Tests:
- Real Redis/MongoDB in Docker
- Concurrent update scenarios
- Session lifecycle (create → suspend → reactivate)

---

## Deliverables

1. Complete FastAPI application
2. Dockerfile
3. Kubernetes manifests (Deployment, Service, ConfigMap)
4. Unit tests with >80% coverage
5. Integration test suite
6. README with setup instructions

---

## Constraints

- Must strictly follow approved architecture
- No direct database access to MADs
- All operations must be idempotent
- Must handle partial failures gracefully
- Code must be production-ready, not prototype

---

## Success Criteria

- Passes all tests
- Handles concurrent updates correctly
- Scales to 3-5 replicas without issues
- S3 rehydration works end-to-end
- RBAC properly enforced