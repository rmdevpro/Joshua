FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY sergey_server.py .
COPY godot/ ./godot/

# Create config and data directories
RUN mkdir -p /config /data

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV SERGEY_PORT=8095
ENV GOOGLE_SERVICE_ACCOUNT_PATH=/config/google-service-account-credentials.json
ENV GODOT_URL=ws://godot-mcp:8060

# Run the server
CMD ["python", "sergey_server.py"]