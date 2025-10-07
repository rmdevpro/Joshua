# Godot Unified Logging Infrastructure - Synthesized Implementation
# Base: Gemini-2.5-Pro with refinements from DeepSeek-R1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y redis-server supervisor procps && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY src/ /app/src/
COPY redis.conf /etc/redis/redis.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Install Python dependencies
# Note: No official MCP Python library yet, will implement WebSocket server directly
RUN pip install --no-cache-dir "redis>=5.0" "websockets>=14.0" "httpx>=0.25.0" "asyncpg>=0.29"

# Expose MCP Server port (Redis is internal only)
EXPOSE 9060

# Copy iccm-network library and start via supervisord
CMD ["sh", "-c", "cp -r /app/iccm-network/iccm_network /app/ && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
