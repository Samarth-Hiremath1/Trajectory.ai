#!/bin/bash

# Deploy Ingress Controller and Configuration Script
# This script sets up NGINX Ingress Controller and applies ingress configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if helm is available (optional, for easier ingress controller installation)
HELM_AVAILABLE=false
if command -v helm &> /dev/null; then
    HELM_AVAILABLE=true
    print_status "Helm is available for ingress controller installation"
fi

# Function to install NGINX Ingress Controller using Helm
install_ingress_controller_helm() {
    print_status "Installing NGINX Ingress Controller using Helm..."
    
    # Add ingress-nginx repository
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    # Install ingress controller
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.replicaCount=2 \
        --set controller.nodeSelector."kubernetes\.io/os"=linux \
        --set defaultBackend.nodeSelector."kubernetes\.io/os"=linux \
        --set controller.admissionWebhooks.patch.nodeSelector."kubernetes\.io/os"=linux \
        --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz \
        --set controller.config.use-forwarded-headers="true" \
        --set controller.config.compute-full-forwarded-for="true" \
        --set controller.config.use-proxy-protocol="false"
    
    print_status "NGINX Ingress Controller installed successfully"
}

# Function to install NGINX Ingress Controller using kubectl
install_ingress_controller_kubectl() {
    print_status "Installing NGINX Ingress Controller using kubectl..."
    
    # Apply the ingress controller manifest
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
    
    print_status "NGINX Ingress Controller installed successfully"
}

# Function to install cert-manager
install_cert_manager() {
    print_status "Installing cert-manager..."
    
    if [ "$HELM_AVAILABLE" = true ]; then
        # Install using Helm
        helm repo add jetstack https://charts.jetstack.io
        helm repo update
        
        helm upgrade --install cert-manager jetstack/cert-manager \
            --namespace cert-manager \
            --create-namespace \
            --set installCRDs=true \
            --set nodeSelector."kubernetes\.io/os"=linux
    else
        # Install using kubectl
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
    fi
    
    print_status "cert-manager installed successfully"
}

# Function to create namespaces
create_namespaces() {
    print_status "Creating namespaces..."
    
    # Create production namespace
    kubectl create namespace goaltrajectory --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace goaltrajectory name=goaltrajectory --overwrite
    
    # Create development namespace
    kubectl create namespace goaltrajectory-dev --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace goaltrajectory-dev name=goaltrajectory-dev --overwrite
    
    print_status "Namespaces created successfully"
}

# Function to apply ingress configurations
apply_ingress_configs() {
    print_status "Applying ingress configurations..."
    
    # Wait for cert-manager to be ready
    print_status "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=300s
    kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=300s
    kubectl wait --for=condition=Available deployment/cert-manager-cainjector -n cert-manager --timeout=300s
    
    # Apply certificate issuers
    kubectl apply -f cert-issuer.yaml
    
    # Apply middleware configurations
    kubectl apply -f middleware.yaml
    
    # Apply network policies
    kubectl apply -f ingress-network-policy.yaml
    
    # Apply ingress resources
    kubectl apply -f ingress.yaml
    
    print_status "Ingress configurations applied successfully"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check ingress controller pods
    print_status "Checking NGINX Ingress Controller pods..."
    kubectl get pods -n ingress-nginx
    
    # Check cert-manager pods
    print_status "Checking cert-manager pods..."
    kubectl get pods -n cert-manager
    
    # Check ingress resources
    print_status "Checking ingress resources..."
    kubectl get ingress -n goaltrajectory
    kubectl get ingress -n goaltrajectory-dev
    
    # Check certificate issuers
    print_status "Checking certificate issuers..."
    kubectl get clusterissuer
    
    print_status "Installation verification completed"
}

# Main execution
main() {
    print_status "Starting ingress controller and configuration deployment..."
    
    # Check if ingress controller is already installed
    if kubectl get namespace ingress-nginx &> /dev/null; then
        print_warning "NGINX Ingress Controller namespace already exists. Skipping installation."
    else
        if [ "$HELM_AVAILABLE" = true ]; then
            install_ingress_controller_helm
        else
            install_ingress_controller_kubectl
        fi
    fi
    
    # Check if cert-manager is already installed
    if kubectl get namespace cert-manager &> /dev/null; then
        print_warning "cert-manager namespace already exists. Skipping installation."
    else
        install_cert_manager
    fi
    
    # Create application namespaces
    create_namespaces
    
    # Apply ingress configurations
    apply_ingress_configs
    
    # Verify installation
    verify_installation
    
    print_status "Ingress deployment completed successfully!"
    print_warning "Note: Update the email address in cert-issuer.yaml before production use"
    print_warning "Note: Update domain names in ingress.yaml to match your actual domains"
}

# Parse command line arguments
case "${1:-}" in
    --install-controller-only)
        if [ "$HELM_AVAILABLE" = true ]; then
            install_ingress_controller_helm
        else
            install_ingress_controller_kubectl
        fi
        ;;
    --install-cert-manager-only)
        install_cert_manager
        ;;
    --apply-configs-only)
        create_namespaces
        apply_ingress_configs
        ;;
    --verify-only)
        verify_installation
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --install-controller-only   Install only NGINX Ingress Controller"
        echo "  --install-cert-manager-only Install only cert-manager"
        echo "  --apply-configs-only        Apply only ingress configurations"
        echo "  --verify-only               Verify existing installation"
        echo "  --help                      Show this help message"
        echo ""
        echo "Run without arguments to perform full installation"
        ;;
    *)
        main
        ;;
esac