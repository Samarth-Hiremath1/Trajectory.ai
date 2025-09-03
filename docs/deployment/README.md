# Deployment Guide

This guide covers deploying GoalTrajectory.AI using Docker and Kubernetes across different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **kubectl**: Version 1.24 or later (for Kubernetes deployment)
- **Kubernetes Cluster**: Version 1.24 or later

### Installation

#### Docker & Docker Compose
```bash
# macOS (using Homebrew)
brew install docker docker-compose

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### kubectl
```bash
# macOS (using Homebrew)
brew install kubectl

# Ubuntu/Debian
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installation
kubectl version --client
```

## Environment Setup

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd goaltrajectory-ai
```

### 2. Configure Environment Variables

Create environment-specific configuration files:

```bash
# Development environment
cp backend/.env.development.example backend/.env.development
cp frontend/.env.development.example frontend/.env.development

# Production environment
cp backend/.env.production.example backend/.env.production
cp frontend/.env.production.example frontend/.env.production
```

Edit the files with your specific configuration values.

### 3. Validate Configuration

```bash
# Validate all configurations for development
./scripts/validate.sh all dev

# Validate production configurations
./scripts/validate.sh all prod
```

## Docker Deployment

### Development Environment

For local development with hot reloading:

```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Start specific services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend chromadb

# Run in background
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Services Available:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ChromaDB: http://localhost:8001

### Production Environment

For production-like local deployment:

```bash
# Build and start production containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build

# Scale services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --scale backend=3 --scale frontend=2
```

### Container Management

#### Building Images

```bash
# Build all services for development
./scripts/build.sh dev all

# Build specific service for production
./scripts/build.sh prod backend

# Build with custom registry and tag
REGISTRY=myregistry TAG=v1.0.0 ./scripts/build.sh prod all
```

#### Managing Services

```bash
# View running containers
docker compose ps

# View logs
docker compose logs -f backend

# Execute commands in containers
docker compose exec backend bash
docker compose exec frontend sh

# Stop services
docker compose down

# Remove volumes (careful - this deletes data!)
docker compose down -v
```

## Kubernetes Deployment

### 1. Cluster Setup

Ensure you have access to a Kubernetes cluster:

```bash
# Check cluster connection
kubectl cluster-info

# Create or switch to appropriate context
kubectl config use-context your-cluster-context
```

### 2. Deploy Application

#### Development Environment

```bash
# Deploy to development
./scripts/deploy.sh dev deploy

# Check deployment status
./scripts/deploy.sh dev status

# View logs
./scripts/deploy.sh dev logs all
```

#### Staging Environment

```bash
# Deploy to staging
./scripts/deploy.sh staging deploy

# Monitor deployment progress
kubectl get pods -n goaltrajectory-staging -w
```

#### Production Environment

```bash
# Deploy to production (requires confirmation)
./scripts/deploy.sh prod deploy

# Check all resources
kubectl get all -n goaltrajectory-prod
```

### 3. Service Access

#### Port Forwarding (Development)

```bash
# Forward frontend service
kubectl port-forward -n goaltrajectory-dev svc/frontend 3000:3000

# Forward backend service
kubectl port-forward -n goaltrajectory-dev svc/backend 8000:8000

# Forward ChromaDB service
kubectl port-forward -n goaltrajectory-dev svc/chromadb 8001:8000
```

#### Ingress (Production)

The application is accessible through the configured ingress:
- Production: https://goaltrajectory.ai
- Staging: https://staging.goaltrajectory.ai

### 4. Scaling

#### Manual Scaling

```bash
# Scale backend pods
kubectl scale deployment backend --replicas=5 -n goaltrajectory-prod

# Scale frontend pods
kubectl scale deployment frontend --replicas=3 -n goaltrajectory-prod
```

#### Horizontal Pod Autoscaler

HPA is configured automatically and will scale based on CPU/memory usage:

```bash
# Check HPA status
kubectl get hpa -n goaltrajectory-prod

# View HPA details
kubectl describe hpa backend-hpa -n goaltrajectory-prod
```

## Environment Configuration

### Development

**Characteristics:**
- Hot reloading enabled
- Debug logging
- Development databases
- Minimal resource limits
- Volume mounts for code

**Configuration Files:**
- `docker-compose.dev.yml`
- `k8s/base/configmap-dev.yaml`
- `backend/.env.development`
- `frontend/.env.development`

### Staging

**Characteristics:**
- Production-like configuration
- Staging databases
- Moderate resource limits
- SSL certificates
- Performance monitoring

**Configuration Files:**
- `k8s/base/configmap-staging.yaml`
- `k8s/base/secrets-staging.yaml`
- `backend/.env.staging`
- `frontend/.env.staging`

### Production

**Characteristics:**
- Optimized builds
- Production databases
- Full resource limits
- SSL/TLS termination
- Comprehensive monitoring
- Security policies

**Configuration Files:**
- `docker-compose.prod.yml`
- `k8s/base/configmap-production.yaml`
- `k8s/base/secrets-production.yaml`
- `backend/.env.production`
- `frontend/.env.production`

## Monitoring and Health Checks

### Health Endpoints

All services expose health check endpoints:

- **Backend**: `GET /health`
- **Frontend**: `GET /api/health`
- **ChromaDB**: `GET /api/v1/heartbeat`

### Kubernetes Health Checks

Services are configured with:
- **Readiness Probes**: Check if service is ready to receive traffic
- **Liveness Probes**: Check if service is running properly
- **Startup Probes**: Check if service has started successfully

### Monitoring Commands

```bash
# Check pod health
kubectl get pods -n goaltrajectory-prod

# View pod details
kubectl describe pod <pod-name> -n goaltrajectory-prod

# Check service endpoints
kubectl get endpoints -n goaltrajectory-prod

# View resource usage
kubectl top pods -n goaltrajectory-prod
kubectl top nodes
```

### Logs

```bash
# View application logs
./scripts/deploy.sh prod logs backend

# View specific pod logs
kubectl logs -f <pod-name> -n goaltrajectory-prod

# View logs from all pods of a deployment
kubectl logs -f deployment/backend -n goaltrajectory-prod

# View previous container logs (if pod restarted)
kubectl logs <pod-name> -n goaltrajectory-prod --previous
```

## Rollback Procedures

### Kubernetes Rollbacks

```bash
# View rollout history
./scripts/rollback.sh prod backend history

# Rollback to previous version
./scripts/rollback.sh prod backend previous

# Rollback to specific revision
./scripts/rollback.sh prod backend 3

# Rollback all services
./scripts/rollback.sh prod all previous
```

### Docker Rollbacks

```bash
# Stop current containers
docker compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and start
docker compose up --build
```

## Security Considerations

### Container Security

- All containers run as non-root users
- Minimal base images (Alpine/Distroless)
- Regular security scanning
- Read-only root filesystems where possible

### Kubernetes Security

- Network policies for service isolation
- Pod Security Standards enforcement
- RBAC for service accounts
- Secrets management with encryption at rest

### SSL/TLS

- Automatic certificate management with cert-manager
- TLS termination at ingress level
- Internal service communication over HTTPS

## Backup and Recovery

### Database Backups

```bash
# Backup PostgreSQL (if using local instance)
kubectl exec -n goaltrajectory-prod <postgres-pod> -- pg_dump -U postgres goaltrajectory > backup.sql

# Restore from backup
kubectl exec -i -n goaltrajectory-prod <postgres-pod> -- psql -U postgres goaltrajectory < backup.sql
```

### ChromaDB Backups

```bash
# Backup ChromaDB data
kubectl cp goaltrajectory-prod/<chromadb-pod>:/chroma/chroma ./chroma-backup

# Restore ChromaDB data
kubectl cp ./chroma-backup goaltrajectory-prod/<chromadb-pod>:/chroma/chroma
```

### Configuration Backups

```bash
# Export all Kubernetes resources
kubectl get all,configmaps,secrets,ingress -n goaltrajectory-prod -o yaml > k8s-backup.yaml

# Backup Docker volumes
docker run --rm -v goaltrajectory_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data
```

## Performance Optimization

### Resource Tuning

Monitor and adjust resource limits based on usage:

```bash
# Check resource usage
kubectl top pods -n goaltrajectory-prod

# Update resource limits
kubectl patch deployment backend -n goaltrajectory-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"1Gi","cpu":"500m"}}}]}}}}'
```

### Scaling Strategies

1. **Horizontal Scaling**: Add more pod replicas
2. **Vertical Scaling**: Increase pod resource limits
3. **Cluster Scaling**: Add more nodes to the cluster

### Caching

- Redis for session caching
- CDN for static assets
- Database query optimization

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).