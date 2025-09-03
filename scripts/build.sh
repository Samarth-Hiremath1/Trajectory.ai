#!/bin/bash

# Build script for GoalTrajectory.AI container images
# Usage: ./scripts/build.sh [environment] [service]
# Environment: dev, prod (default: dev)
# Service: backend, frontend, all (default: all)

set -e

# Configuration
ENVIRONMENT=${1:-dev}
SERVICE=${2:-all}
REGISTRY=${REGISTRY:-"goaltrajectory"}
TAG=${TAG:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be 'dev' or 'prod'"
        exit 1
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Build backend image
build_backend() {
    log_info "Building backend image for $ENVIRONMENT environment..."
    
    local dockerfile="backend/Dockerfile"
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        dockerfile="backend/Dockerfile.prod"
    fi
    
    if [[ ! -f "$dockerfile" ]]; then
        log_error "Dockerfile not found: $dockerfile"
        return 1
    fi
    
    docker build \
        -f "$dockerfile" \
        -t "${REGISTRY}/backend:${TAG}" \
        -t "${REGISTRY}/backend:${ENVIRONMENT}-${TAG}" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        backend/
    
    log_info "Backend image built successfully"
}

# Build frontend image
build_frontend() {
    log_info "Building frontend image for $ENVIRONMENT environment..."
    
    local dockerfile="frontend/Dockerfile"
    
    if [[ ! -f "$dockerfile" ]]; then
        log_error "Dockerfile not found: $dockerfile"
        return 1
    fi
    
    # Set build args based on environment
    local build_args=""
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        build_args="--build-arg NODE_ENV=production"
    else
        build_args="--build-arg NODE_ENV=development"
    fi
    
    docker build \
        -f "$dockerfile" \
        -t "${REGISTRY}/frontend:${TAG}" \
        -t "${REGISTRY}/frontend:${ENVIRONMENT}-${TAG}" \
        $build_args \
        frontend/
    
    log_info "Frontend image built successfully"
}

# Main build function
main() {
    log_info "Starting build process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Service: $SERVICE"
    log_info "Registry: $REGISTRY"
    log_info "Tag: $TAG"
    
    validate_environment
    check_docker
    
    case "$SERVICE" in
        "backend")
            build_backend
            ;;
        "frontend")
            build_frontend
            ;;
        "all")
            build_backend
            build_frontend
            ;;
        *)
            log_error "Invalid service: $SERVICE. Must be 'backend', 'frontend', or 'all'"
            exit 1
            ;;
    esac
    
    log_info "Build process completed successfully!"
    
    # Show built images
    log_info "Built images:"
    docker images | grep "$REGISTRY" | head -10
}

# Show usage
show_usage() {
    echo "Usage: $0 [environment] [service]"
    echo ""
    echo "Arguments:"
    echo "  environment  Target environment (dev|prod) [default: dev]"
    echo "  service      Service to build (backend|frontend|all) [default: all]"
    echo ""
    echo "Environment variables:"
    echo "  REGISTRY     Docker registry prefix [default: goaltrajectory]"
    echo "  TAG          Image tag [default: latest]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build all services for dev"
    echo "  $0 prod               # Build all services for prod"
    echo "  $0 dev backend        # Build only backend for dev"
    echo "  REGISTRY=myregistry TAG=v1.0.0 $0 prod"
}

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"