# Emergency Log Retrieval

## Overview
When the MCP relay is down or Dewey tools are unavailable, you can query logs directly from the PostgreSQL database.

---

## Prerequisites

**Database Connection Info:**
- Host: `192.168.1.210`
- Port: `5432`
- Database: `winni`
- User: `dewey`
- Password: `D3w3y!SecurePass2025`

---

## Method 1: Query via Dewey Container (Recommended)

The Dewey container has direct access to the database and Python with asyncpg installed.

### Basic Log Query

```bash
docker exec dewey-mcp python3 << 'PYTHON'
import asyncpg
import asyncio
import json

async def query_logs():
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    # Query last 100 logs from a component
    rows = await conn.fetch('''
        SELECT component, level, message, data, created_at
        FROM logs
        WHERE component = $1
        ORDER BY created_at DESC
        LIMIT 100
    ''', 'mcp-relay')  # Change component name here

    print(f'Found {len(rows)} log entries:\n')

    for row in rows:
        print(f'[{row["created_at"]}] {row["level"]}: {row["message"]}')
        if row['data']:
            print(f'  Data: {json.dumps(dict(row["data"]), indent=2)}')
        print()

    await conn.close()

asyncio.run(query_logs())
PYTHON
```

### Query by Time Range

```bash
docker exec dewey-mcp python3 << 'PYTHON'
import asyncpg
import asyncio

async def query_logs():
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    rows = await conn.fetch('''
        SELECT component, level, message, created_at
        FROM logs
        WHERE created_at BETWEEN $1 AND $2
        ORDER BY created_at DESC
    ''', '2025-10-10 10:00:00+00', '2025-10-10 12:00:00+00')

    for row in rows:
        print(f'[{row["created_at"]}] {row["component"]} - {row["level"]}: {row["message"]}')

    await conn.close()

asyncio.run(query_logs())
PYTHON
```

### Query by Log Level

```bash
docker exec dewey-mcp python3 << 'PYTHON'
import asyncpg
import asyncio

async def query_errors():
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    rows = await conn.fetch('''
        SELECT component, message, created_at
        FROM logs
        WHERE level = 'ERROR'
        AND created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC
    ''')

    print(f'Found {len(rows)} errors in last 24 hours:\n')
    for row in rows:
        print(f'[{row["created_at"]}] {row["component"]}: {row["message"]}')

    await conn.close()

asyncio.run(query_errors())
PYTHON
```

### Check Log Activity by Component

```bash
docker exec dewey-mcp python3 << 'PYTHON'
import asyncpg
import asyncio

async def check_activity():
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    rows = await conn.fetch('''
        SELECT component,
               COUNT(*) as count,
               MAX(created_at) as latest,
               MIN(created_at) as earliest
        FROM logs
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY component
        ORDER BY count DESC
    ''')

    print('Log activity in last 24 hours:\n')
    print(f'{"Component":<20} {"Count":<10} {"Latest":<30}')
    print('-' * 60)

    for row in rows:
        print(f'{row["component"]:<20} {row["count"]:<10} {row["latest"]}')

    if not rows:
        print('No logs found in last 24 hours')

    await conn.close()

asyncio.run(check_activity())
PYTHON
```

---

## Method 2: Direct psql Query (from irina)

If you have SSH access to the database server (192.168.1.210):

```bash
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
  "PGPASSWORD='D3w3y!SecurePass2025' psql -h localhost -U dewey -d winni -c \
  \"SELECT component, level, message, created_at FROM logs ORDER BY created_at DESC LIMIT 50;\""
```

### Get Error Count by Component

```bash
sshpass -p "Edgar01760" ssh -o StrictHostKeyChecking=no aristotle9@192.168.1.210 \
  "PGPASSWORD='D3w3y!SecurePass2025' psql -h localhost -U dewey -d winni -c \
  \"SELECT component, COUNT(*) as errors FROM logs WHERE level='ERROR' GROUP BY component ORDER BY errors DESC;\""
```

---

## Method 3: Emergency Python Script

Save this as `/tmp/emergency_logs.py` and run with `python3 /tmp/emergency_logs.py`:

```python
#!/usr/bin/env python3
"""
Emergency log retrieval script.
Usage: python3 emergency_logs.py [component] [hours_back]
"""
import asyncpg
import asyncio
import sys
import json
from datetime import datetime, timedelta

async def query_logs(component=None, hours_back=24):
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    if component:
        query = '''
            SELECT component, level, message, data, created_at
            FROM logs
            WHERE component = $1
            AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
        ''' % hours_back
        rows = await conn.fetch(query, component)
    else:
        query = '''
            SELECT component, level, message, data, created_at
            FROM logs
            WHERE created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 200
        ''' % hours_back
        rows = await conn.fetch(query)

    print(f'Found {len(rows)} log entries:\n')

    for row in rows:
        timestamp = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{timestamp}] {row["component"]} - {row["level"]}: {row["message"]}')
        if row['data']:
            print(f'  {json.dumps(dict(row["data"]), indent=2)}')

    await conn.close()

if __name__ == '__main__':
    component = sys.argv[1] if len(sys.argv) > 1 else None
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    print(f'Querying logs for {component or "all components"} from last {hours} hours...\n')
    asyncio.run(query_logs(component, hours))
```

### Usage Examples

```bash
# All logs from last 24 hours
python3 /tmp/emergency_logs.py

# Specific component, last 2 hours
python3 /tmp/emergency_logs.py mcp-relay 2

# Fiedler logs, last hour
python3 /tmp/emergency_logs.py fiedler 1
```

---

## Database Schema Reference

### Logs Table Structure

```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')),
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Useful Queries

**Count logs by level:**
```sql
SELECT level, COUNT(*)
FROM logs
GROUP BY level
ORDER BY COUNT(*) DESC;
```

**Recent errors with JSON data:**
```sql
SELECT component, message, data, created_at
FROM logs
WHERE level = 'ERROR'
AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

**Search message text:**
```sql
SELECT component, level, message, created_at
FROM logs
WHERE message ILIKE '%connection%'
AND created_at > NOW() - INTERVAL '6 hours'
ORDER BY created_at DESC;
```

**Query JSON data:**
```sql
SELECT component, message, data->>'request_id' as request_id, created_at
FROM logs
WHERE data->>'request_id' IS NOT NULL
LIMIT 50;
```

---

## Troubleshooting

### Connection Refused

**Issue:** `connection refused` error

**Solution:** Check if PostgreSQL is running on 192.168.1.210:
```bash
docker exec dewey-mcp nc -zv 192.168.1.210 5432
```

### Authentication Failed

**Issue:** `password authentication failed`

**Solution:** Verify password in Dewey container environment:
```bash
docker exec dewey-mcp env | grep DEWEY_DB_PASSWORD
```

### No Logs Found

**Possible causes:**
1. Logging system not writing to database (see Issue #11)
2. Time range too narrow
3. Component name incorrect

**Verify logs exist:**
```bash
docker exec dewey-mcp python3 << 'PYTHON'
import asyncpg
import asyncio

async def check():
    conn = await asyncpg.connect(
        host='192.168.1.210',
        port=5432,
        database='winni',
        user='dewey',
        password='D3w3y!SecurePass2025'
    )

    count = await conn.fetchval('SELECT COUNT(*) FROM logs')
    print(f'Total logs in database: {count}')

    if count > 0:
        latest = await conn.fetchrow('SELECT component, created_at FROM logs ORDER BY created_at DESC LIMIT 1')
        print(f'Latest log: {latest["component"]} at {latest["created_at"]}')

    await conn.close()

asyncio.run(check())
PYTHON
```

---

## Security Notes

⚠️ **Warning:** This document contains database credentials. In production:
- Use environment variables
- Restrict access to this document
- Rotate passwords regularly
- Use certificate-based auth where possible

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/Logging_System.md` - Normal logging usage
- GitHub Issue #11 - Logging system bugs
- `/mnt/projects/Joshua/knowledge-base/Error_Handling_Protocol.md` - Error handling

---

*Last Updated: 2025-10-10*
*Created for emergency diagnostics when Dewey tools unavailable*
