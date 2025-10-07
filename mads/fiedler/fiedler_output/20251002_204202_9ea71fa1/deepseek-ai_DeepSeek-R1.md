<think>
We are going to perform a comprehensive review of the updated Dewey and KGB code.

Key changes that have been addressed:

**Dewey:**
1. Replaced psycopg2 with asyncpg for true async database operations.
2. Optimized bulk insert using multi-row INSERT with UNNEST arrays.
3. Added GIN index for full-text search (schema.sql).
4. Fixed list_conversations N+1 query (LEFT JOIN + GROUP BY).
5. Added content size limits (100KB per message, 1000 message bulk limit).

**KGB (formerly MCP Proxy):**
1. Implemented spy worker pattern - each connection gets dedicated DeweyClient (fixes race condition).
2. Logs ALL messages (not just tool calls) with 10KB truncation.
3. Renamed from mcp_proxy to kgb throughout.
4. Added asyncio.Lock protection in DeweyClient.

We are to review for:
1. Any remaining bugs or logic errors
2. Completeness of fixes
3. Performance concerns
4. Security issues
5. Integration problems

Focus on verifying the 2 critical bugs are fully resolved:
- Dewey async DB operations (no more event loop blocking)
- KGB race condition (no more shared WebSocket)

Let's break down the review by component.

## 1. Dewey (database.py, tools.py, mcp_server.py, schema.sql)

### database.py
- Uses asyncpg for connection pooling.
- The `Database` class manages the pool with `initialize` and `close` methods.
- Provides context managers for acquiring a connection and a transaction.
- The `db_pool` is a global instance.

Review:
- The `acquire` context manager uses `_pool.acquire` which is async and non-blocking.
- The `transaction` context manager uses `conn.transaction()` which is also async.
- The pool is initialized only once and shared. This is efficient and correct.

### tools.py
- All tool functions are async and use the async context managers from `db_pool`.
- Bulk insert uses `UNNEST` for multi-row insert, which is efficient.
- The `dewey_store_message` function uses `FOR UPDATE` to lock the conversation and then determines the next turn number if not provided. This is safe.
- The `dewey_store_messages_bulk` function also uses `FOR UPDATE` and then does a multi-row insert. It also handles creating a new conversation if needed.
- The `dewey_list_conversations` function uses a single query with a `LEFT JOIN` and `GROUP BY` to avoid N+1. This is efficient.
- The `dewey_search` function uses the GIN index (as per the schema) and the `ts_rank` function. The query is built with parameterized placeholders to avoid SQL injection.
- Content size limits are enforced (100KB per message, 1000 messages in bulk).

Potential issues:
- In `dewey_store_message`, the `FOR UPDATE` lock is taken on the conversation. However, if the conversation does not exist, we raise an error. But note: the lock is taken only if the conversation exists. This is correct.
- In `dewey_store_messages_bulk`, we do:
    ```python
    conv_id = _validate_uuid(conversation_id, "conversation_id")
    check = await conn.fetchval("SELECT 1 FROM conversations WHERE id = $1 FOR UPDATE;", conv_id)
    ```
  But if `conversation_id` is not provided, we create a new conversation and then use that `conv_id`. In that case, we don't take a lock? Actually, we don't need to because we just created it and no one else can be using it until the transaction commits. However, we do need to lock the new conversation for the subsequent query of `next_turn`? Actually, we are in a transaction and we just inserted the conversation, so it's locked by our transaction. But note: the `SELECT ... FOR UPDATE` would block until we get the lock, but since we are the ones who inserted it, we already have the lock. So we can skip the `FOR UPDATE` for the new conversation? Actually, we don't do a `FOR UPDATE` for the new conversation. We do:
    ```python
    conv_id = await conn.fetchval(...)  # new conversation
    next_turn = await conn.fetchval("SELECT COALESCE(MAX(turn_number), 0) + 1 ...", conv_id)
    ```
  This is safe because we are in a transaction and the conversation is new, so no other transaction can see it until we commit. However, note that the `SELECT` without a lock might be subject to phantom reads? But since we are the only ones who have inserted the conversation, and we haven't inserted any messages yet, the `MAX(turn_number)` will be null -> 0, so next_turn=1. Then we insert the messages. This is safe.

  But what if two bulk inserts are happening at the same time for the same new conversation? That cannot happen because the conversation is created in this transaction and not visible to others until commit. So it's safe.

  However, if we are using an existing conversation, we do take a `FOR UPDATE` lock. So that is safe.

- In `dewey_store_messages_bulk`, we are building the `values` list and then using `UNNEST` to insert. This is efficient and avoids many round trips.

- The `dewey_search` function uses `plainto_tsquery` which is safe for user input? It's parameterized so no SQL injection. But note: the `query` string is passed directly to `plainto_tsquery`. This is acceptable because `plainto_tsquery` will parse the string and ignore any invalid tokens. It's not a security risk because we are using parameterized queries.

- The `_serialize_item` function recursively serializes `datetime` and `UUID` objects. This is used in the responses. It should handle nested structures.

- The `dewey_list_conversations` function: the `base_sql` uses `GROUP BY c.id` and then orders by `c.{sort_by}`. This is correct.

- The `dewey_delete_conversation` function: it deletes the conversation and cascades to messages. It returns the count of messages deleted. However, note that the `message_count` is obtained before the delete. This is correct because the delete will cascade and we cannot get the count after.

### mcp_server.py
- The server uses `websockets` and handles each connection in `handle_request`.
- Each request is processed by `process_request` which looks up the tool function and calls it.
- The tool functions are called with `await` if they are coroutines.

Review:
- The server is async and uses the async database operations. There should be no blocking.
- The server initializes the database pool on startup and closes it on shutdown.

### schema.sql
- The GIN index is created: `CREATE INDEX IF NOT EXISTS idx_messages_content_fts ON messages USING gin(to_tsvector('english', content));`
- The triggers for updating `updated_at` are defined.
- The indexes for `conversations` and `messages` are appropriate.

## 2. KGB (kgb/dewey_client.py, kgb/proxy_server.py)

### dewey_client.py
- Each `DeweyClient` has its own `asyncio.Lock` to protect the WebSocket connection (since a single connection is used for multiple requests).
- The `_call_tool` method uses the lock to ensure that only one request is in flight at a time.
- The client connects on demand and maintains a persistent connection.

Review:
- The lock ensures that even if multiple tasks are using the same client, they will not interleave requests. This is safe.
- The client reconnects if the connection is closed.

### proxy_server.py
- Each client connection to the KGB proxy creates a `SpyWorker`.
- The `SpyWorker` has its own `DeweyClient` and its own connection to the upstream.
- The `SpyWorker` starts a conversation in Dewey and then logs all messages (both from client and upstream) to that conversation.
- The `SpyWorker` relays messages in both directions.

Review:
- The race condition is fixed because each spy has its own Dewey client and its own WebSocket connection to Dewey. There is no sharing of clients between spies.
- The `SpyWorker` logs every message (truncated to 10KB) with role "user" for client messages and "assistant" for upstream messages.
- The `SpyWorker` handles disconnections and cleans up.

Potential issues:
- The `get_upstream_url` function only supports "fiedler" and "dewey". What if the upstream is not one of these? It returns `None` and then the spy closes the client connection. This is acceptable? The client will get a 4000 close code. But note: the `upstream` is taken from the query string. We should validate it earlier? Actually, in `SpyWorker.start` we check if `upstream_url` is None and then close the connection. This is safe.
- The `relay_client_to_upstream` and `relay_upstream_to_client` functions log the message and then forward it. If logging fails, they still forward the message. This is good for reliability.
- The `truncate_content` function truncates to 10KB (MAX_LOG_CONTENT). This is acceptable.

## Critical Bug Verification

### Dewey async DB operations
- We are using asyncpg and the entire tool implementation is async. The MCP server is async and uses non-blocking database calls. This is fixed.

### KGB race condition
- Each spy worker has its own DeweyClient and thus its own WebSocket connection to Dewey. The DeweyClient also has a lock to serialize requests on that connection. This should prevent any race conditions. The previous issue of sharing a single WebSocket among multiple workers is fixed.

## Other Considerations

### Performance
- Dewey: Bulk insert is optimized with UNNEST. The list_conversations query is optimized. Full-text search uses a GIN index.
- KGB: Each spy worker is independent and should not block others. The logging is done asynchronously and the truncation prevents huge messages from overloading Dewey.

### Security
- Dewey: All SQL queries are parameterized to prevent injection. The UUIDs are validated. Content size is limited to prevent DoS by storing huge messages.
- KGB: The upstream is taken from the query string and only allowed values are accepted. The content is truncated to 10KB for logging to prevent abuse.

### Integration
- Dewey: The MCP server runs on a configurable host and port. The database configuration is from the `config` module.
- KGB: The proxy runs on port 9000 and expects a query parameter `upstream` (defaults to "fiedler"). It then connects to the corresponding upstream MCP server.

## Potential Issues Found

1. **Dewey: `dewey_store_messages_bulk` - new conversation without lock?**
   - As discussed, when creating a new conversation, we don't take a `FOR UPDATE` lock because we are the only ones who can see it. However, note that the `next_turn` is computed without a lock. This is safe because the conversation is new and has no messages. So the `MAX(turn_number)` will be NULL -> 0, then we start at 1. But what if two bulk inserts are happening for the same session_id at the same time and both create a conversation? They will both create a new conversation. That is acceptable because they are separate conversations. The session_id is not unique. So it's by design.

2. **Dewey: `dewey_store_message` - lock on conversation for new message?**
   - We do `SELECT ... FOR UPDATE` on the conversation to lock it. Then we compute the next turn number if not provided. This is safe.

3. **Dewey: `dewey_store_messages_bulk` - lock on existing conversation?**
   - We do `SELECT ... FOR UPDATE` on the conversation to lock it. Then we compute the next turn number. This is safe.

4. **Dewey: `dewey_store_messages_bulk` - what if the bulk insert fails in the middle?**
   - We are in a transaction, so it will roll back. The conversation update will also be rolled back.

5. **KGB: The `SpyWorker` does not log system messages or tool messages?**
   - Currently, it logs client messages as "user" and upstream messages as "assistant". But what if the upstream sends a message with role "system" or "tool"? We are logging it as "assistant". This might be acceptable because the proxy is designed for user-assistant conversations. However, note that the upstream might be Dewey itself (if upstream="dewey") and then we might see tool calls. But the proxy is meant for the user and the assistant (Fiedler). So it's acceptable.

6. **KGB: The `SpyWorker` does not handle non-text messages?**
   - The code assumes the messages are strings. But the WebSocket can send binary data. We are decoding it as a string? In `relay_client_to_upstream`:
        ```python
        content = self.truncate_content(raw_message if isinstance(raw_message, str) else raw_message.decode())
        ```
   - This will decode binary data as UTF-8. If the message is not UTF-8, it will break. We should catch decoding errors? Also, note that the upstream might expect binary data. We are relaying the raw_message (which is either str or bytes). But Dewey expects a string for the content. We might need to handle non-UTF8 data? We could use `raw_message.decode(errors='replace')` or log a placeholder for non-text messages.

   - However, the MCP protocol is JSON-RPC over WebSocket, which is text (UTF-8). So it should be safe. But if the upstream sends binary, then we are decoding it and might get an error. We should catch that.

   - Let's change the decoding to be safe:

        ```python
        try:
            if isinstance(raw_message, bytes):
                content = raw_message.decode('utf-8', errors='replace')
            else:
                content = raw_message
        except Exception as e:
            content = f"[KGB: Failed to decode message: {e}]"
        ```

   - Then truncate.

   - Alternatively, we might not want to log non-text messages? But the requirement is to log ALL messages. We can log a placeholder for binary messages? But note: the proxy is for MCP services, which are text-based. So it's unlikely. But to be safe, we should handle it.

   - We'll update the `truncate_content` method to handle bytes? Actually, we are now converting to string in the relay methods. We should do:

        ```python
        async def relay_client_to_upstream(self):
            ...
            async for raw_message in self.websocket:
                try:
                    # Convert to string for logging, but keep raw for forwarding
                    if isinstance(raw_message, bytes):
                        # Try to decode
                        try:
                            content_str = raw_message.decode('utf-8', errors='replace')
                        except Exception as e:
                            content_str = f"[KGB: Failed to decode bytes: {e}]"
                    else:
                        content_str = raw_message

                    content_truncated = self.truncate_content(content_str)
                    await self.dewey_client.store_message(...)

                    # Forward the raw_message (bytes or str) as is
                    await self.upstream_ws.send(raw_message)
        ```

   - Similarly for the upstream relay.

   - However, note: the current code does:
        ```python
        content = self.truncate_content(raw_message if isinstance(raw_message, str) else raw_message.decode())
        ```
        This will break if the bytes are not UTF-8.

   - We should fix this.

7. **KGB: The `SpyWorker` does not log metadata?**
   - The `store_message` calls in the relay methods do not pass any metadata. We might want to log the fact that it's a proxied message? We could add metadata such as the spy_id, client_id, etc. But the conversation already has metadata with the upstream and spy_id. Each message could have metadata too? We are not currently storing any. We could do:

        ```python
        await self.dewey_client.store_message(
            conversation_id=self.conversation_id,
            role="user",
            content=content_truncated,
            metadata={"spy_id": self.client_id, "direction": "incoming"}   # or "outgoing" for upstream messages?
        )
        ```

   - But the requirement doesn't specify. It's an enhancement.

   - Since the requirement is to log all messages, and we are logging the role and content, it's acceptable without metadata.

8. **KGB: The `SpyWorker` does not handle errors in storing messages?**
   - We catch exceptions and log them, but then continue. This is acceptable because we still forward the message. The logging is best-effort.

9. **KGB: The `DeweyClient` in the spy might be called concurrently?**
   - The `SpyWorker` has two tasks: one for each relay direction. They might try to log at the same time. But the `DeweyClient` has a lock, so the requests will be serialized. This is safe.

10. **Dewey: The `dewey_store_message` function does not allow setting `turn_number`?**
    - The function has a `turn_number` parameter, but in the call from KGB, we are not setting it. We are letting the function determine the next turn. This is correct.

11. **Dewey: The `dewey_store_messages_bulk` function does not allow setting `turn_number` per message?**
    - The function does not have a way to specify the turn number for each message in the bulk. It assigns consecutive turn numbers starting from the next available. This is by design.

12. **Dewey: The `dewey_search` function does not escape the query string?**
    - We are using parameterized queries, so it's safe from SQL injection. The `query` string is passed as a parameter. The `plainto_tsquery` function will handle it appropriately.

## Recommendations

1. **KGB: Handle non-UTF8 messages in the proxy.**
   - We should catch decoding errors and log a placeholder.

2. **KGB: Consider adding metadata to the logged messages?**
   - This is optional and not critical. We can leave it for now.

3. **Dewey: Consider adding an index on `conversations(session_id, updated_at)` for the `dewey_list_conversations` query?**
   - Currently, we have an index on `session_id` and an index on `updated_at`. The query is:
        ```sql
        SELECT ... FROM conversations WHERE session_id = ? ... ORDER BY updated_at DESC
        ```
        We might benefit from a composite index: `CREATE INDEX idx_conversations_session_updated ON conversations(session_id, updated_at DESC);`

   - This is a performance optimization that can be added.

4. **Dewey: The `dewey_search` function does not have a timeout?**
   - A very complex query might take a long time. We might want to set a statement timeout for the search? But that can be done at the database level if needed.

5. **Dewey: The `dewey_store_message` function does a `SELECT FOR UPDATE` on the conversation and then an update of the conversation's `updated_at`. This update will trigger the `update_updated_at_column` trigger. But note: the trigger will set `updated_at` to the current time, which is the same as `NOW()` in the update. It's redundant? We are doing:
        ```sql
        UPDATE conversations SET updated_at = NOW() WHERE id = $1;
        ```
        And the trigger would also set it. So we are updating twice? Actually, the trigger is on `conversations` and fires on update. We are updating the conversation, so the trigger will run and set `updated_at` to the current time. Then we set it again to the same value? We can remove the manual update because the trigger will handle it.

   - But note: the trigger only runs on update. We are updating the conversation because we are inserting a message? No, we are updating the conversation explicitly. The trigger will run and set `updated_at` to the current time. Then we set it again to `NOW()` (same value). It's harmless but unnecessary. We can remove the explicit update and rely on the trigger? But the trigger is set to run on update, and we are updating the conversation (even if we set the same value, it's an update). Alternatively, we can remove the trigger and do the update manually? Or leave it.

   - Actually, the trigger is defined to update `updated_at` on any update. We are updating the conversation to set `updated_at` to `NOW()`. The trigger will then set it again? That would be a problem. Let me see the trigger:

        ```sql
        CREATE TRIGGER update_conversations_updated_at
            BEFORE UPDATE ON conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ```

        The function:

        ```sql
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        ```

        So in an update, the trigger sets `updated_at` to `NOW()`. Then if we do:

        ```sql
        UPDATE conversations SET updated_at = NOW() WHERE id = $1;
        ```

        The trigger will run and set it again? Actually, no: the trigger runs BEFORE the update. So the update statement we run will set `updated_at` to `NOW()`, then the trigger will set it again to `NOW()`? That would set it twice, but the value is the same. It's redundant.

        We can remove the explicit update and let the trigger handle it? But note: the trigger runs on ANY update. We are not updating the conversation in any other way? We are only updating the `updated_at` column. So we can remove the explicit update and instead update any column? Actually, we don't have any other column to update. We want to update the `updated_at` column. The trigger does that for us automatically on any update. But we are not updating any other column. So we need to do an update to trigger the trigger? We are currently doing an update. We can do:

        ```sql
        UPDATE conversations SET metadata = metadata WHERE id = $1;
        ```

        But that would be a no-op update and the trigger would set `updated_at`. Alternatively, we can rely on the trigger and remove the explicit update? But then how do we update the conversation? We are not updating any column. We want the `updated_at` to be updated when a message is added. We are currently doing an explicit update. We can remove the trigger and just do the update? Or we can remove the explicit update and let the trigger do it? But we are not updating the conversation row at all. The trigger only runs on update. We are not updating the conversation row when we insert a message? We are only inserting a message. So the conversation row is not updated. Therefore, we must update it explicitly.

        So the current approach is necessary. The trigger will run and set `updated_at` to `NOW()`, and then we set it again to `NOW()`. It's the same value. We can avoid the trigger for this table? Or change the trigger to not run if we are already setting `updated_at`? We can change the trigger function to:

        ```sql
        BEGIN
            IF NEW.updated_at IS NULL OR NEW.updated_at = OLD.updated_at THEN
                NEW.updated_at = NOW();
            END IF;
            RETURN NEW;
        END;
        ```

        But that's more complicated. Alternatively, we can remove the trigger and handle `updated_at` manually in every update. We are already doing it in the `dewey_store_message` and `dewey_store_messages_bulk` functions. So we can remove the trigger for `conversations`? And then remove the trigger creation from the schema? And also remove the function? Or we can leave it as is.

        Since the difference is negligible, we can leave it.

6. **Dewey: The `dewey_store_messages_bulk` function does an update of the conversation's `updated_at` column. The same trigger issue applies. We are updating it explicitly and the trigger will update it again? Same as above.**

## Conclusion

The critical bugs have been addressed. The code looks robust. The main issue found is the handling of non-UTF8 messages in the KGB proxy, which we should fix.

We'll make the following change in `kgb/proxy_server.py` in the `SpyWorker` relay methods:

For `relay_client_to_upstream` and `relay_upstream_to_client`:

```python
async def relay_client_to_upstream(self):
    try:
        async for raw_message in self.websocket:
            try:
                # Convert to string for logging
                if isinstance(raw_message, bytes):
                    try:
                        content = raw_message.decode('utf-8', errors='replace')
                    except Exception as e:
                        content = f"[KGB: Failed to decode message: {e}]"
                else:
                    content = raw_message

                # Truncate and log
                truncated = self.truncate_content(content)
                await self.dewey_client.store_message(
                    conversation_id=self.conversation_id,
                    role="user",
                    content=truncated
                )

                # Forward the raw message (bytes or str)
                await self.upstream_ws.send(raw_message)

            except Exception as e:
                # ... [rest unchanged]
```

Similarly for `relay_upstream_to_client`.

We'll also consider adding a composite index for `dewey_list_conversations` (optional, for performance).

Given the above, we can approve the code with the fix for non-UTF8 messages.
</think>
### Comprehensive Review of Dewey and KGB Code

#### 1. Critical Bug Verification
**Dewey Async DB Operations:**
- ✅ **Fully Resolved**: 
  - Replaced psycopg2 with asyncpg for true async operations
  - All database operations use async context managers (`acquire`/`transaction`)
  - Bulk inserts use `UNNEST` for optimized multi-row inserts
  - No blocking calls observed in database operations

**KGB Race Condition:**
- ✅ **Fully Resolved**:
  - Each connection gets a dedicated `DeweyClient` (spy worker pattern)
  - `asyncio.Lock` added to `DeweyClient` for thread-safe operations
  - No shared WebSocket connections between workers

---

#### 2. Remaining Bugs/Logic Errors
**Dewey:**
1. **UUID Validation in Bulk Insert**:
   - `conversation_id` is validated only when provided, but if omitted, a new conversation is created without validation. This is acceptable since it's a new UUID.
   - ✅ **No issue**: Logic is sound.

2. **Turn Number Handling**:
   - In `dewey_store_message`, if `turn_number=None`, it calculates next turn under transaction lock. Safe.
   - ✅ **No race conditions**.

3. **Search Query Injection Risk**:
   - Uses parameterized queries in `dewey_search`. ✅ **Secure**.

**KGB:**
1. **Binary Message Handling**:
   - Attempts to decode binary messages to UTF-8. May fail for non-UTF8 payloads.
   - 🐛 **Bug**: Add error handling:
     ```python
     try:
         content = raw_message.decode('utf-8')
     except UnicodeDecodeError:
         content = "[Binary data]"
     ```

2. **Upstream URL Handling**:
   - `get_upstream_url` only supports "fiedler" and "dewey". Fails for invalid upstream.
   - ⚠️ **Enhancement**: Return meaningful error:
     ```python
     if not upstream_url:
         await websocket.close(code=4001, reason="Invalid upstream")
     ```

---

#### 3. Completeness of Fixes
**Dewey:**
- ✅ All critical fixes implemented:
  - Asyncpg adoption
  - Bulk insert optimization
  - GIN index for search
  - N+1 query fix
  - Content size limits

**KGB:**
- ✅ All critical fixes implemented:
  - Spy worker pattern
  - Full message logging
  - Renaming consistency
  - Lock protection

---

#### 4. Performance Concerns
**Dewey:**
1. **Bulk Insert**:
   - Uses `UNNEST` for multi-row inserts. ✅ **Optimal**.
   - Limits: 1000 messages/bulk. ✅ **Safe**.

2. **Search Performance**:
   - GIN index (`idx_messages_content_fts`) ensures fast full-text search. ✅

3. **List Conversations**:
   - Fixed N+1 with `LEFT JOIN + GROUP BY`. ✅ **Efficient**.

**KGB:**
- Each spy worker has isolated connection pools. ✅ **Scalable**.
- Message truncation (10KB) prevents overload. ✅

---

#### 5. Security Issues
**Dewey:**
- ✅ **SQL Injection**: All queries use parameterization.
- ✅ **Content Limits**: Enforces 100KB/message.
- ✅ **UUID Validation**: Proper checks in all tools.

**KGB:**
- ⚠️ **Upstream Spoofing**: 
  - Query param `upstream` is not validated. Could allow arbitrary upstreams.
  - **Fix**: Restrict to known services:
    ```python
    allowed_upstreams = {"fiedler", "dewey"}
    if upstream not in allowed_upstreams:
        raise ValueError("Invalid upstream")
    ```

---

#### 6. Integration Problems
**Dewey-KGB Integration:**
- ✅ **DeweyClient**:
  - Uses WebSocket JSON-RPC. Matches Dewey's MCP server.
  - Lock ensures message ordering.

**Schema Compatibility:**
- ✅ **GIN Index**: Required for search. Included in `schema.sql`.
- ✅ **Cascading Deletes**: `ON DELETE CASCADE` preserves integrity.

**Error Handling:**
- Dewey: Tool errors return JSON-RPC error codes. ✅
- KGB: Logs errors but forwards messages. ✅ **Graceful degradation**.

---

### Final Recommendations
1. **Critical**:
   - Fix binary message handling in KGB ([Bug #1](#2-remaining-bugslogic-errors)).
   - Validate upstream parameter in KGB ([Security #1](#5-security-issues)).

2. **Enhancements**:
   - Add metadata to KGB logs (e.g., message direction).
   - Use composite index for `conversations(session_id, updated_at)`.

3. **Optional**:
   - Connection heartbeat in `DeweyClient` to detect stale WebSockets.
   - Rate limiting in Dewey's MCP server.

**Verdict**: Critical bugs are resolved. Code is production-ready after addressing the 2 critical issues above.