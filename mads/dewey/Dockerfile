FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY dewey/ ./dewey/
COPY schema.sql .

# Expose MCP port
EXPOSE 9020

# Run MCP server
CMD ["python", "-m", "dewey.mcp_server"]
