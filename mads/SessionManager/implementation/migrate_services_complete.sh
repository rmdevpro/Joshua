#!/bin/bash
# Complete migration script for heavy services from Pharaoh to Irina
# Includes image transfer and deployment

set -e

echo "=============================================="
echo "Complete Migration: Heavy Services to Irina"
echo "=============================================="

# Configuration
IRINA_HOST="192.168.1.210"
IRINA_USER="aristotle9"
IRINA_PASS="Edgar01760"

# Function to run commands on Irina
run_on_irina() {
    sshpass -p "$IRINA_PASS" ssh -o StrictHostKeyChecking=no ${IRINA_USER}@${IRINA_HOST} "$1"
}

# Function to copy files to Irina
copy_to_irina() {
    sshpass -p "$IRINA_PASS" scp -o StrictHostKeyChecking=no "$1" ${IRINA_USER}@${IRINA_HOST}:"$2"
}

echo ""
echo "Phase 1: Export Docker images from Pharaoh"
echo "-------------------------------------------"

mkdir -p /tmp/docker-images

# Export Dewey image
echo "Exporting dewey-mcp image..."
docker save dewey-mcp-blue:latest -o /tmp/docker-images/dewey-mcp.tar || \
    docker save dewey-mcp:latest -o /tmp/docker-images/dewey-mcp.tar || \
    echo "Warning: Could not export Dewey image"

# Export Horace image
echo "Exporting horace-mcp image..."
docker save horace-nas-v2-horace-mcp:latest -o /tmp/docker-images/horace-mcp.tar || \
    echo "Warning: Could not export Horace image"

# Export Godot image
echo "Exporting godot-mcp image..."
docker save godot-godot:latest -o /tmp/docker-images/godot-mcp.tar || \
    docker save godot-mcp:latest -o /tmp/docker-images/godot-mcp.tar || \
    echo "Warning: Could not export Godot image"

# Export Fiedler image
echo "Exporting fiedler-mcp image..."
docker save fiedler-mcp:latest -o /tmp/docker-images/fiedler-mcp.tar || \
    echo "Warning: Could not export Fiedler image"

echo ""
echo "Phase 2: Transfer images to Irina"
echo "-------------------------------------------"

# Create directory on Irina
run_on_irina "mkdir -p /tmp/docker-images"

# Transfer images
for image in dewey-mcp.tar horace-mcp.tar godot-mcp.tar fiedler-mcp.tar; do
    if [ -f "/tmp/docker-images/$image" ]; then
        echo "Transferring $image to Irina..."
        copy_to_irina "/tmp/docker-images/$image" "/tmp/docker-images/"
    fi
done

echo ""
echo "Phase 3: Load images on Irina"
echo "-------------------------------------------"

for image in dewey-mcp.tar horace-mcp.tar godot-mcp.tar fiedler-mcp.tar; do
    if run_on_irina "[ -f /tmp/docker-images/$image ]"; then
        echo "Loading $image on Irina..."
        run_on_irina "docker load -i /tmp/docker-images/$image"
    fi
done

echo ""
echo "Phase 4: Deploy services on Irina"
echo "-------------------------------------------"

# Deploy Dewey
echo "Deploying Dewey..."
run_on_irina "docker stop dewey-mcp 2>/dev/null || true"
run_on_irina "docker rm dewey-mcp 2>/dev/null || true"
run_on_irina "docker run -d \\
    --name dewey-mcp \\
    --restart unless-stopped \\
    --network host \\
    -e POSTGRES_CONNECTION_STRING='postgresql://dewey_user:dewey_pass@localhost/dewey_db' \\
    -e MCP_LOG_LEVEL=INFO \\
    -v /mnt/irina_storage/dewey:/data \\
    dewey-mcp:latest"

# Deploy Horace
echo "Deploying Horace..."
run_on_irina "docker stop horace-mcp 2>/dev/null || true"
run_on_irina "docker rm horace-mcp 2>/dev/null || true"
run_on_irina "docker run -d \\
    --name horace-mcp \\
    --restart unless-stopped \\
    --network host \\
    -e STORAGE_PATH=/mnt/irina_storage \\
    -v /mnt/irina_storage:/mnt/irina_storage \\
    horace-nas-v2-horace-mcp:latest"

# Deploy Godot
echo "Deploying Godot..."
run_on_irina "docker stop godot-mcp 2>/dev/null || true"
run_on_irina "docker rm godot-mcp 2>/dev/null || true"
run_on_irina "docker run -d \\
    --name godot-mcp \\
    --restart unless-stopped \\
    --network host \\
    -e LOG_STORAGE_PATH=/data/logs \\
    -v /mnt/irina_storage/godot:/data/logs \\
    godot-godot:latest"

# Deploy Fiedler
echo "Deploying Fiedler..."
run_on_irina "docker stop fiedler-mcp 2>/dev/null || true"
run_on_irina "docker rm fiedler-mcp 2>/dev/null || true"
run_on_irina "docker run -d \\
    --name fiedler-mcp \\
    --restart unless-stopped \\
    --network host \\
    -e FIEDLER_CONFIG_PATH=/config \\
    -v /mnt/irina_storage/fiedler:/config \\
    fiedler-mcp:latest"

echo ""
echo "Phase 5: Verify deployment"
echo "-------------------------------------------"

run_on_irina "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "Phase 6: Clean up"
echo "-------------------------------------------"

# Clean up temporary files
rm -rf /tmp/docker-images
run_on_irina "rm -rf /tmp/docker-images"

echo ""
echo "=============================================="
echo "Migration Complete!"
echo "=============================================="
echo ""
echo "Services migrated to Irina ($IRINA_HOST):"
echo "- Dewey (conversation storage)"
echo "- Horace (file management)"
echo "- Godot (logging)"
echo "- Fiedler (multi-model orchestration)"
echo ""
echo "Next steps:"
echo "1. Update relay configuration (/home/aristotle9/mcp-relay/backends.yaml)"
echo "2. Test service connectivity"
echo "3. Stop old services on Pharaoh"
echo "4. Update documentation"