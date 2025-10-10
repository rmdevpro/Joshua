#!/bin/bash
# Migration script for heavy services from Pharaoh to Irina
# Part of optimal hardware distribution strategy

echo "========================================"
echo "Migrating Heavy Services to Irina"
echo "========================================"

# Configuration
IRINA_HOST="192.168.1.210"
IRINA_USER="aristotle9"
IRINA_PASS="Edgar01760"

# Function to run commands on Irina
run_on_irina() {
    sshpass -p "$IRINA_PASS" ssh -o StrictHostKeyChecking=no ${IRINA_USER}@${IRINA_HOST} "$1"
}

echo ""
echo "1. Deploying Dewey (Conversation Storage) on Irina..."
echo "---------------------------------------"

# Deploy Dewey on Irina
run_on_irina "docker run -d \\
    --name dewey-mcp \\
    --restart unless-stopped \\
    -p 9022:9020 \\
    -e POSTGRES_CONNECTION_STRING='postgresql://dewey_user:dewey_pass@localhost/dewey_db' \\
    -e MCP_LOG_LEVEL=INFO \\
    -v /mnt/irina_storage/dewey:/data \\
    dewey:latest || echo 'Dewey deployment skipped (may already exist)'"

echo ""
echo "2. Deploying Horace (File Management) on Irina..."
echo "---------------------------------------"

# Deploy Horace on Irina - needs access to 60TB storage
run_on_irina "docker run -d \\
    --name horace-mcp \\
    --restart unless-stopped \\
    -p 9070:9070 \\
    -e STORAGE_PATH=/mnt/irina_storage \\
    -v /mnt/irina_storage:/mnt/irina_storage \\
    horace:latest || echo 'Horace deployment skipped (may already exist)'"

echo ""
echo "3. Deploying Godot (Logger) on Irina..."
echo "---------------------------------------"

# Deploy Godot on Irina
run_on_irina "docker run -d \\
    --name godot-mcp \\
    --restart unless-stopped \\
    -p 9060:9060 \\
    -e LOG_STORAGE_PATH=/data/logs \\
    -v /mnt/irina_storage/godot:/data/logs \\
    godot:latest || echo 'Godot deployment skipped (may already exist)'"

echo ""
echo "4. Deploying Fiedler (Multi-Model Orchestration) on Irina..."
echo "---------------------------------------"

# Deploy Fiedler on Irina - benefits from more RAM
run_on_irina "docker run -d \\
    --name fiedler-mcp \\
    --restart unless-stopped \\
    -p 9010:8080 \\
    -p 9011:8081 \\
    -e FIEDLER_CONFIG_PATH=/config \\
    -v /mnt/irina_storage/fiedler:/config \\
    fiedler:latest || echo 'Fiedler deployment skipped (may already exist)'"

echo ""
echo "5. Checking deployed services on Irina..."
echo "---------------------------------------"

run_on_irina "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'dewey|horace|godot|fiedler|session'"

echo ""
echo "========================================"
echo "Migration Status Check Complete"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Update MCP relay configuration to point to Irina endpoints"
echo "2. Test connectivity to migrated services"
echo "3. Stop services on Pharaoh once Irina services verified"
echo "4. Update documentation with new service locations"