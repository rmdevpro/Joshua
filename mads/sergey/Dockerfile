FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install joshua-libs (joshua_network + joshua_logger)
COPY lib/joshua_network /tmp/joshua-libs-install/joshua_network
COPY lib/joshua_logger /tmp/joshua-libs-install/joshua_logger
COPY lib/pyproject.toml /tmp/joshua-libs-install/
RUN pip install --no-cache-dir /tmp/joshua-libs-install && rm -rf /tmp/joshua-libs-install

# Copy requirements first for better caching
COPY mads/sergey/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY mads/sergey/sergey_server.py .

# Create config and data directories
RUN mkdir -p /config /data

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV SERGEY_PORT=8095
ENV GOOGLE_SERVICE_ACCOUNT_PATH=/config/google-service-account-credentials.json
ENV GODOT_URL=ws://godot-mcp:9060
ENV LOGGING_ENABLED=true

# Run the server
CMD ["python", "sergey_server.py"]