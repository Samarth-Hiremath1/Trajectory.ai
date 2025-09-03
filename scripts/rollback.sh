#!/bin/bash

# Rollback script for GoalTrajectory.AI Kubernetes deployments
# Usage: ./scripts/rollback.sh [environment] [service] [revision]
# Environment: dev, staging, prod (default: dev)
# Service: backend, frontend, chromadb, all (default: all)
# Revision: specific revision number or 'previous' (default: previous)

set -e

# Configuration
ENVIRONMENT=${1:-dev}
SERVICE=${2:-all}
REVISION=${3:-previous}
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

# Check if namespace exists
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
}

# Show rollout history for a deployment
show_history() {
    local deployment=$1
    
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
        log_warn "Deployment $deployment not found in namespace $NAMESPACE"
        return 1
    fi
    
    log_info "Rollout history for $deployment:"
    kubectl rollout history deployment/"$deployment" -n "$NAMESPACE"
    return 0
}

# Rollback a specific deployment
rollback_deployment() {
    local deployment=$1
    local target_revision=$2
    
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
        log_warn "Deployment $deployment not found in namespace $NAMESPACE"
        return 1
    fi
    
    log_info "Rolling back deployment: $deployment"
    
    # Show current status
    log_debug "Current status of $deployment:"
    kubectl get deployment "$deployment" -n "$NAMESPACE"
    
    # Perform rollback
    if [[ "$target_revision" == "previous" ]]; then
        log_info "Rolling back $deployment to previous revision"
        kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE"
    else
        log_info "Rolling back $deployment to revision $target_revision"
        kubectl rollout undo deployment/"$deployment" --to-revision="$target_revision" -n "$NAMESPACE"
    fi
    
    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${KUBECTL_TIMEOUT}s"
    
    # Show new status
    log_info "Rollback completed for $deployment"
    kubectl get deployment "$deployment" -n "$NAMESPACE"
    
    return 0
}

# Verify rollback success
verify_rollback() {
    local deployment=$1
    
    log_info "Verifying rollback for $deployment..."
    
    # Check if pods are ready
    local ready_pods=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired_pods=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    if [[ "$ready_pods" == "$desired_pods" && "$ready_pods" -gt 0 ]]; then
        log_info "✓ $deployment rollback verified: $ready_pods/$desired_pods pods ready"
        return 0
    else
        log_error "✗ $deployment rollback verification failed: $ready_pods/$desired_pods pods ready"
        return 1
    fi
}

# Show current deployment status
show_status() {
    local deployment=$1
    
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
        log_warn "Deployment $deployment not found"
        return 1
    fi
    
    echo ""
    log_info "=== Status for $deployment ==="
    kubectl get deployment "$deployment" -n "$NAMESPACE"
    
    echo ""
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -l app="$deployment"
    
    echo ""
    log_info "Recent events:"
    kubectl get events -n "$NAMESPACE" --field-selector involvedObject.name="$deployment" --sort-by='.lastTimestamp' | tail -5
}

# Rollback all services
rollback_all() {
    local services=("chromadb" "backend" "frontend")
    local failed_services=()
    
    log_info "Rolling back all services to $REVISION revision"
    
    # Show history for all services first
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
            show_history "$service"
            echo ""
        fi
    done
    
    # Confirm rollback
    if [[ "$REVISION" != "previous" ]] || [[ "${FORCE_ROLLBACK:-}" != "true" ]]; then
        echo ""
        log_warn "This will rollback all services in $ENVIRONMENT environment"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi
    
    # Rollback services in reverse dependency order
    for service in "${services[@]}"; do
        if rollback_deployment "$service" "$REVISION"; then
            log_info "✓ Successfully rolled back $service"
        else
            log_error "✗ Failed to rollback $service"
            failed_services+=("$service")
        fi
        echo ""
    done
    
    # Verify all rollbacks
    log_info "Verifying rollbacks..."
    for service in "${services[@]}"; do
        if [[ ! " ${failed_services[@]} " =~ " ${service} " ]]; then
            verify_rollback "$service"
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_info "All services rolled back successfully!"
    else
        log_error "Some services failed to rollback: ${failed_services[*]}"
        exit 1
    fi
}

# Main rollback function
main() {
    log_info "Starting rollback process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Service: $SERVICE"
    log_info "Revision: $REVISION"
    log_info "Namespace: $NAMESPACE"
    
    validate_environment
    check_kubectl
    check_namespace
    
    case "$SERVICE" in
        "all")
            rollback_all
            ;;
        "backend"|"frontend"|"chromadb")
            # Show history first
            show_history "$SERVICE"
            echo ""
            
            # Confirm rollback for production
            if [[ "$ENVIRONMENT" == "prod" && "${FORCE_ROLLBACK:-}" != "true" ]]; then
                log_warn "This will rollback $SERVICE in PRODUCTION environment"
                read -p "Are you sure you want to continue? (y/N): " -n 1 -r
                echo ""
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Rollback cancelled"
                    exit 0
                fi
            fi
            
            if rollback_deployment "$SERVICE" "$REVISION"; then
                verify_rollback "$SERVICE"
                show_status "$SERVICE"
                log_info "Rollback completed successfully!"
            else
                log_error "Rollback failed!"
                exit 1
            fi
            ;;
        *)
            log_error "Invalid service: $SERVICE. Must be 'backend', 'frontend', 'chromadb', or 'all'"
            exit 1
            ;;
    esac
}

# Show usage
show_usage() {
    echo "Usage: $0 [environment] [service] [revision]"
    echo ""
    echo "Arguments:"
    echo "  environment  Target environment (dev|staging|prod) [default: dev]"
    echo "  service      Service to rollback (backend|frontend|chromadb|all) [default: all]"
    echo "  revision     Target revision ('previous' or specific number) [default: previous]"
    echo ""
    echo "Environment variables:"
    echo "  KUBECTL_TIMEOUT  Timeout for kubectl operations in seconds [default: 300]"
    echo "  FORCE_ROLLBACK   Skip confirmation prompts (true|false) [default: false]"
    echo ""
    echo "Examples:"
    echo "  $0                        # Rollback all services to previous revision in dev"
    echo "  $0 prod backend           # Rollback backend to previous revision in prod"
    echo "  $0 staging frontend 3     # Rollback frontend to revision 3 in staging"
    echo "  FORCE_ROLLBACK=true $0 dev all  # Force rollback without confirmation"
    echo ""
    echo "Special commands:"
    echo "  $0 [env] [service] history    # Show rollout history only"
    echo "  $0 [env] [service] status     # Show current status only"
}

# Handle special commands
if [[ "$3" == "history" ]]; then
    validate_environment
    check_kubectl
    check_namespace
    
    if [[ "$SERVICE" == "all" ]]; then
        for svc in "backend" "frontend" "chromadb"; do
            show_history "$svc"
            echo ""
        done
    else
        show_history "$SERVICE"
    fi
    exit 0
fi

if [[ "$3" == "status" ]]; then
    validate_environment
    check_kubectl
    check_namespace
    
    if [[ "$SERVICE" == "all" ]]; then
        for svc in "backend" "frontend" "chromadb"; do
            show_status "$svc"
        done
    else
        show_status "$SERVICE"
    fi
    exit 0
fi

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"