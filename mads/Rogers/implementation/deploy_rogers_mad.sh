#!/bin/bash
# Deploy Rogers MAD on Irina with correct architecture
# Phase 1: Basic Thought Engine + Strong Action Engine

set -e

echo "=============================================="
echo "   Deploying Rogers MAD - Phase 1"
echo "   Thought Engine + Action Engine"
echo "=============================================="

# Configuration
IRINA_HOST="192.168.1.210"
IRINA_USER="aristotle9"
IRINA_PASS="Edgar01760"
DEPLOYMENT_PATH="/mnt/projects/Joshua/mads/Rogers"

# Function to run commands on Irina
run_on_irina() {
    sshpass -p "$IRINA_PASS" ssh -o StrictHostKeyChecking=no ${IRINA_USER}@${IRINA_HOST} "$1"
}

# Function to copy files to Irina
copy_to_irina() {
    sshpass -p "$IRINA_PASS" scp -r -o StrictHostKeyChecking=no "$1" ${IRINA_USER}@${IRINA_HOST}:"$2"
}

echo ""
echo "Step 1: Copying Rogers MAD files to Irina"
echo "------------------------------------------"

# Copy all Rogers files
copy_to_irina "/mnt/projects/Joshua/mads/Rogers/*" "$DEPLOYMENT_PATH/"

echo "Files copied successfully"

echo ""
echo "Step 2: Building Rogers MAD container"
echo "--------------------------------------"

run_on_irina "cd $DEPLOYMENT_PATH/implementation && \
    docker build -f Dockerfile.rogers -t rogers-mad:phase1 ."

echo ""
echo "Step 3: Stopping old SessionManager deployment"
echo "-----------------------------------------------"

run_on_irina "cd $DEPLOYMENT_PATH/implementation && \
    docker-compose down || true"

echo ""
echo "Step 4: Starting Rogers MAD with new architecture"
echo "--------------------------------------------------"

run_on_irina "cd $DEPLOYMENT_PATH/implementation && \
    docker-compose -f docker-compose-rogers.yml up -d"

echo ""
echo "Step 5: Verifying deployment"
echo "-----------------------------"

sleep 5  # Give services time to start

# Check health
echo "Checking Rogers health..."
curl -s http://${IRINA_HOST}:8000/health | python3 -m json.tool || echo "Health check pending..."

# Check conversation interface
echo ""
echo "Testing conversation interface..."
curl -s -X POST http://${IRINA_HOST}:8090/conversation \
    -H "Content-Type: application/json" \
    -d '{
        "from_mad": "Deployment-Test",
        "content": "Rogers, are you ready for conversations?"
    }' | python3 -m json.tool || echo "Conversation interface starting..."

echo ""
echo "Step 6: Deployment status"
echo "-------------------------"

run_on_irina "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep rogers"

echo ""
echo "=============================================="
echo "   Rogers MAD Deployment Complete!"
echo "=============================================="
echo ""
echo "Architecture deployed:"
echo "- Thought Engine: Basic (Imperator + rogers.md)"
echo "- Action Engine: Strong (3-tier storage)"
echo "- Phase: 1 (Foundation for DER/CET evolution)"
echo ""
echo "Endpoints:"
echo "- Health: http://${IRINA_HOST}:8000/health"
echo "- Conversations: http://${IRINA_HOST}:8090/conversation"
echo "- MCP Control: http://${IRINA_HOST}:8080/mcp/command"
echo "- Traditional API: http://${IRINA_HOST}:8000/api/v1/sessions"
echo ""
echo "Next steps:"
echo "1. Test MAD-to-MAD conversations"
echo "2. Monitor interaction logs"
echo "3. Prepare for Phase 2 (DER integration)"
echo ""
echo "Example test conversation:"
echo 'curl -X POST http://192.168.1.210:8090/conversation \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"from_mad": "Dewey", "content": "Rogers, create a session for user123"}'"'"