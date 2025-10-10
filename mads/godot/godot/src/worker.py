"""
Godot Worker - Consumes logs from Redis and sends to Dewey
Based on Gemini-2.5-Pro recommendation (correlation_id: b5afd3b0)
"""
import asyncio
import json
import time
import redis.asyncio as redis
from joshua_logger import Logger

import config
from mcp_client import MCPClient

logger = Logger()

async def send_batch_to_dewey(mcp_client, batch):
    """Sends a batch of logs to Dewey with exponential backoff retry (REQ-REL-002)"""
    if not batch:
        return

    log_entries = [json.loads(item) for item in batch]

    delay = config.RETRY_INITIAL_DELAY
    for attempt in range(config.RETRY_MAX_ATTEMPTS):
        try:
            if not mcp_client.is_connected:
                await logger.log("WARN", "Dewey client disconnected. Attempting to reconnect...", "godot-worker")
                await mcp_client.connect()
                await logger.log("INFO", "Reconnected to Dewey.", "godot-worker")

            await logger.log("INFO", f"Sending batch of {len(log_entries)} logs to Dewey.", "godot-worker")
            await mcp_client.call_tool("dewey_store_logs_batch", {"logs": log_entries})
            await logger.log("INFO", f"Successfully sent batch of {len(log_entries)} logs.", "godot-worker")
            return
        except Exception as e:
            await logger.log("ERROR", f"Attempt {attempt + 1} failed to send batch to Dewey: {e}", "godot-worker")
            if attempt + 1 == config.RETRY_MAX_ATTEMPTS:
                await logger.log("ERROR", "Max retries reached. Discarding batch.", "godot-worker")
                break

            await logger.log("INFO", f"Retrying in {delay} seconds...", "godot-worker")
            await asyncio.sleep(delay)
            delay = min(delay * 2, config.RETRY_MAX_DELAY)

async def main():
    """Main worker loop - consumes logs from Redis and sends to Dewey"""
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    mcp_client = MCPClient(config.DEWEY_MCP_URL, timeout=config.DEWEY_CONNECT_TIMEOUT)

    await logger.log("INFO", "Godot worker starting...", "godot-worker")
    await logger.log("INFO", f"Connecting to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}", "godot-worker")
    await logger.log("INFO", f"Connecting to Dewey at {config.DEWEY_MCP_URL}", "godot-worker")

    await mcp_client.connect()

    while True:
        try:
            batch = []
            start_time = time.monotonic()

            # REQ-GOD-002: Batch of 100 logs or 100ms timeout, whichever first
            while len(batch) < config.BATCH_SIZE and (time.monotonic() - start_time) * 1000 < config.BATCH_TIMEOUT_MS:
                try:
                    timeout = max(0.1, (config.BATCH_TIMEOUT_MS / 1000))
                    result = await redis_client.brpop(config.LOG_QUEUE_NAME, timeout=timeout)
                    if result:
                        _, item = result
                        batch.append(item)
                    else:
                        break
                except redis.ConnectionError as e:
                    await logger.log("ERROR", f"Redis connection error: {e}. Retrying in 5 seconds...", "godot-worker")
                    await asyncio.sleep(5)
                    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
                    break

            if batch:
                await send_batch_to_dewey(mcp_client, batch)

            # REQ-GOD-005: Enforce FIFO drop policy - keep newest 100,000
            await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)

        except Exception as e:
            await logger.log("ERROR", f"Unhandled exception in main worker loop: {e}", "godot-worker")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
