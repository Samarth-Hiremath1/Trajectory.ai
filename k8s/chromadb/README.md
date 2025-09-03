# ChromaDB Kubernetes Deployment

This directory contains Kubernetes manifests for deploying ChromaDB as a persistent vector database service.

## Components

### Core Resources
- `deployment.yaml` - ChromaDB deployment with persistent storage
- `service.yaml` - Service for internal communication
- `pvc.yaml` - Persistent Volume Claim for data storage
- `configmap.yaml` - Configuration settings for ChromaDB

### Scaling and Performance
- `hpa.yaml` - Horizontal Pod Autoscaler for automatic scaling
- Resource limits and requests configured for optimal performance

### Security
- `network-policy.yaml` - Network isolation policies
- Non-root user configuration
- Security contexts and capabilities restrictions

### Monitoring
- `servicemonitor.yaml` - Prometheus monitoring integration
- Health check endpoints configured
- Metrics collection setup

## Deployment

### Prerequisites
- Kubernetes cluster with persistent volume support
- Namespace `goaltrajectory-ai` created
- StorageClass available (default: `standard`)

### Deploy ChromaDB
```bash
# Apply all manifests
kubectl apply -f k8s/chromadb/

# Or use kustomize
kubectl apply -k k8s/chromadb/
```

### Verify Deployment
```bash
# Check pod status
kubectl get pods -n goaltrajectory-ai -l app=chromadb

# Check service
kubectl get svc -n goaltrajectory-ai chromadb-service

# Check persistent volume
kubectl get pvc -n goaltrajectory-ai chromadb-pvc

# Check logs
kubectl logs -n goaltrajectory-ai -l app=chromadb
```

## Configuration

### Storage
- Default storage: 10Gi
- Access mode: ReadWriteOnce
- StorageClass: standard (configurable)

### Resources
- CPU: 250m request, 500m limit
- Memory: 512Mi request, 1Gi limit
- Adjustable based on workload requirements

### Scaling
- Min replicas: 1
- Max replicas: 3
- CPU threshold: 70%
- Memory threshold: 80%

## Networking

### Internal Access
- Service name: `chromadb-service`
- Port: 8000
- Protocol: HTTP

### Backend Integration
Update backend configuration to use:
```
CHROMA_HOST=chromadb-service.goaltrajectory-ai.svc.cluster.local
CHROMA_PORT=8000
```

## Monitoring

### Health Checks
- Liveness probe: `/api/v1/heartbeat`
- Readiness probe: `/api/v1/heartbeat`
- Probe intervals and timeouts configured

### Metrics
- Prometheus ServiceMonitor included
- Metrics endpoint: `/api/v1/heartbeat`
- Custom annotations for scraping

## Security

### Network Policies
- Ingress: Only from backend pods and monitoring
- Egress: DNS resolution and HTTPS updates
- Namespace isolation enforced

### Pod Security
- Non-root user (UID: 1000)
- Read-only root filesystem where possible
- Dropped capabilities for minimal attack surface

## Troubleshooting

### Common Issues
1. **Pod not starting**: Check PVC status and storage availability
2. **Connection refused**: Verify service and network policies
3. **Out of memory**: Adjust resource limits in deployment
4. **Storage full**: Increase PVC size or clean up data

### Debug Commands
```bash
# Describe pod for events
kubectl describe pod -n goaltrajectory-ai -l app=chromadb

# Check resource usage
kubectl top pod -n goaltrajectory-ai -l app=chromadb

# Port forward for local testing
kubectl port-forward -n goaltrajectory-ai svc/chromadb-service 8000:8000
```

## Customization

### Environment-Specific Changes
- Modify resource limits in `deployment.yaml`
- Update storage size in `pvc.yaml`
- Adjust scaling parameters in `hpa.yaml`
- Configure storage class for cloud providers

### Production Considerations
- Enable authentication in ConfigMap
- Set up backup strategies for persistent data
- Configure monitoring alerts
- Implement disaster recovery procedures