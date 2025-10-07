# Dewey Tools Additions for Godot Logging
# To be merged into existing /mnt/projects/ICCM/dewey/dewey/tools.py

import os
import json
import logging
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_values, Json

# Assume db_pool is existing connection pool
# from .database import db_pool

# --- NEW LOGGING TOOLS ---

# REQ-DEW-001: Batch log storage tool
async def dewey_store_logs_batch(logs: list):
    """
    Stores a batch of log entries (REQ-DEW-004: single transaction)
    Max 1,000 entries per batch (REQ-DEW-001)
    """
    if not logs:
        return {"status": "ok", "message": "No logs to store."}

    if len(logs) > 1000:
        raise ValueError(f"Batch size {len(logs)} exceeds maximum 1000")

    # REQ-DEW-003: Validate log levels
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    for log in logs:
        if log.get('level', '').upper() not in valid_levels:
            raise ValueError(f"Invalid log level in batch: {log.get('level')}")

    # Prepare data for execute_values
    insert_data = [
        (
            log.get('trace_id'),
            log.get('component'),
            log.get('level', '').upper(),
            log.get('message'),
            Json(log.get('data')) if log.get('data') else None,
            log.get('created_at', datetime.now(timezone.utc).isoformat())
        ) for log in logs
    ]

    query = """
        INSERT INTO logs (trace_id, component, level, message, data, created_at)
        VALUES %s
    """

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            execute_values(cur, query, insert_data)
        conn.commit()
        return {"status": "ok", "inserted_count": len(insert_data)}
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Failed to batch insert logs: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)


# REQ-DEW-006: Log query tool
async def dewey_query_logs(
    trace_id: str = None,
    component: str = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    search: str = None,
    limit: int = 100
):
    """Queries logs with various filters (REQ-DEW-008: includes age)"""
    limit = min(max(1, limit), 1000)  # Clamp to 1-1000

    query_parts = ["SELECT id, trace_id, component, level, message, data, created_at, (NOW() - created_at) as age FROM logs"]
    where_clauses = []
    params = []

    if trace_id:
        where_clauses.append("trace_id = %s")
        params.append(trace_id)
    if component:
        where_clauses.append("component = %s")
        params.append(component)
    if level:
        # Minimum log level filter
        levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR']
        try:
            min_level_index = levels.index(level.upper())
            allowed_levels = levels[min_level_index:]
            where_clauses.append("level = ANY(%s)")
            params.append(allowed_levels)
        except ValueError:
            raise ValueError(f"Invalid level: {level}")
    if start_time:
        where_clauses.append("created_at >= %s")
        params.append(start_time)
    if end_time:
        where_clauses.append("created_at <= %s")
        params.append(end_time)
    if search:
        # REQ-DEW-006: Full-text search
        where_clauses.append("to_tsvector('english', message) @@ websearch_to_tsquery('english', %s)")
        params.append(search)

    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    query_parts.append("ORDER BY created_at DESC")
    query_parts.append("LIMIT %s")
    params.append(limit)

    final_query = " ".join(query_parts)

    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(final_query, tuple(params))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in rows]
            return results
    finally:
        db_pool.putconn(conn)


# REQ-DEW-009: Log clearing tool
async def dewey_clear_logs(before_time: str = None, component: str = None, level: str = None):
    """Clears logs based on criteria with default retention policy"""
    where_clauses = []
    params = []

    if before_time:
        where_clauses.append("created_at < %s")
        params.append(before_time)
    else:
        # Default retention policy from env var
        retention_days = int(os.environ.get("LOG_RETENTION_DAYS", 7))
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        where_clauses.append("created_at < %s")
        params.append(cutoff_date.isoformat())

    if component:
        where_clauses.append("component = %s")
        params.append(component)
    if level:
        where_clauses.append("level = %s")
        params.append(level.upper())

    if not where_clauses:
        raise ValueError("clear_logs requires at least one filter to prevent accidental deletion.")

    query = f"DELETE FROM logs WHERE {' AND '.join(where_clauses)}"

    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            deleted_count = cur.rowcount
        conn.commit()
        return {"status": "ok", "deleted_count": deleted_count}
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)


# REQ-DEW-010: Log statistics tool
async def dewey_get_log_stats():
    """Returns statistics about the logs table"""
    queries = {
        "total_count": "SELECT COUNT(*) FROM logs;",
        "count_by_component": "SELECT component, COUNT(*) FROM logs GROUP BY component;",
        "count_by_level": "SELECT level, COUNT(*) FROM logs GROUP BY level;",
        "time_range": "SELECT MIN(created_at), MAX(created_at) FROM logs;",
        "db_size": "SELECT pg_size_pretty(pg_total_relation_size('logs'));"
    }

    stats = {}
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(queries["total_count"])
            stats["total_count"] = cur.fetchone()[0]

            cur.execute(queries["count_by_component"])
            stats["count_by_component"] = dict(cur.fetchall())

            cur.execute(queries["count_by_level"])
            stats["count_by_level"] = dict(cur.fetchall())

            cur.execute(queries["time_range"])
            min_ts, max_ts = cur.fetchone()
            stats["oldest_log_at"] = min_ts.isoformat() if min_ts else None
            stats["newest_log_at"] = max_ts.isoformat() if max_ts else None

            cur.execute(queries["db_size"])
            stats["estimated_db_size"] = cur.fetchone()[0]

        return stats
    finally:
        db_pool.putconn(conn)
