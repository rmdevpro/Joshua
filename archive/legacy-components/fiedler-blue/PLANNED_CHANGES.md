# Fiedler Planned Changes

## Change 1: Direct Filesystem Access

**Problem:**
Current design requires copying files to `/mnt/projects/ICCM/fiedler/allowed_files/` and translating paths from host format (`/mnt/projects/...`) to container format (`/app/allowed_files/...`). This creates friction for every use.

**Solution:**
Mount `/mnt/projects` directly into the container with read-only access.

**Implementation:**

### docker-compose.yml
```yaml
services:
  fiedler-mcp:
    volumes:
      # Add this line
      - /mnt/projects:/mnt/projects:ro

      # Keep existing volumes
      - ./allowed_files:/app/allowed_files:ro
      - fiedler_output:/app/fiedler_output
      - fiedler_state:/root/.fiedler
```

### Environment Variable
Update `FIEDLER_ALLOWED_FILE_ROOTS` in docker-compose.yml or .env:
```yaml
environment:
  FIEDLER_ALLOWED_FILE_ROOTS: /app/allowed_files,/app/fiedler_output,/mnt/projects
```

**Benefits:**
- No file copying required
- Use actual host paths in Fiedler calls
- Simpler workflow for development/research use
- Still read-only (can't accidentally modify files)

**Trade-offs:**
- Less security isolation (acceptable for single-user research environment)
- Larger attack surface if Fiedler were compromised (deferred concern)

**Testing:**
1. Apply changes to docker-compose.yml
2. Restart container: `docker-compose restart fiedler-mcp`
3. Test: Send request with `/mnt/projects/ICCM/docs/papers/01_*.md`
4. Verify file is accessible without copying

---

## Change 2: Progress/Status Querying

**Problem:**
When Fiedler sends requests to multiple LLMs in parallel, there's no way to check:
- Which models are still running
- How long each has been running
- Which have finished
- What the current status is

The old `triplet_verifier.py` had a ProgressLogger that showed real-time status for each model. Fiedler needs the same capability.

**Solution:**
Add job tracking and a new MCP tool to query progress.

**Implementation:**

### 1. Job State Management

Create `fiedler/utils/jobs.py`:
```python
"""Job tracking for in-progress LLM requests."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ModelJobStatus:
    model: str
    status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    elapsed_seconds: Optional[float]
    error: Optional[str]
    output_file: Optional[str]
    tokens_used: Optional[int]

@dataclass
class FiedlerJob:
    job_id: str
    correlation_id: str
    started_at: datetime
    prompt_summary: str  # First 100 chars
    models: List[str]
    model_statuses: Dict[str, ModelJobStatus]
    total_elapsed_seconds: float
    completed_count: int
    failed_count: int
    pending_count: int

# Global job registry
_active_jobs: Dict[str, FiedlerJob] = {}

def register_job(job: FiedlerJob):
    """Register a new job for tracking."""
    _active_jobs[job.job_id] = job

def update_model_status(job_id: str, model: str, status: ModelJobStatus):
    """Update status for a specific model in a job."""
    if job_id in _active_jobs:
        _active_jobs[job_id].model_statuses[model] = status

def get_job(job_id: str) -> Optional[FiedlerJob]:
    """Get job by ID."""
    return _active_jobs.get(job_id)

def list_active_jobs() -> List[FiedlerJob]:
    """List all jobs (active and completed in last hour)."""
    return list(_active_jobs.values())

def cleanup_old_jobs():
    """Remove jobs older than 1 hour."""
    # Implementation
    pass
```

### 2. Update fiedler_send to Track Progress

Modify `fiedler/tools/send.py`:
```python
def fiedler_send(prompt: str, files: Optional[List[str]] = None, models: Optional[List[str]] = None):
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{correlation_id[:8]}"

    # Register job
    job = FiedlerJob(
        job_id=job_id,
        correlation_id=correlation_id,
        started_at=datetime.now(),
        prompt_summary=prompt[:100],
        models=resolved_models,
        model_statuses={m: ModelJobStatus(m, JobStatus.QUEUED, None, None, None, None, None, None) for m in resolved_models},
        total_elapsed_seconds=0,
        completed_count=0,
        failed_count=0,
        pending_count=len(resolved_models)
    )
    register_job(job)

    # Update status as models run
    # ... in provider execution ...
    update_model_status(job_id, model_name, ModelJobStatus(
        model=model_name,
        status=JobStatus.RUNNING,
        started_at=datetime.now(),
        ...
    ))

    # Return job_id in response
    return {
        "status": "success",
        "job_id": job_id,
        "correlation_id": correlation_id,
        ...
    }
```

### 3. New MCP Tool: fiedler_get_status

Create `fiedler/tools/status.py`:
```python
"""Status and progress tracking tools."""

from typing import Optional, Dict, Any
from ..utils.jobs import get_job, list_active_jobs

def fiedler_get_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get status of Fiedler jobs.

    Args:
        job_id: Optional job ID. If None, lists all recent jobs.

    Returns:
        Job status information
    """
    if job_id:
        job = get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        return {
            "job_id": job.job_id,
            "correlation_id": job.correlation_id,
            "started_at": job.started_at.isoformat(),
            "elapsed_seconds": job.total_elapsed_seconds,
            "prompt": job.prompt_summary,
            "models": {
                model: {
                    "status": status.status.value,
                    "started_at": status.started_at.isoformat() if status.started_at else None,
                    "completed_at": status.completed_at.isoformat() if status.completed_at else None,
                    "elapsed_seconds": status.elapsed_seconds,
                    "error": status.error,
                    "output_file": status.output_file,
                    "tokens_used": status.tokens_used
                }
                for model, status in job.model_statuses.items()
            },
            "summary": {
                "completed": job.completed_count,
                "failed": job.failed_count,
                "pending": job.pending_count
            }
        }
    else:
        # List all recent jobs
        jobs = list_active_jobs()
        return {
            "total_jobs": len(jobs),
            "jobs": [
                {
                    "job_id": j.job_id,
                    "started_at": j.started_at.isoformat(),
                    "elapsed_seconds": j.total_elapsed_seconds,
                    "completed": j.completed_count,
                    "failed": j.failed_count,
                    "pending": j.pending_count,
                    "models": list(j.model_statuses.keys())
                }
                for j in jobs
            ]
        }
```

### 4. Register New Tool in MCP Server

Update `fiedler/server.py` to add tool definition:
```python
{
    "name": "fiedler_get_status",
    "description": "Get status of in-progress or recent Fiedler jobs",
    "inputSchema": {
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "Optional job ID to get detailed status. If omitted, lists all recent jobs."
            }
        }
    }
}
```

**Usage Examples:**

```python
# After sending a request
result = fiedler_send(prompt="...", files=["..."], models=["gemini-2.5-pro", "gpt-5", "grok-4"])
job_id = result["job_id"]

# Check progress
status = fiedler_get_status(job_id)
# {
#   "job_id": "job_20251002_100500_a1b2c3d4",
#   "elapsed_seconds": 45.2,
#   "models": {
#     "gemini-2.5-pro": {"status": "completed", "elapsed_seconds": 32.1, ...},
#     "gpt-5": {"status": "running", "elapsed_seconds": 45.2, ...},
#     "grok-4": {"status": "queued", ...}
#   },
#   "summary": {"completed": 1, "failed": 0, "pending": 2}
# }

# List all jobs
all_jobs = fiedler_get_status()
# {
#   "total_jobs": 3,
#   "jobs": [
#     {"job_id": "...", "completed": 3, "pending": 0, ...},
#     {"job_id": "...", "completed": 1, "pending": 2, ...}
#   ]
# }
```

**Benefits:**
- Real-time visibility into LLM processing
- Can check long-running jobs without blocking
- Matches functionality of old triplet_verifier.py
- Helpful for debugging slow/stuck models
- User can decide whether to wait or move on

**Testing:**
1. Send a multi-model request
2. Immediately call `fiedler_get_status(job_id)` to see "running" status
3. Poll every 5-10 seconds to watch progress
4. Verify completion status shows timing/output info

---

## Implementation Priority

1. **Change 1 (Direct Filesystem)** - High priority, immediate friction reduction
2. **Change 2 (Progress Querying)** - Medium priority, quality-of-life improvement

## Rollout Plan

1. Implement Change 1 first (simpler, immediate value)
2. Test thoroughly with current architecture work
3. Implement Change 2 after validating new workflow
4. Consider adding both to a v1.1 release

## Security Notes

**Change 1:** Acceptable risk for single-user research environment. Can be reverted later if Fiedler is deployed in multi-user or exposed context.

**Change 2:** No security implications, purely additive feature.

---

## Change 3: Performance Tracking Database

**Problem:**
Fiedler currently has no way to:
- Track LLM performance over time
- Compare model quality across jobs
- Analyze cost/speed/quality trade-offs
- Review and rate output quality
- Build historical performance data

Traditional logging to files doesn't support:
- Structured queries (e.g., "show me all Gemini jobs from last week")
- Aggregations (e.g., "average response time by model")
- Relational data (e.g., "jobs that used multiple models")
- Quality ratings and reviews

**Solution:**
Add SQLite database for structured performance tracking and quality reviews.

**Why SQLite:**
- Embedded (no separate server)
- ACID compliant (reliable)
- Full SQL support (powerful queries)
- Easy migration path to PostgreSQL later
- Python stdlib support (no new dependencies)
- Single file (~5MB typical size)

**Database Schema:**

### Table: models
```sql
CREATE TABLE models (
    model_id TEXT PRIMARY KEY,           -- "gemini-2.5-pro", "gpt-5", etc.
    provider TEXT NOT NULL,              -- "google", "openai", "together", "xai"
    display_name TEXT,                   -- "Gemini 2.5 Pro"
    max_tokens INTEGER,                  -- Context window size
    cost_per_million_input REAL,         -- Input token cost
    cost_per_million_output REAL,        -- Output token cost
    capabilities TEXT,                   -- JSON: ["text", "vision", "function_calling"]
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    total_jobs_completed INTEGER DEFAULT 0,
    notes TEXT
);
```

### Table: jobs
```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    prompt_summary TEXT,                 -- First 200 chars of prompt
    prompt_tokens INTEGER,               -- Estimated input size
    num_files INTEGER,                   -- Files in package
    package_size_bytes INTEGER,          -- Total package size
    models_requested TEXT,               -- JSON array: ["gemini-2.5-pro", "gpt-5"]
    output_dir TEXT,
    status TEXT,                         -- "running", "completed", "partial", "failed"
    total_elapsed_seconds REAL,
    notes TEXT
);
```

### Table: model_executions
```sql
CREATE TABLE model_executions (
    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    elapsed_seconds REAL,
    status TEXT,                         -- "completed", "failed", "timeout"

    -- Token usage
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Cost
    input_cost REAL,                     -- Calculated cost for input
    output_cost REAL,                    -- Calculated cost for output
    total_cost REAL,

    -- Output
    output_file TEXT,                    -- Path to output markdown
    output_size_bytes INTEGER,
    output_line_count INTEGER,

    -- Error info
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);
```

### Table: quality_reviews
```sql
CREATE TABLE quality_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewer TEXT,                       -- "user" or specific username

    -- Quality dimensions (1-10 scale)
    accuracy REAL,                       -- Correctness of information
    completeness REAL,                   -- Addressed all requirements
    clarity REAL,                        -- Clear, well-organized output
    depth REAL,                          -- Level of detail/analysis
    usefulness REAL,                     -- Practical value

    -- Overall rating
    overall_rating REAL,                 -- Average or weighted score

    -- Qualitative feedback
    strengths TEXT,                      -- What was good
    weaknesses TEXT,                     -- What was lacking
    notes TEXT,                          -- General observations

    FOREIGN KEY (execution_id) REFERENCES model_executions(execution_id)
);
```

### Table: performance_metrics (View)
```sql
CREATE VIEW performance_metrics AS
SELECT
    m.model_id,
    m.provider,
    m.display_name,
    COUNT(e.execution_id) as total_executions,
    SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
    ROUND(AVG(e.elapsed_seconds), 2) as avg_elapsed_seconds,
    ROUND(AVG(e.total_tokens), 0) as avg_total_tokens,
    ROUND(SUM(e.total_cost), 2) as total_cost,
    ROUND(AVG(r.overall_rating), 2) as avg_quality_rating,
    ROUND(AVG(r.accuracy), 2) as avg_accuracy,
    ROUND(AVG(r.completeness), 2) as avg_completeness,
    ROUND(AVG(r.usefulness), 2) as avg_usefulness,
    MAX(e.completed_at) as last_used_at
FROM models m
LEFT JOIN model_executions e ON m.model_id = e.model_id
LEFT JOIN quality_reviews r ON e.execution_id = r.execution_id
GROUP BY m.model_id;
```

**Implementation:**

### 1. Database Manager Module

Create `fiedler/db/__init__.py`:
```python
"""Database management for Fiedler performance tracking."""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

DB_PATH = Path.home() / ".fiedler" / "fiedler.db"

def init_db():
    """Initialize database with schema."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Execute schema creation (SQL from above)
    with open(Path(__file__).parent / "schema.sql") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

@contextmanager
def get_connection():
    """Get database connection with context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### 2. Repository Pattern for Data Access

Create `fiedler/db/repositories.py`:
```python
"""Data access layer for Fiedler database."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .manager import get_connection

class JobRepository:
    @staticmethod
    def create_job(job_data: Dict[str, Any]) -> str:
        """Create a new job record."""
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, correlation_id, prompt_summary,
                                  prompt_tokens, num_files, package_size_bytes,
                                  models_requested, output_dir, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_data['job_id'], job_data['correlation_id'], ...))
        return job_data['job_id']

    @staticmethod
    def update_job_status(job_id: str, status: str, completed_at: datetime = None):
        """Update job completion status."""
        # Implementation
        pass

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        # Implementation
        pass

class ExecutionRepository:
    @staticmethod
    def create_execution(execution_data: Dict[str, Any]) -> int:
        """Create a model execution record."""
        # Implementation
        pass

    @staticmethod
    def update_execution(execution_id: int, updates: Dict[str, Any]):
        """Update execution with results."""
        # Implementation
        pass

class ReviewRepository:
    @staticmethod
    def create_review(review_data: Dict[str, Any]) -> int:
        """Create a quality review."""
        # Implementation
        pass

    @staticmethod
    def get_reviews_for_execution(execution_id: int) -> List[Dict]:
        """Get all reviews for an execution."""
        # Implementation
        pass

class MetricsRepository:
    @staticmethod
    def get_model_performance(model_id: str = None) -> List[Dict]:
        """Get performance metrics, optionally filtered by model."""
        with get_connection() as conn:
            if model_id:
                cursor = conn.execute(
                    "SELECT * FROM performance_metrics WHERE model_id = ?",
                    (model_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM performance_metrics")

            return [dict(row) for row in cursor.fetchall()]
```

### 3. Integrate with fiedler_send

Update `fiedler/tools/send.py`:
```python
from ..db.repositories import JobRepository, ExecutionRepository

def fiedler_send(...):
    # Create job record
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{correlation_id[:8]}"

    JobRepository.create_job({
        'job_id': job_id,
        'correlation_id': correlation_id,
        'prompt_summary': prompt[:200],
        'prompt_tokens': estimate_tokens(full_prompt),
        'num_files': len(files) if files else 0,
        'package_size_bytes': package_size,
        'models_requested': json.dumps(resolved_models),
        'output_dir': output_dir,
        'status': 'running'
    })

    # For each model execution
    for model_name in resolved_models:
        execution_id = ExecutionRepository.create_execution({
            'job_id': job_id,
            'model_id': model_name,
            'started_at': datetime.now(),
            'status': 'running'
        })

        # ... execute model ...

        # Update with results
        ExecutionRepository.update_execution(execution_id, {
            'completed_at': datetime.now(),
            'elapsed_seconds': elapsed,
            'status': 'completed',
            'prompt_tokens': result['usage']['prompt_tokens'],
            'completion_tokens': result['usage']['completion_tokens'],
            'total_cost': calculated_cost,
            'output_file': output_path,
            ...
        })

    # Update job completion
    JobRepository.update_job_status(job_id, 'completed', datetime.now())
```

### 4. New MCP Tool: fiedler_review_output

Create `fiedler/tools/review.py`:
```python
"""Quality review tools."""

def fiedler_review_output(
    execution_id: int,
    accuracy: float,
    completeness: float,
    clarity: float,
    depth: float,
    usefulness: float,
    strengths: str = "",
    weaknesses: str = "",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Submit a quality review for a model execution.

    Args:
        execution_id: ID from model_executions table
        accuracy: Correctness rating (1-10)
        completeness: Completeness rating (1-10)
        clarity: Clarity rating (1-10)
        depth: Depth rating (1-10)
        usefulness: Usefulness rating (1-10)
        strengths: What was good about this output
        weaknesses: What was lacking
        notes: General observations

    Returns:
        Review confirmation with ID
    """
    overall = (accuracy + completeness + clarity + depth + usefulness) / 5

    review_id = ReviewRepository.create_review({
        'execution_id': execution_id,
        'reviewer': 'user',
        'accuracy': accuracy,
        'completeness': completeness,
        'clarity': clarity,
        'depth': depth,
        'usefulness': usefulness,
        'overall_rating': overall,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'notes': notes
    })

    return {
        "status": "reviewed",
        "review_id": review_id,
        "overall_rating": overall
    }
```

### 5. New MCP Tool: fiedler_get_metrics

Create `fiedler/tools/metrics.py`:
```python
"""Performance metrics and analytics."""

def fiedler_get_metrics(model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance metrics for models.

    Args:
        model_id: Optional model to filter by

    Returns:
        Performance statistics
    """
    metrics = MetricsRepository.get_model_performance(model_id)

    return {
        "metrics": metrics,
        "summary": {
            "total_models": len(metrics),
            "best_speed": min(m['avg_elapsed_seconds'] for m in metrics if m['avg_elapsed_seconds']),
            "best_quality": max(m['avg_quality_rating'] for m in metrics if m['avg_quality_rating']),
            "most_used": max(metrics, key=lambda m: m['total_executions'])['model_id']
        }
    }
```

### 6. New MCP Tool: fiedler_list_jobs

```python
def fiedler_list_jobs(
    limit: int = 20,
    model_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List recent jobs with optional filters.

    Args:
        limit: Max number of jobs to return
        model_id: Filter by model used
        status: Filter by status (running, completed, failed)

    Returns:
        List of jobs with summary info
    """
    # Query jobs with filters
    # Return structured results
```

**Usage Examples:**

```python
# After a job completes
result = fiedler_send(...)
job_id = result["job_id"]

# Get execution details
status = fiedler_get_status(job_id)
gemini_execution_id = status["models"]["gemini-2.5-pro"]["execution_id"]

# Review the output quality
fiedler_review_output(
    execution_id=gemini_execution_id,
    accuracy=9.0,
    completeness=8.5,
    clarity=9.5,
    depth=8.0,
    usefulness=9.0,
    strengths="Very thorough analysis, well-organized, clear explanations",
    weaknesses="Could have included more code examples",
    notes="Best output so far for requirements extraction"
)

# View performance metrics
metrics = fiedler_get_metrics()
# Shows: avg speed, quality ratings, cost, success rate per model

# Compare models
metrics = fiedler_get_metrics("gemini-2.5-pro")
# Shows: Gemini-specific performance data
```

**Benefits:**
- **Historical tracking** - See performance trends over time
- **Model comparison** - Which model is fastest/best/cheapest?
- **Quality analytics** - Track output quality across jobs
- **Cost monitoring** - Total spend per model/provider
- **Informed decisions** - Data-driven model selection
- **Problem detection** - Identify declining performance
- **Future ML** - Data for training model selection heuristics

**Migration Path:**
- SQLite for now (embedded, simple)
- Later: Migrate to PostgreSQL (production scale)
- Schema compatible with both
- Export/import tools for migration

**Testing:**
1. Initialize database: `fiedler` auto-creates on first run
2. Run a job: Verify records in `jobs` and `model_executions`
3. Submit review: Test `fiedler_review_output`
4. View metrics: Test `fiedler_get_metrics`
5. Query history: Test `fiedler_list_jobs`

---

## Implementation Priority

1. **Change 1 (Direct Filesystem)** - High priority, immediate friction reduction
2. **Change 2 (Progress Querying)** - Medium priority, quality-of-life improvement
3. **Change 3 (Performance Database)** - Medium priority, enables analytics

## Rollout Plan

1. Implement Change 1 first (simpler, immediate value)
2. Test thoroughly with current architecture work
3. Implement Change 2 alongside Change 3 (they complement each other)
4. Consider versioning as Fiedler v1.1

## Dependencies

- **Change 2 → Change 3:** Job tracking (Change 2) feeds into database (Change 3)
- Can implement incrementally: Database first, then reviews, then analytics

---

**Status:** Change 1 complete, Changes 2 & 3 pending

## Implementation Log

### Change 1: Direct Filesystem Access - ✓ COMPLETED (2025-10-02)

**Implementation:**
- Modified `/mnt/projects/ICCM/fiedler/docker-compose.yml`:
  - Added volume mount: `/mnt/projects:/mnt/projects:ro`
  - Updated env var: `FIEDLER_ALLOWED_FILE_ROOTS=/app/allowed_files,/app/fiedler_output,/mnt/projects`
- Rebuilt container: `docker compose down && docker compose up -d --build`

**Verification:**
- ✓ Container can access `/mnt/projects` directory
- ✓ File validation allows `/mnt/projects/ICCM/architecture/scope.md`
- ✓ Security still blocks unauthorized paths (e.g., `/etc/passwd`)

**Side Effect:**
- MCP connection breaks on container restart (expected for stdio protocol)
- Solution: Restart Claude Code to re-establish MCP connection

**Benefits Realized:**
- No more copying files to `/mnt/projects/ICCM/fiedler/allowed_files/`
- No more path translation between host and container
- Simpler workflow for all future Fiedler operations

**Next Steps:**
- Restart Claude Code to reconnect MCP
- Retry requirements extraction job with actual host paths
- Monitor for output/logs (Change 2 would help here)

---

## Troubleshooting Notes

### First Requirements Extraction Attempt (2025-10-02 ~09:55 EDT)

**What happened:**
- Sent 768KB package (18 files) to Fiedler's default triplet
- Job failed silently - no output files, no logs, no error messages
- Waited 10+ minutes, checked multiple times
- Output directory `/mnt/projects/ICCM/architecture/phase1_requirements_extraction` was created but remained empty

**Debugging attempted:**
- Checked `docker logs fiedler-mcp` - empty
- Checked `/app/fiedler_output/` - empty
- Checked for any .md files modified in last 60 minutes - only input files
- Verified papers were copied to `/app/allowed_files/phase1_papers/` - confirmed present
- No process logs, no error files, no indication of what went wrong

**Root cause:**
Unknown - no diagnostic information available

**Why this motivated Change 2 (Progress Querying):**
This incident showed that Fiedler has zero visibility into job execution. When a job fails, there's no way to:
- Check if it started
- See which models are processing
- Get error messages
- Determine if it's still running or died

Change 2 will add `fiedler_get_status(job_id)` to provide real-time job tracking.

**Action items for retry:**
- Use actual host paths (e.g., `/mnt/projects/ICCM/docs/papers/01_*.md`) instead of copied files
- Check for grok-4 model availability (previous config only showed gemini-2.5-pro and gpt-5)
- After retry, if successful, compare to understand what changed
- After retry, if failed again, implement Change 2 immediately for diagnostics

---

**Next Steps After Session Restart:**
1. Verify MCP reconnection: `fiedler_get_config()`
2. Retry requirements extraction using actual paths
3. If job fails again, prioritize Change 2 implementation
