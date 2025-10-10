#!/bin/bash

# Sergey MAD Startup Script

echo "Starting Sergey Google Workspace MAD..."

# Build the container
docker compose build

# Start the container
docker compose up -d

# Wait for startup
echo "Waiting for Sergey to start..."
sleep 5

# Check if running
if docker ps | grep -q sergey-mcp; then
    echo "✅ Sergey MAD started successfully on port 8095"
    echo ""
    echo "To add to MCP relay:"
    echo "  relay_add_server(name='sergey', url='ws://localhost:8095')"
    echo ""
    echo "To view logs:"
    echo "  docker logs -f sergey-mcp"
else
    echo "❌ Failed to start Sergey MAD"
    echo "Check logs: docker-compose logs sergey-mcp"
    exit 1
fi