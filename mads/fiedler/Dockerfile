FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY fiedler/ ./fiedler/

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

# Run Fiedler MCP server with unbuffered output
CMD ["python", "-u", "-m", "fiedler.server"]
