# dewey/tools.py
"""
Implementation of all 15 Dewey MCP tools with async database operations.
Updated to include 4 Godot logging tools.
"""
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from dewey.database import db_pool

logger = logging.getLogger(__name__)

# Configuration limits removed - let PostgreSQL handle size constraints
# If issues arise, will be logged as bugs and handled appropriately

class ToolError(Exception):
    """Custom exception for tool-specific errors."""
    def __init__(self, message, code=-32000):
        super().__init__(message)
        self.code = code

def _validate_uuid(uuid_str, param_name):
    """Helper to validate a string is a valid UUID."""
    try:
        return UUID(uuid_str)
    except (ValueError, TypeError):
        raise ToolError(f"Invalid UUID format for parameter '{param_name}'.")

def _serialize_item(item):
    """Recursively serialize datetime, UUID, timedelta, and asyncpg Record objects."""
    # Handle asyncpg Record objects by converting to dict
    if hasattr(item, '__class__') and item.__class__.__name__ == 'Record':
        return _serialize_item(dict(item))
    if isinstance(item, dict):
        return {k: _serialize_item(v) for k, v in item.items()}
    if isinstance(item, list):
        return [_serialize_item(i) for i in item]
    if isinstance(item, datetime):
        return item.isoformat()
    if isinstance(item, timedelta):
        return item.total_seconds()
    if isinstance(item, UUID):
        return str(item)
    return item

# --- Conversation Management Tools ---

async def dewey_get_conversation(conversation_id: str) -> dict:
    """Retrieves a full conversation with all its messages."""
    conv_id = _validate_uuid(conversation_id, "conversation_id")

    async with db_pool.acquire() as conn:
        conv = await conn.fetchrow("SELECT * FROM conversations WHERE id = $1;", conv_id)
        if not conv:
            raise ToolError(f"Conversation with id '{conversation_id}' not found.")

        messages = await conn.fetch(
            "SELECT id, turn_number AS turn, role, content, metadata, created_at FROM messages WHERE conversation_id = $1 ORDER BY turn_number;",
            conv_id
        )

    logger.info(f"Retrieved conversation {conversation_id} with {len(messages)} messages.")
    return {
        "conversation_id": str(conv['id']),
        "session_id": conv['session_id'],
        "created_at": conv['created_at'].isoformat(),
        "updated_at": conv['updated_at'].isoformat(),
        "metadata": conv['metadata'],
        "messages": _serialize_item(messages)
    }

async def dewey_list_conversations(session_id: str = None, limit: int = 20, offset: int = 0, sort_by: str = "updated_at") -> dict:
    """Lists conversations with pagination - optimized with LEFT JOIN instead of correlated subquery."""
    if limit > 100 or limit < 1:
        limit = 20
    if offset < 0:
        offset = 0
    if sort_by not in ("created_at", "updated_at"):
        sort_by = "updated_at"

    async with db_pool.acquire() as conn:
        # Optimized query using LEFT JOIN + GROUP BY instead of correlated subquery
        base_sql = f"""
            SELECT c.id, c.session_id, c.created_at, c.updated_at, c.metadata,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
        """
        count_sql = "SELECT COUNT(*) AS total FROM conversations"

        params = []
        if session_id:
            base_sql += " WHERE c.session_id = $1"
            count_sql += " WHERE session_id = $1"
            params.append(session_id)

        base_sql += f" GROUP BY c.id ORDER BY c.{sort_by} DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2};"
        params.extend([limit, offset])

        conversations = await conn.fetch(base_sql, *params)

        # Get total count
        total = await conn.fetchval(count_sql, *params[:1] if session_id else [])

    logger.info(f"Listed {len(conversations)} conversations (total: {total}).")
    return {
        "conversations": _serialize_item(conversations),
        "total": total,
        "limit": limit,
        "offset": offset
    }

# --- Search Tool ---

async def dewey_search(query: str, session_id: str = None, start_date: str = None, end_date: str = None, limit: int = 20, offset: int = 0) -> dict:
    """Full-text search across conversations - requires GIN index for performance."""
    if not query:
        raise ToolError("Query cannot be empty.")

    if limit > 100 or limit < 1:
        limit = 20
    if offset < 0:
        offset = 0

    async with db_pool.acquire() as conn:
        # Build search query with parameterized placeholders
        base_sql = """
            SELECT m.id AS message_id, m.conversation_id, m.turn_number AS turn,
                   m.role, m.content, m.created_at, m.metadata,
                   c.session_id, c.metadata AS conversation_metadata,
                   ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', $1)) AS rank
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE to_tsvector('english', m.content) @@ plainto_tsquery('english', $1)
        """
        count_sql = """
            SELECT COUNT(*) AS total
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE to_tsvector('english', m.content) @@ plainto_tsquery('english', $1)
        """

        params = [query]
        param_idx = 2

        # Add filters
        if session_id:
            base_sql += f" AND c.session_id = ${param_idx}"
            count_sql += f" AND c.session_id = ${param_idx}"
            params.append(session_id)
            param_idx += 1

        if start_date:
            base_sql += f" AND m.created_at >= ${param_idx}"
            count_sql += f" AND m.created_at >= ${param_idx}"
            params.append(start_date)
            param_idx += 1

        if end_date:
            base_sql += f" AND m.created_at <= ${param_idx}"
            count_sql += f" AND m.created_at <= ${param_idx}"
            params.append(end_date)
            param_idx += 1

        base_sql += f" ORDER BY rank DESC, m.created_at DESC LIMIT ${param_idx} OFFSET ${param_idx+1};"
        params.extend([limit, offset])

        results = await conn.fetch(base_sql, *params)
        total = await conn.fetchval(count_sql, *params[:len(params)-2])

    logger.info(f"Search for '{query}' returned {len(results)} results (total: {total}).")
    return {
        "results": _serialize_item(results),
        "total": total,
        "limit": limit,
        "offset": offset
    }

# --- Startup Context Tools ---

async def dewey_get_startup_context(name: str = None) -> dict:
    """Gets a startup context by name or the active context."""
    async with db_pool.acquire() as conn:
        if name:
            result = await conn.fetchrow("SELECT * FROM startup_contexts WHERE name = $1;", name)
        else:
            result = await conn.fetchrow("SELECT * FROM startup_contexts WHERE is_active = TRUE LIMIT 1;")

    if not result:
        return None

    logger.info(f"Retrieved startup context '{result['name']}'.")
    return _serialize_item(dict(result))

async def dewey_list_startup_contexts(include_content: bool = False) -> dict:
    """Lists all startup contexts."""
    async with db_pool.acquire() as conn:
        if include_content:
            contexts = await conn.fetch("SELECT * FROM startup_contexts ORDER BY name;")
        else:
            contexts = await conn.fetch("SELECT id, name, is_active, created_at, updated_at FROM startup_contexts ORDER BY name;")

    logger.info(f"Listed {len(contexts)} startup contexts.")
    return {"contexts": _serialize_item(contexts)}

# --- Godot Logging Tools ---

async def dewey_store_logs_batch(logs: list) -> dict:
    """
    Stores a batch of log entries (REQ-DEW-004: single transaction)
    Max 1,000 entries per batch (REQ-DEW-001)
    """
    if not logs:
        return {"status": "ok", "message": "No logs to store."}

    if len(logs) > 1000:
        raise ToolError(f"Batch size {len(logs)} exceeds maximum 1000")

    # REQ-DEW-003: Validate log levels
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    for log in logs:
        if log.get('level', '').upper() not in valid_levels:
            raise ToolError(f"Invalid log level in batch: {log.get('level')}")

    # Prepare data for batch insert
    insert_data = []
    for log in logs:
        # Parse created_at if it's a string
        created_at = log.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.now(timezone.utc)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        insert_data.append((
            log.get('trace_id'),
            log.get('component'),
            log.get('level', '').upper(),
            log.get('message'),
            json.dumps(log.get('data')) if log.get('data') else None,
            created_at
        ))

    query = """
        INSERT INTO logs (trace_id, component, level, message, data, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
    """

    async with db_pool.transaction() as conn:
        for data in insert_data:
            await conn.execute(query, *data)

    logger.info(f"Batch stored {len(insert_data)} logs")
    return {"status": "ok", "inserted_count": len(insert_data)}

async def dewey_query_logs(
    trace_id: str = None,
    component: str = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    search: str = None,
    limit: int = 100
) -> list:
    """Queries logs with various filters (REQ-DEW-008: includes age)"""
    limit = min(max(1, limit), 1000)  # Clamp to 1-1000

    query_parts = [
        "SELECT id, trace_id, component, level, message, data, created_at, ",
        "(NOW() - created_at) as age FROM logs"
    ]
    where_clauses = []
    params = []

    if trace_id:
        where_clauses.append(f"trace_id = ${len(params) + 1}")
        params.append(trace_id)
    if component:
        where_clauses.append(f"component = ${len(params) + 1}")
        params.append(component)
    if level:
        # Minimum log level filter
        levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR']
        try:
            min_level_index = levels.index(level.upper())
            allowed_levels = levels[min_level_index:]
            where_clauses.append(f"level = ANY(${len(params) + 1})")
            params.append(allowed_levels)
        except ValueError:
            raise ToolError(f"Invalid level: {level}")
    if start_time:
        where_clauses.append(f"created_at >= ${len(params) + 1}")
        params.append(start_time)
    if end_time:
        where_clauses.append(f"created_at <= ${len(params) + 1}")
        params.append(end_time)
    if search:
        # REQ-DEW-006: Full-text search
        where_clauses.append(f"to_tsvector('english', message) @@ websearch_to_tsquery('english', ${len(params) + 1})")
        params.append(search)

    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    query_parts.append("ORDER BY created_at DESC")
    query_parts.append(f"LIMIT ${len(params) + 1}")
    params.append(limit)

    final_query = " ".join(query_parts)

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(final_query, *params)
        results = [_serialize_item(dict(row)) for row in rows]

    logger.info(f"Queried logs: {len(results)} results")
    return results

async def dewey_clear_logs(before_time: str = None, component: str = None, level: str = None) -> dict:
    """Clears logs based on criteria with default retention policy"""
    where_clauses = []
    params = []

    if before_time:
        where_clauses.append(f"created_at < ${len(params) + 1}")
        params.append(before_time)
    else:
        # Default retention policy from env var
        retention_days = int(os.environ.get("LOG_RETENTION_DAYS", 7))
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        where_clauses.append(f"created_at < ${len(params) + 1}")
        params.append(cutoff_date.isoformat())

    if component:
        where_clauses.append(f"component = ${len(params) + 1}")
        params.append(component)
    if level:
        where_clauses.append(f"level = ${len(params) + 1}")
        params.append(level.upper())

    if not where_clauses:
        raise ToolError("clear_logs requires at least one filter to prevent accidental deletion.")

    query = f"DELETE FROM logs WHERE {' AND '.join(where_clauses)}"

    async with db_pool.transaction() as conn:
        result = await conn.execute(query, *params)

    # Extract count from result string "DELETE N"
    deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0

    logger.info(f"Cleared {deleted_count} logs")
    return {"status": "ok", "deleted_count": deleted_count}

async def dewey_get_log_stats() -> dict:
    """Returns statistics about the logs table"""
    stats = {}

    async with db_pool.acquire() as conn:
        # Total count
        total = await conn.fetchval("SELECT COUNT(*) FROM logs;")
        stats["total_count"] = total

        # Count by component
        rows = await conn.fetch("SELECT component, COUNT(*) FROM logs GROUP BY component;")
        stats["count_by_component"] = {row['component']: row['count'] for row in rows}

        # Count by level
        rows = await conn.fetch("SELECT level, COUNT(*) FROM logs GROUP BY level;")
        stats["count_by_level"] = {row['level']: row['count'] for row in rows}

        # Time range
        row = await conn.fetchrow("SELECT MIN(created_at) as min_ts, MAX(created_at) as max_ts FROM logs;")
        stats["oldest_log_at"] = row['min_ts'].isoformat() if row['min_ts'] else None
        stats["newest_log_at"] = row['max_ts'].isoformat() if row['max_ts'] else None

        # DB size
        size = await conn.fetchval("SELECT pg_size_pretty(pg_total_relation_size('logs'));")
        stats["estimated_db_size"] = size

    logger.info("Retrieved log statistics")
    return stats
