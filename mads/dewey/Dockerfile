FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install joshua libraries (joshua_network + joshua_logger)
COPY --chown=root:root lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY --chown=root:root lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY --chown=root:root lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Install Python dependencies
COPY mads/dewey/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mads/dewey/dewey/ ./dewey/
COPY mads/dewey/schema.sql .

# Expose MCP port
EXPOSE 9020

# Run MCP server
CMD ["python", "-m", "dewey.mcp_server"]
