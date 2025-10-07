# dewey/tools.py
"""
Implementation of all 11 Dewey MCP tools with async database operations.
"""
import logging
import json
from datetime import datetime
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
    """Recursively serialize datetime, UUID, and asyncpg Record objects."""
    # Handle asyncpg Record objects by converting to dict
    if hasattr(item, '__class__') and item.__class__.__name__ == 'Record':
        return _serialize_item(dict(item))
    if isinstance(item, dict):
        return {k: _serialize_item(v) for k, v in item.items()}
    if isinstance(item, list):
        return [_serialize_item(i) for i in item]
    if isinstance(item, datetime):
        return item.isoformat()
    if isinstance(item, UUID):
        return str(item)
    return item

# --- Conversation Management Tools ---

async def dewey_begin_conversation(session_id: str = None, metadata: dict = None) -> dict:
    """Starts a new conversation and returns its ID."""
    sql = """
        INSERT INTO conversations (session_id, metadata)
        VALUES ($1, $2)
        RETURNING id, session_id, created_at;
    """
    try:
        async with db_pool.transaction() as conn:
            result = await conn.fetchrow(sql, session_id, json.dumps(metadata) if metadata else None)
        logger.info(f"Began new conversation {result['id']}.")
        return {
            "conversation_id": str(result['id']),
            "session_id": result['session_id'],
            "created_at": result['created_at'].isoformat()
        }
    except Exception as e:
        logger.error(f"Error in dewey_begin_conversation: {e}")
        raise ToolError("Failed to begin conversation.")

async def dewey_store_message(conversation_id: str, role: str, content: str, turn_number: int = None, metadata: dict = None) -> dict:
    """Stores a single message in a conversation."""
    conv_id = _validate_uuid(conversation_id, "conversation_id")
    if role not in ('user', 'assistant', 'system', 'tool'):
        raise ToolError("Invalid role. Must be one of 'user', 'assistant', 'system', 'tool'.")

    # Validate content size
    if len(content) > MAX_CONTENT_SIZE:
        raise ToolError(f"Content exceeds maximum size of {MAX_CONTENT_SIZE} bytes.")

    try:
        async with db_pool.transaction() as conn:
            # Lock the conversation to safely determine the next turn number
            check = await conn.fetchval("SELECT 1 FROM conversations WHERE id = $1 FOR UPDATE;", conv_id)
            if check is None:
                raise ToolError(f"Conversation with id '{conversation_id}' not found.")

            if turn_number is None:
                turn_number = await conn.fetchval(
                    "SELECT COALESCE(MAX(turn_number), 0) + 1 FROM messages WHERE conversation_id = $1;",
                    conv_id
                )

            sql = """
                INSERT INTO messages (conversation_id, turn_number, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, turn_number, created_at;
            """
            result = await conn.fetchrow(sql, conv_id, turn_number, role, content, json.dumps(metadata) if metadata else None)

            # Update conversation timestamp (trigger will set updated_at automatically)
            await conn.execute("UPDATE conversations SET id = id WHERE id = $1;", conv_id)

        logger.info(f"Stored message {result['id']} in conversation {conversation_id} (turn {result['turn_number']}).")
        return {
            "message_id": str(result['id']),
            "turn_number": result['turn_number'],
            "created_at": result['created_at'].isoformat()
        }
    except Exception as e:
        logger.error(f"Error in dewey_store_message: {e}")
        if isinstance(e, ToolError):
            raise
        raise ToolError("Failed to store message.")

async def dewey_store_messages_bulk(messages: list = None, messages_file: str = None, conversation_id: str = None, session_id: str = None, metadata: dict = None) -> dict:
    """Stores a list of messages in a single transaction using optimized multi-row INSERT.

    Args:
        messages: List of message objects (inline)
        messages_file: Path to JSON file containing message array (industry-standard file reference)
        conversation_id: Existing conversation ID
        session_id: Session ID for new conversation
        metadata: Metadata for new conversation
    """
    # Support industry-standard file reference pattern
    if messages_file:
        import json
        import os
        if not os.path.exists(messages_file):
            raise ToolError(f"File not found: {messages_file}")
        try:
            with open(messages_file, 'r') as f:
                # Detect format: JSON array or JSONL (Claude Code session format)
                first_char = f.read(1)
                f.seek(0)

                if first_char == '[':
                    # Standard JSON array
                    messages = json.load(f)
                elif first_char == '{':
                    # JSONL format (newline-delimited JSON objects)
                    messages = []
                    for line in f:
                        line = line.strip()
                        if line:
                            messages.append(json.loads(line))
                else:
                    raise ToolError(f"Unrecognized file format (must start with '[' or '{{')")
        except json.JSONDecodeError as e:
            raise ToolError(f"Invalid JSON in messages_file: {e}")

    if not isinstance(messages, list) or not messages:
        raise ToolError("Parameter 'messages' (or messages_file content) must be a non-empty list.")

    # Normalize messages to fit Dewey schema (BUG #18 workaround)
    import json
    for i, msg in enumerate(messages):
        # Handle Claude Code session format
        if 'message' in msg and isinstance(msg['message'], dict):
            # Extract role/content from nested message
            role = msg['message'].get('role', 'NA')
            content = msg['message'].get('content', 'NA')
            # Store original full entry in metadata
            messages[i] = {
                'role': role,
                'content': json.dumps(content) if isinstance(content, (list, dict)) else str(content),
                'metadata': msg  # Full original entry
            }
        elif 'role' in msg and 'content' in msg:
            # Already in correct format
            content = msg.get('content')
            if isinstance(content, (list, dict)):
                messages[i]['content'] = json.dumps(content)
        else:
            # Non-message entry (snapshot, etc.) - store as system message with full entry in metadata
            messages[i] = {
                'role': 'system',
                'content': msg.get('type', 'unknown'),  # Use type as content placeholder
                'metadata': msg  # Full original entry
            }

    try:
        async with db_pool.transaction() as conn:
            if conversation_id:
                conv_id = _validate_uuid(conversation_id, "conversation_id")
                check = await conn.fetchval("SELECT 1 FROM conversations WHERE id = $1 FOR UPDATE;", conv_id)
                if check is None:
                    raise ToolError(f"Conversation with id '{conversation_id}' not found.")
            else:
                # Create a new conversation
                conv_id = await conn.fetchval(
                    "INSERT INTO conversations (session_id, metadata) VALUES ($1, $2) RETURNING id;",
                    session_id, json.dumps(metadata) if metadata else None
                )

            # Get starting turn number
            next_turn = await conn.fetchval(
                "SELECT COALESCE(MAX(turn_number), 0) + 1 FROM messages WHERE conversation_id = $1;",
                conv_id
            )

            # Build multi-row INSERT for efficiency
            values = []
            for i, msg in enumerate(messages):
                role = msg.get('role')
                content = msg.get('content')
                msg_metadata = msg.get('metadata')
                values.append((
                    conv_id,
                    next_turn + i,
                    role,
                    content,
                    json.dumps(msg_metadata) if msg_metadata else None
                ))

            # Execute multi-row INSERT with RETURNING
            sql = """
                INSERT INTO messages (conversation_id, turn_number, role, content, metadata)
                SELECT * FROM UNNEST($1::uuid[], $2::integer[], $3::text[], $4::text[], $5::jsonb[])
                RETURNING id;
            """
            results = await conn.fetch(
                sql,
                [v[0] for v in values],  # conversation_ids
                [v[1] for v in values],  # turn_numbers
                [v[2] for v in values],  # roles
                [v[3] for v in values],  # contents
                [v[4] for v in values],  # metadata
            )

            message_ids = [str(row['id']) for row in results]

            # Update conversation timestamp (trigger will set updated_at automatically)
            await conn.execute("UPDATE conversations SET id = id WHERE id = $1;", conv_id)

        logger.info(f"Bulk stored {len(messages)} messages in conversation {conv_id}.")
        return {
            "conversation_id": str(conv_id),
            "stored": len(message_ids),
            "message_ids": message_ids
        }
    except Exception as e:
        logger.error(f"Error in dewey_store_messages_bulk: {e}")
        if isinstance(e, ToolError):
            raise
        raise ToolError("Failed to bulk store messages.")

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

async def dewey_delete_conversation(conversation_id: str, force: bool = False) -> dict:
    """Deletes a conversation and its messages (requires force=True for safety)."""
    if not force:
        raise ToolError("Deletion requires 'force=True' parameter for safety.")

    conv_id = _validate_uuid(conversation_id, "conversation_id")

    async with db_pool.transaction() as conn:
        # Get message count
        message_count = await conn.fetchval("SELECT COUNT(*) FROM messages WHERE conversation_id = $1;", conv_id)

        # Delete conversation (cascade deletes messages)
        result = await conn.execute("DELETE FROM conversations WHERE id = $1;", conv_id)
        if result == "DELETE 0":
            raise ToolError(f"Conversation with id '{conversation_id}' not found.")

    logger.info(f"Deleted conversation {conversation_id} with {message_count} messages.")
    return {
        "deleted": True,
        "messages_deleted": message_count
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

async def dewey_set_startup_context(name: str, content: str, set_active: bool = True) -> dict:
    """Creates or updates a startup context."""
    if not name:
        raise ToolError("Name cannot be empty.")
    if not content:
        raise ToolError("Content cannot be empty.")

    async with db_pool.transaction() as conn:
        # Deactivate other contexts if setting active
        if set_active:
            await conn.execute("UPDATE startup_contexts SET is_active = FALSE WHERE is_active = TRUE;")

        # Upsert context
        result = await conn.fetchrow(
            """
            INSERT INTO startup_contexts (name, content, is_active)
            VALUES ($1, $2, $3)
            ON CONFLICT (name) DO UPDATE
            SET content = EXCLUDED.content,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id, name, is_active, created_at;
            """,
            name, content, set_active
        )

    logger.info(f"Set startup context '{name}' (active: {set_active}).")
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

async def dewey_delete_startup_context(name: str, force: bool = False) -> dict:
    """Deletes a startup context (requires force=True for safety)."""
    if not force:
        raise ToolError("Deletion requires 'force=True' parameter for safety.")

    async with db_pool.transaction() as conn:
        result = await conn.execute("DELETE FROM startup_contexts WHERE name = $1;", name)
        if result == "DELETE 0":
            raise ToolError(f"Startup context '{name}' not found.")

    logger.info(f"Deleted startup context '{name}'.")
    return {"deleted": True}
