# Naming Convention Update

## Service Naming Changes

### 1. SessionManager → Rogers
- **Old Name**: SessionManager
- **New Name**: Rogers
- **Purpose**: Session management for forever conversations
- **Location**: Deployed on Irina (192.168.1.210)

### 2. Driver → Imperator (The Thinking Engine)
- **Old Name**: Driver (in triplet consultations)
- **New Name**: Imperator
- **Role**: CENTER OF THE THINKING ENGINE
- **Purpose**: Drives ALL activity in the MAD ecosystem
- **Scope**:
  - Orchestrates triplet consultations
  - Controls MAD workflow execution
  - Makes architectural decisions
  - Coordinates all autonomous development activities
  - Central intelligence that directs the entire system

## Imperator - The Thinking Engine

**Imperator is the brain of the MAD system:**
- **Primary Function**: Central orchestrator for all MAD activities
- **Decision Making**: Determines what tasks need to be done and delegates to appropriate MADs
- **Triplet Leadership**: Leads consultations with Senior and Junior members
- **Workflow Control**: Manages the entire development cycle
- **Architecture Authority**: Makes system-wide architectural decisions
- **MAD Coordination**: Assigns work to specific MADs based on their capabilities

## Updated MAD Architecture

```
        IMPERATOR (Thinking Engine)
              ↓ Commands ↓
    ┌─────────┴─────────────┴──────────┐
    ↓                ↓                  ↓
  Rogers          Dewey              Horace
(Sessions)    (Conversations)    (File Mgmt)
    ↓                ↓                  ↓
  Godot          Fiedler            Gates
(Logging)      (Multi-Model)      (Docs)
    ↓                ↓                  ↓
 Playfair          Marco           [Others]
(Diagrams)       (Browser)
```

## Container Names
- `rogers-blue` (formerly sessionmanager-blue)
- `rogers-green` (formerly sessionmanager-green)
- `rogers-router` (formerly sessionmanager-router)
- `rogers-redis` (formerly sessionmanager-redis)
- `rogers-mongodb` (formerly sessionmanager-mongodb)

## API Endpoints
- `/api/v1/sessions` - Rogers session management API
- `/health` - Rogers health check
- `/metrics` - Rogers metrics endpoint

## Documentation Updates Required
- [ ] Update docker-compose.yml container names
- [ ] Update nginx.conf upstream names
- [ ] Update main.py service identification
- [ ] Update architecture documents
- [ ] Update deployment scripts
- [ ] Update test files
- [ ] Document Imperator's role as Thinking Engine

---

*Last Updated: 2025-10-08*
*Imperator defined as the central Thinking Engine that drives all MAD activity*