#!/bin/bash

# Validation script for GoalTrajectory.AI configurations
# Usage: ./scripts/validate.sh [type] [environment]
# Type: docker, k8s, all (default: all)
# Environment: dev, staging, prod (default: dev)

set -e

# Configuration
TYPE=${1:-all}
ENVIRONMENT=${2:-dev}
NAMESPACE="goaltrajectory-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

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

log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

# Test result functions
pass_check() {
    ((TOTAL_CHECKS++))
    ((PASSED_CHECKS++))
    echo -e "${GREEN}  ✓ PASS${NC} $1"
}

fail_check() {
    ((TOTAL_CHECKS++))
    ((FAILED_CHECKS++))
    echo -e "${RED}  ✗ FAIL${NC} $1"
}

warn_check() {
    ((TOTAL_CHECKS++))
    echo -e "${YELLOW}  ! WARN${NC} $1"
}

# Validate Docker configurations
validate_docker() {
    log_info "Validating Docker configurations..."
    
    # Check if Docker is available
    log_check "Docker availability"
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            pass_check "Docker is running and accessible"
        else
            fail_check "Docker is installed but not running"
        fi
    else
        fail_check "Docker is not installed"
    fi
    
    # Check Dockerfiles
    log_check "Dockerfile validation"
    
    local dockerfiles=(
        "backend/Dockerfile"
        "backend/Dockerfile.prod"
        "frontend/Dockerfile"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            # Basic syntax check
            if docker build --dry-run -f "$dockerfile" . &> /dev/null; then
                pass_check "$dockerfile syntax is valid"
            else
                fail_check "$dockerfile has syntax errors"
            fi
        else
            fail_check "$dockerfile not found"
        fi
    done
    
    # Check Docker Compose files
    log_check "Docker Compose validation"
    
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.dev.yml"
        "docker-compose.prod.yml"
    )
    
    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]]; then
            if docker-compose -f "$compose_file" config &> /dev/null; then
                pass_check "$compose_file is valid"
            else
                fail_check "$compose_file has configuration errors"
            fi
        else
            fail_check "$compose_file not found"
        fi
    done
    
    # Check environment files
    log_check "Environment files validation"
    
    local env_files=(
        "backend/.env.${ENVIRONMENT}"
        "frontend/.env.${ENVIRONMENT}"
        ".env.${ENVIRONMENT}"
    )
    
    for env_file in "${env_files[@]}"; do
        if [[ -f "$env_file" ]]; then
            pass_check "$env_file exists"
            
            # Check for required variables (basic check)
            if grep -q "ENVIRONMENT=" "$env_file" 2>/dev/null; then
                pass_check "$env_file contains ENVIRONMENT variable"
            else
                warn_check "$env_file missing ENVIRONMENT variable"
            fi
        else
            warn_check "$env_file not found (may be optional)"
        fi
    done
}

# Validate Kubernetes configurations
validate_k8s() {
    log_info "Validating Kubernetes configurations..."
    
    # Check if kubectl is available
    log_check "kubectl availability"
    if command -v kubectl &> /dev/null; then
        pass_check "kubectl is installed"
        
        if kubectl cluster-info &> /dev/null; then
            pass_check "kubectl can connect to cluster"
            log_debug "Current context: $(kubectl config current-context)"
        else
            warn_check "kubectl cannot connect to cluster (may be expected for validation)"
        fi
    else
        fail_check "kubectl is not installed"
    fi
    
    # Validate Kubernetes manifests
    log_check "Kubernetes manifest validation"
    
    local k8s_dirs=(
        "k8s/base"
        "k8s/backend"
        "k8s/frontend"
        "k8s/chromadb"
        "k8s/ingress"
    )
    
    for k8s_dir in "${k8s_dirs[@]}"; do
        if [[ -d "$k8s_dir" ]]; then
            pass_check "$k8s_dir directory exists"
            
            # Validate YAML files in directory
            for yaml_file in "$k8s_dir"/*.yaml; do
                if [[ -f "$yaml_file" ]]; then
                    # Basic YAML syntax check
                    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" &> /dev/null; then
                        pass_check "$(basename "$yaml_file") has valid YAML syntax"
                    else
                        fail_check "$(basename "$yaml_file") has invalid YAML syntax"
                    fi
                    
                    # Kubernetes API validation (if kubectl is available and connected)
                    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
                        if kubectl apply --dry-run=client -f "$yaml_file" &> /dev/null; then
                            pass_check "$(basename "$yaml_file") passes Kubernetes API validation"
                        else
                            fail_check "$(basename "$yaml_file") fails Kubernetes API validation"
                        fi
                    fi
                fi
            done
        else
            fail_check "$k8s_dir directory not found"
        fi
    done
    
    # Check for required Kubernetes resources
    log_check "Required Kubernetes resources"
    
    local required_files=(
        "k8s/base/namespace.yaml"
        "k8s/base/configmap.yaml"
        "k8s/backend/deployment.yaml"
        "k8s/backend/service.yaml"
        "k8s/frontend/deployment.yaml"
        "k8s/frontend/service.yaml"
        "k8s/chromadb/deployment.yaml"
        "k8s/chromadb/service.yaml"
        "k8s/ingress/ingress.yaml"
    )
    
    for required_file in "${required_files[@]}"; do
        if [[ -f "$required_file" ]]; then
            pass_check "$(basename "$required_file") exists"
        else
            fail_check "$(basename "$required_file") is missing"
        fi
    done
    
    # Validate environment-specific configurations
    log_check "Environment-specific configurations"
    
    local env_configs=(
        "k8s/base/configmap-${ENVIRONMENT}.yaml"
        "k8s/base/secrets-${ENVIRONMENT}.yaml"
    )
    
    for env_config in "${env_configs[@]}"; do
        if [[ -f "$env_config" ]]; then
            pass_check "$(basename "$env_config") exists for $ENVIRONMENT"
        else
            warn_check "$(basename "$env_config") not found for $ENVIRONMENT (may use defaults)"
        fi
    done
}

# Validate security configurations
validate_security() {
    log_info "Validating security configurations..."
    
    # Check for security contexts in Kubernetes manifests
    log_check "Security contexts in Kubernetes manifests"
    
    local deployment_files=(
        "k8s/backend/deployment.yaml"
        "k8s/frontend/deployment.yaml"
        "k8s/chromadb/deployment.yaml"
    )
    
    for deployment_file in "${deployment_files[@]}"; do
        if [[ -f "$deployment_file" ]]; then
            if grep -q "securityContext" "$deployment_file"; then
                pass_check "$(basename "$deployment_file") has security context"
            else
                fail_check "$(basename "$deployment_file") missing security context"
            fi
            
            if grep -q "runAsNonRoot" "$deployment_file"; then
                pass_check "$(basename "$deployment_file") configured for non-root user"
            else
                fail_check "$(basename "$deployment_file") missing non-root configuration"
            fi
        fi
    done
    
    # Check for network policies
    log_check "Network security policies"
    
    if [[ -f "k8s/base/network-policies.yaml" ]]; then
        pass_check "Network policies file exists"
    else
        fail_check "Network policies file missing"
    fi
    
    # Check for secrets management
    log_check "Secrets management"
    
    local secret_files=(
        "k8s/base/secrets.yaml"
        "k8s/base/secrets-${ENVIRONMENT}.yaml"
    )
    
    for secret_file in "${secret_files[@]}"; do
        if [[ -f "$secret_file" ]]; then
            pass_check "$(basename "$secret_file") exists"
            
            # Check if secrets are base64 encoded (basic check)
            if grep -q "data:" "$secret_file"; then
                pass_check "$(basename "$secret_file") uses data section (likely base64 encoded)"
            else
                warn_check "$(basename "$secret_file") may not be properly encoded"
            fi
        fi
    done
}

# Validate resource configurations
validate_resources() {
    log_info "Validating resource configurations..."
    
    # Check for resource limits and requests
    log_check "Resource limits and requests"
    
    local deployment_files=(
        "k8s/backend/deployment.yaml"
        "k8s/frontend/deployment.yaml"
        "k8s/chromadb/deployment.yaml"
    )
    
    for deployment_file in "${deployment_files[@]}"; do
        if [[ -f "$deployment_file" ]]; then
            if grep -q "resources:" "$deployment_file"; then
                pass_check "$(basename "$deployment_file") has resource configuration"
                
                if grep -A 10 "resources:" "$deployment_file" | grep -q "limits:"; then
                    pass_check "$(basename "$deployment_file") has resource limits"
                else
                    warn_check "$(basename "$deployment_file") missing resource limits"
                fi
                
                if grep -A 10 "resources:" "$deployment_file" | grep -q "requests:"; then
                    pass_check "$(basename "$deployment_file") has resource requests"
                else
                    warn_check "$(basename "$deployment_file") missing resource requests"
                fi
            else
                fail_check "$(basename "$deployment_file") missing resource configuration"
            fi
        fi
    done
    
    # Check for HPA configurations
    log_check "Horizontal Pod Autoscaler configurations"
    
    local hpa_files=(
        "k8s/backend/hpa.yaml"
        "k8s/frontend/hpa.yaml"
        "k8s/chromadb/hpa.yaml"
    )
    
    for hpa_file in "${hpa_files[@]}"; do
        if [[ -f "$hpa_file" ]]; then
            pass_check "$(basename "$hpa_file") exists"
        else
            warn_check "$(basename "$hpa_file") not found (HPA may be optional)"
        fi
    done
}

# Show validation summary
show_summary() {
    echo ""
    log_info "=== Validation Summary ==="
    echo "Total checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo -e "${GREEN}✓ All critical validations passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some validations failed. Please review the issues above.${NC}"
        return 1
    fi
}

# Main validation function
main() {
    log_info "Starting validation process..."
    log_info "Type: $TYPE"
    log_info "Environment: $ENVIRONMENT"
    
    case "$TYPE" in
        "docker")
            validate_docker
            ;;
        "k8s")
            validate_k8s
            validate_security
            validate_resources
            ;;
        "all")
            validate_docker
            echo ""
            validate_k8s
            echo ""
            validate_security
            echo ""
            validate_resources
            ;;
        *)
            log_error "Invalid type: $TYPE. Must be 'docker', 'k8s', or 'all'"
            exit 1
            ;;
    esac
    
    show_summary
}

# Show usage
show_usage() {
    echo "Usage: $0 [type] [environment]"
    echo ""
    echo "Arguments:"
    echo "  type         Validation type (docker|k8s|all) [default: all]"
    echo "  environment  Target environment (dev|staging|prod) [default: dev]"
    echo ""
    echo "Examples:"
    echo "  $0                # Validate all configurations for dev environment"
    echo "  $0 docker         # Validate only Docker configurations"
    echo "  $0 k8s prod       # Validate Kubernetes configurations for prod"
    echo "  $0 all staging    # Validate all configurations for staging"
}

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main "$@"