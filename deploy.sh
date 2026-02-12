#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NAMESPACE="microservices"
IMAGE_NAME="registry.experioservices.com/stargate"
VERSION=${1:-1.0.0}

echo -e "${BLUE}Building and deploying stargate...${NC}"
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo ""

# Build Docker image
echo -e "${BLUE}[1/4] Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${VERSION} .

# Push to registry
echo -e "${BLUE}[2/4] Pushing to registry...${NC}"
docker push ${IMAGE_NAME}:${VERSION}

# Update deployment with new image if not 1.0.0
if [ "$VERSION" != "1.0.0" ]; then
    echo -e "${BLUE}[3/4] Updating deployment with version ${VERSION}...${NC}"
    sed "s|image: registry.experioservices.com/stargate:1.0.0|image: registry.experioservices.com/stargate:${VERSION}|g" k8s-manifests.yaml > k8s-manifests-${VERSION}.yaml
    kubectl apply -f k8s-manifests-${VERSION}.yaml
    rm k8s-manifests-${VERSION}.yaml
else
    echo -e "${BLUE}[3/4] Applying deployment...${NC}"
    kubectl apply -f k8s-manifests.yaml
fi

# Wait for rollout
echo -e "${BLUE}[4/4] Waiting for deployment to complete...${NC}"
kubectl rollout status deployment/stargate -n ${NAMESPACE} --timeout=300s

echo ""
echo -e "${GREEN}✅ stargate deployed successfully!${NC}"
echo ""