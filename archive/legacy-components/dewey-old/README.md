# Dewey MCP Server

Dewey is a WebSocket-based MCP (Model Context Protocol) server that manages **Winni**, a PostgreSQL data lake for conversation histories, startup contexts, and LLM orchestration results.

## Architecture

- **Protocol**: WebSocket MCP on port 9020
- **Database**: PostgreSQL (Winni) on Irina server
- **Container**: Docker (dewey-mcp)
- **Network**: iccm_network (shared with Fiedler)

## Features

- **11 MCP Tools**: Complete conversation management, search, and startup context tools
- **Transaction-Safe**: Automatic turn numbering with row locking
- **Full-Text Search**: PostgreSQL ts_rank for relevance ranking
- **Connection Pooling**: Efficient database connection management
- **Docker Deployment**: Single-command deployment

## Quick Start

### 1. Setup Database

```bash
# Connect to PostgreSQL as postgres user
psql -U postgres -h irina

# Create database and user
CREATE DATABASE winni;
CREATE USER dewey WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE winni TO dewey;

# Connect to winni database
\c winni

# Run schema (from your local machine, pointing to the schema file)
\i /mnt/projects/ICCM/dewey/schema.sql
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set your password
nano .env
```

### 3. Build and Start

```bash
# Build container
docker-compose build

# Start service
docker-compose up -d

# Check logs
docker logs -f dewey-mcp
```

### 4. Configure Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "dewey": {
      "url": "ws://localhost:9020"
    }
  }
}
```

## Available Tools

### Conversation Management
- `dewey_begin_conversation` - Start a new conversation
- `dewey_store_message` - Store a single message
- `dewey_store_messages_bulk` - Store multiple messages at once (supports file references)
- `dewey_get_conversation` - Retrieve full conversation
- `dewey_list_conversations` - List conversations with pagination
- `dewey_delete_conversation` - Delete conversation and messages

### Search
- `dewey_search` - Full-text search with ranking

### Startup Contexts
- `dewey_get_startup_context` - Get active or named context
- `dewey_set_startup_context` - Create/update context
- `dewey_list_startup_contexts` - List all contexts
- `dewey_delete_startup_context` - Delete a context

## Storing Claude Code Sessions

Dewey can directly import Claude Code session files using the **file reference pattern**:

### Method 1: Inline (Small Conversations)
```python
dewey_store_messages_bulk(
    conversation_id="...",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
)
```

### Method 2: File Reference - Claude Code Sessions (Recommended)
```python
# 1. Find current Claude Code session file
# Located at: ~/.claude/projects/-home-<user>/<session-uuid>.jsonl

# 2. Store entire session directly (no conversion needed)
dewey_store_messages_bulk(
    conversation_id="...",
    messages_file="/host/home/aristotle9/.claude/projects/-home-aristotle9/<session-id>.jsonl"
)
```

**Features:**
- **No size limits** - PostgreSQL handles constraints
- **Automatic format detection** - Supports JSON arrays OR JSONL (newline-delimited)
- **Claude Code native format** - Handles nested message structures automatically
- **Full filesystem access** - Entire host filesystem mounted read-only at `/host/`
- **Automatic content normalization** - Arrays/objects → JSON strings

**Claude Code Format Handling (BUG #18 workaround):**
- Extracts `role` and `content` from nested `message: {role, content}` structures
- Stores non-message entries (snapshots, metadata) as `role='system'`
- Preserves full original entry in `metadata` JSONB field for complete fidelity

**Known Issues:**
- **BUG #19**: Large bulk stores (>1000 messages) succeed but response exceeds 25K token limit
  - Operation completes successfully, response just can't be displayed
  - Workaround: Verify with `dewey_list_conversations` to see message count

## Database Schema

### Tables
- **conversations**: Conversation metadata with JSONB metadata column
- **messages**: Messages with turn numbers, full-text search index
- **startup_contexts**: Named contexts with single-active enforcement
- **fiedler_results**: LLM orchestration results (Phase 2)

### Key Features
- UUID primary keys
- Automatic timestamps (created_at, updated_at)
- Cascade deletes
- Full-text search indexes
- JSONB metadata support
- Transaction-safe turn numbering

## Development

### Project Structure
```
dewey/
├── dewey/
│   ├── __init__.py
│   ├── config.py         # Environment configuration
│   ├── database.py       # Connection pooling
│   ├── tools.py          # 11 MCP tool implementations
│   └── mcp_server.py     # WebSocket MCP server
├── schema.sql            # PostgreSQL schema
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# TODO: Add test suite
# docker exec -it dewey-mcp python -m pytest tests/
```

### Viewing Logs

```bash
# Follow logs
docker logs -f dewey-mcp

# Last 100 lines
docker logs --tail 100 dewey-mcp
```

## Troubleshooting

### Database Connection Failed
- Check Irina server is accessible
- Verify database credentials in .env
- Ensure winni database exists

### Port Already in Use
- Check if another service is using port 9020
- Modify port in docker-compose.yml if needed

### Container Won't Start
- Check logs: `docker logs dewey-mcp`
- Verify environment variables are set
- Ensure iccm_network exists: `docker network ls`

## Phase 2 Roadmap

- Fiedler integration tools
- Link Fiedler results to conversations
- Semantic search (pgvector + embeddings)
- Performance monitoring
- Automated backups

## Contributing

This is part of the ICCM (Integrated Cognitive-Cybernetic Methodology) project.

## License

Internal use only
