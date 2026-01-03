#!/bin/bash
# Docker deployment script for Neural Mesh Pipeline

set -e

echo "========================================="
echo "Neural Mesh Pipeline - Docker Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

print_status "Docker found: $(docker --version)"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

print_status "docker-compose found"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning ".env file created from template."
        print_warning "Please edit .env and add your OPENAI_API_KEY before continuing."
        read -p "Press Enter after you've configured .env file..."
    else
        print_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    print_status ".env file exists"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/storage data/logs src/tests
print_status "Data directories created"

# Build Docker image
echo ""
echo "Building Docker image..."
if docker compose version &> /dev/null; then
    docker compose build
else
    docker-compose build
fi
print_status "Docker image built"

# Start services
echo ""
echo "Starting services..."
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi
print_status "Services started"

# Wait for container to be healthy
echo ""
echo "Waiting for container to be healthy..."
sleep 5

# Detect which docker-compose command to use
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    CONTAINER_STATUS=$(docker compose ps -q neural-mesh-pipeline | xargs docker inspect -f '{{.State.Status}}')
else
    DOCKER_COMPOSE_CMD="docker-compose"
    CONTAINER_STATUS=$(docker-compose ps -q neural-mesh-pipeline | xargs docker inspect -f '{{.State.Status}}')
fi

if [ "$CONTAINER_STATUS" == "running" ]; then
    print_status "Container is running"
else
    print_warning "Container status: $CONTAINER_STATUS"
fi

echo ""
echo "========================================="
print_status "Deployment complete!"
echo "========================================="
echo ""
echo "Container name: neural-mesh-pipeline"
echo ""
echo "Useful commands:"
echo "  View logs:       docker logs -f neural-mesh-pipeline"
echo "  Stop services:   $DOCKER_COMPOSE_CMD down"
echo "  Restart:         $DOCKER_COMPOSE_CMD restart"
echo "  View status:     $DOCKER_COMPOSE_CMD ps"
echo "  Enter container: docker exec -it neural-mesh-pipeline bash"
echo ""
echo "Data locations:"
echo "  Logs:    ./data/logs"
echo "  State:   ./data/storage"
echo "  Source:  ./src"
echo ""
