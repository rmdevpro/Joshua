FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install joshua_network library
COPY --chown=root:root lib/joshua_network /tmp/joshua-network-install/joshua_network
COPY --chown=root:root lib/pyproject.toml /tmp/joshua-network-install/
RUN pip install --no-cache-dir /tmp/joshua-network-install && rm -rf /tmp/joshua-network-install

# Copy project files
COPY mads/fiedler/pyproject.toml .
COPY mads/fiedler/fiedler/ ./fiedler/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir tiktoken

# Create output directory
RUN mkdir -p /app/fiedler_output && chmod 777 /app/fiedler_output

# Expose MCP server port and HTTP streaming proxy port
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run Fiedler MCP server with unbuffered output (joshua_network implementation)
CMD ["python", "-u", "-m", "fiedler.server_joshua"]
