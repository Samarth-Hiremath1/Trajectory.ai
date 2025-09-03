#!/bin/bash

# Deployment script for GoalTrajectory.AI Kubernetes deployment
# Usage: ./scripts/deploy.sh [environment] [action]
# Environment: dev, staging, prod (default: dev)
# Action: deploy, update, status, logs (default: deploy)

set -e

# Configuration
ENVIRONMENT=${1:-dev}
ACTION=${2:-deploy}
NAMESPACE="goaltrajectory-${ENVIRONMENT}"
KUBECTL_TIMEOUT=${KUBECTL_TIMEOUT:-300}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Validate environment
validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be 'dev', 'staging', or 'prod'"
        exit 1
    fi
}

# Check if kubectl is available and configured
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    
    log_info "Connected to cluster: $(kubectl config current-context)"
}

# Create namespace if it doesn't exist
create_namespace() {
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        log_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
        kubectl label namespace "$NAMESPACE" environment="$ENVIRONMENT"
    fi
}

# Apply configuration files
apply_configs() {
    log_info "Applying base configurations..."
    
    # Apply namespace first
    if [[ -f "k8s/base/namespace.yaml" ]]; then
        envsubst < k8s/base/namespace.yaml | kubectl apply -f -
    fi
    
    # Apply base configurations
    local config_files=(
        "k8s/base/configmap-${ENVIRONMENT}.yaml"
        "k8s/base/configmap.yaml"
        "k8s/base/secrets-${ENVIRONMENT}.yaml"
        "k8s/base/secrets.yaml"
        "k8s/base/network-policies.yaml"
        "k8s/base/security-config.yaml"
    )
    
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            log_info "Applying $config_file"
            envsubst < "$config_file" | kubectl apply -n "$NAMESPACE" -f -
        else
            log_warn "Configuration file not found: $config_file"
        fi
    done
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Deploy ChromaDB first (dependency)
    if [[ -d "k8s/chromadb" ]]; then
        log_info "Deploying ChromaDB..."
        for file in k8s/chromadb/*.yaml; do
            if [[ -f "$file" && ! "$file" =~ kustomization.yaml ]]; then
                log_debug "Applying $file"
                envsubst < "$file" | kubectl apply -n "$NAMESPACE" -f -
            fi
        done
    fi
    
    # Deploy backend
    if [[ -d "k8s/backend" ]]; then
        log_info "Deploying backend..."
        for file in k8s/backend/*.yaml; do
            if [[ -f "$file" ]]; then
                log_debug "Applying $file"
                envsubst < "$file" | kubectl apply -n "$NAMESPACE" -f -
            fi
        done
    fi
    
    # Deploy frontend
    if [[ -d "k8s/frontend" ]]; then
        log_info "Deploying frontend..."
        for file in k8s/frontend/*.yaml; do
            if [[ -f "$file" ]]; then
                log_debug "Applying $file"
                envsubst < "$file" | kubectl apply -n "$NAMESPACE" -f -
            fi
        done
    fi
    
    # Deploy ingress
    if [[ -d "k8s/ingress" ]]; then
        log_info "Deploying ingress..."
        for file in k8s/ingress/*.yaml; do
            if [[ -f "$file" && ! "$file" =~ deploy-ingress.sh ]]; then
                log_debug "Applying $file"
                envsubst < "$file" | kubectl apply -n "$NAMESPACE" -f -
            fi
        done
    fi
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."
    
    local deployments=(
        "chromadb"
        "backend"
        "frontend"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            log_info "Waiting for deployment: $deployment"
            kubectl wait --for=condition=available \
                --timeout="${KUBECTL_TIMEOUT}s" \
                deployment/"$deployment" \
                -n "$NAMESPACE"
        else
            log_warn "Deployment not found: $deployment"
        fi
    done
}

# Check deployment status
check_status() {
    log_info "Checking deployment status for environment: $ENVIRONMENT"
    
    echo ""
    log_info "Namespace status:"
    kubectl get namespace "$NAMESPACE" 2>/dev/null || log_warn "Namespace $NAMESPACE not found"
    
    echo ""
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE" 2>/dev/null || log_warn "No deployments found"
    
    echo ""
    log_info "Services:"
    kubectl get services -n "$NAMESPACE" 2>/dev/null || log_warn "No services found"
    
    echo ""
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" 2>/dev/null || log_warn "No pods found"
    
    echo ""
    log_info "Ingress:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || log_warn "No ingress found"
    
    echo ""
    log_info "ConfigMaps:"
    kubectl get configmaps -n "$NAMESPACE" 2>/dev/null || log_warn "No configmaps found"
    
    echo ""
    log_info "Secrets:"
    kubectl get secrets -n "$NAMESPACE" 2>/dev/null || log_warn "No secrets found"
}

# Show logs
show_logs() {
    local service=${3:-"all"}
    
    log_info "Showing logs for environment: $ENVIRONMENT, service: $service"
    
    if [[ "$service" == "all" ]]; then
        local services=("backend" "frontend" "chromadb")
        for svc in "${services[@]}"; do
            echo ""
            log_info "=== Logs for $svc ==="
            kubectl logs -n "$NAMESPACE" -l app="$svc" --tail=50 2>/dev/null || log_warn "No logs found for $svc"
        done
    else
        kubectl logs -n "$NAMESPACE" -l app="$service" --tail=100 -f 2>/dev/null || log_warn "No logs found for $service"
    fi
}

# Update deployment (rolling update)
update_deployment() {
    log_info "Updating deployment for environment: $ENVIRONMENT"
    
    # Restart deployments to pull latest images
    local deployments=(
        "backend"
        "frontend"
        "chromadb"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            log_info "Restarting deployment: $deployment"
            kubectl rollout restart deployment/"$deployment" -n "$NAMESPACE"
        fi
    done
    
    # Wait for rollout to complete
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            log_info "Waiting for rollout to complete: $deployment"
            kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${KUBECTL_TIMEOUT}s"
        fi
    done
}

# Main deployment function
deploy() {
    log_info "Starting deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    
    validate_environment
    check_kubectl
    create_namespace
    apply_configs
    deploy_services
    wait_for_deployments
    
    log_info "Deployment completed successfully!"
    echo ""
    check_status
}

# Show usage
show_usage() {
    echo "Usage: $0 [environment] [action] [service]"
    echo ""
    echo "Arguments:"
    echo "  environment  Target environment (dev|staging|prod) [default: dev]"
    echo "  action       Action to perform (deploy|update|status|logs) [default: deploy]"
    echo "  service      Service for logs action (backend|frontend|chromadb|all) [default: all]"
    echo ""
    echo "Environment variables:"
    echo "  KUBECTL_TIMEOUT  Timeout for kubectl operations in seconds [default: 300]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to dev environment"
    echo "  $0 prod deploy        # Deploy to prod environment"
    echo "  $0 dev status         # Check status of dev environment"
    echo "  $0 dev logs backend   # Show backend logs from dev environment"
    echo "  $0 staging update     # Update staging deployment"
}

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Set environment variables for envsubst
export ENVIRONMENT
export NAMESPACE

# Main execution
case "$ACTION" in
    "deploy")
        deploy
        ;;
    "update")
        validate_environment
        check_kubectl
        update_deployment
        ;;
    "status")
        validate_environment
        check_kubectl
        check_status
        ;;
    "logs")
        validate_environment
        check_kubectl
        show_logs "$@"
        ;;
    *)
        log_error "Invalid action: $ACTION. Must be 'deploy', 'update', 'status', or 'logs'"
        show_usage
        exit 1
        ;;
esac