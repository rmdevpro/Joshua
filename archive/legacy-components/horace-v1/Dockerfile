# Dockerfile
FROM python:3.11-alpine

# Install system dependencies for python-magic and fcntl
RUN apk add --no-cache libmagic build-base

WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose the MCP port
EXPOSE 8070

# Run the server (v2 uses iccm-network library)
# Install iccm-network from mounted volume, then start server
CMD ["sh", "-c", "pip install -e /app/iccm-network && python -m src.mcp_server_v2"]
