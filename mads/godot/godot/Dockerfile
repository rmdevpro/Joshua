# Godot Unified Logging Infrastructure - Synthesized Implementation
# Base: Gemini-2.5-Pro with refinements from DeepSeek-R1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y redis-server supervisor procps && rm -rf /var/lib/apt/lists/*

# Copy and install joshua-libs (joshua_network + joshua_logger)
# Note: Godot uses joshua_logger to log to itself - this is fine, not circular!
COPY --chown=root:root lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY --chown=root:root lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY --chown=root:root lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Install Python dependencies
RUN pip install --no-cache-dir "redis>=5.0" "websockets>=14.0" "httpx>=0.25.0" "asyncpg>=0.29"

# Copy application code
COPY mads/godot/godot/src/ /app/src/
COPY mads/godot/godot/redis.conf /etc/redis/redis.conf
COPY mads/godot/godot/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose MCP Server port (Redis is internal only)
EXPOSE 9060

# Start via supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
