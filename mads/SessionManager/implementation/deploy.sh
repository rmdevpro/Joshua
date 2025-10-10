#!/bin/bash

# SessionManager Blue/Green Deployment Script
# Usage: ./deploy.sh [blue|green]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to blue if not specified
DEPLOYMENT_COLOR=${1:-blue}

if [[ "$DEPLOYMENT_COLOR" != "blue" && "$DEPLOYMENT_COLOR" != "green" ]]; then
    echo -e "${RED}Error: Deployment color must be 'blue' or 'green'${NC}"
    exit 1
fi

echo -e "${BLUE}=== SessionManager Blue/Green Deployment ===${NC}"
echo -e "Deploying to: ${GREEN}$DEPLOYMENT_COLOR${NC}"

# Step 1: Build Docker image
echo -e "\n${BLUE}Step 1: Building Docker image...${NC}"
docker build -t sessionmanager:latest .

# For local Kubernetes (minikube/kind), load the image
if command -v minikube &> /dev/null; then
    echo "Loading image into Minikube..."
    minikube image load sessionmanager:latest
elif command -v kind &> /dev/null; then
    echo "Loading image into Kind..."
    kind load docker-image sessionmanager:latest
fi

# Step 2: Create namespaces
echo -e "\n${BLUE}Step 2: Creating namespaces...${NC}"
kubectl apply -f k8s/namespace.yaml

# Step 3: Check if secrets exist
echo -e "\n${BLUE}Step 3: Checking secrets...${NC}"
if ! kubectl get secret sessionmanager-secrets -n sessionmanager &> /dev/null; then
    echo -e "${RED}Warning: Secrets not found. Please create k8s/secrets.yaml from template${NC}"
    echo "Copy k8s/secrets-template.yaml to k8s/secrets.yaml and fill in values"
    exit 1
fi

# Step 4: Deploy infrastructure (Redis, MongoDB)
echo -e "\n${BLUE}Step 4: Deploying infrastructure services...${NC}"
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/mongodb.yaml

# Wait for infrastructure to be ready
echo "Waiting for Redis and MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n sessionmanager --timeout=60s
kubectl wait --for=condition=ready pod -l app=mongodb -n sessionmanager --timeout=60s

# Step 5: Deploy to the specified color
echo -e "\n${BLUE}Step 5: Deploying SessionManager to $DEPLOYMENT_COLOR environment...${NC}"
kubectl apply -f k8s/deployment-${DEPLOYMENT_COLOR}.yaml

# Wait for deployment to be ready
echo "Waiting for SessionManager pods to be ready..."
kubectl wait --for=condition=ready pod -l app=sessionmanager,version=${DEPLOYMENT_COLOR} \
    -n sessionmanager-${DEPLOYMENT_COLOR} --timeout=120s

# Step 6: Check deployment status
echo -e "\n${BLUE}Step 6: Checking deployment status...${NC}"
kubectl get pods -n sessionmanager-${DEPLOYMENT_COLOR}

# Step 7: Run smoke test
echo -e "\n${BLUE}Step 7: Running smoke test...${NC}"
# Port forward for testing
kubectl port-forward -n sessionmanager-${DEPLOYMENT_COLOR} \
    service/sessionmanager-${DEPLOYMENT_COLOR} 8080:80 &
PF_PID=$!
sleep 5

# Test health endpoint
if curl -s http://localhost:8080/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    kill $PF_PID
    exit 1
fi

kill $PF_PID

# Step 8: Switch traffic (if tests pass)
echo -e "\n${BLUE}Step 8: Ready to switch traffic to $DEPLOYMENT_COLOR${NC}"
echo "To switch traffic, update k8s/router-service.yaml selector.version to '$DEPLOYMENT_COLOR'"
echo "Then run: kubectl apply -f k8s/router-service.yaml"

echo -e "\n${GREEN}=== Deployment to $DEPLOYMENT_COLOR completed successfully ===${NC}"

# Display useful commands
echo -e "\n${BLUE}Useful commands:${NC}"
echo "  View pods:        kubectl get pods -n sessionmanager-${DEPLOYMENT_COLOR}"
echo "  View logs:        kubectl logs -n sessionmanager-${DEPLOYMENT_COLOR} -l app=sessionmanager"
echo "  Port forward:     kubectl port-forward -n sessionmanager-${DEPLOYMENT_COLOR} service/sessionmanager-${DEPLOYMENT_COLOR} 8080:80"
echo "  Switch traffic:   Edit k8s/router-service.yaml and apply"
echo "  Rollback:         ./deploy.sh [blue|green] (deploy to other color)"