# Troubleshooting Guide

This guide helps resolve common issues encountered during deployment and operation of GoalTrajectory.AI.

## Table of Contents

- [Docker Issues](#docker-issues)
- [Kubernetes Issues](#kubernetes-issues)
- [Application Issues](#application-issues)
- [Network Issues](#network-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)
- [Debugging Tools](#debugging-tools)

## Docker Issues

### Container Build Failures

#### Issue: Docker build fails with "no space left on device"
```bash
# Clean up Docker system
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

#### Issue: Build fails with dependency errors
```bash
# Clear build cache
docker builder prune

# Build with no cache
docker build --no-cache -f backend/Dockerfile backend/

# Check Dockerfile syntax
./scripts/validate.sh docker dev
```

#### Issue: Multi-stage build fails
```bash
# Build specific stage for debugging
docker build --target build-stage -f backend/Dockerfile backend/

# Check intermediate layers
docker build --progress=plain -f backend/Dockerfile backend/
```

### Container Runtime Issues

#### Issue: Container exits immediately
```bash
# Check container logs
docker logs <container-name>

# Run container interactively
docker run -it <image-name> /bin/bash

# Check container health
docker inspect <container-name> | grep -A 10 Health
```

#### Issue: Permission denied errors
```bash
# Check file permissions in container
docker exec <container-name> ls -la /app

# Verify non-root user configuration
docker exec <container-name> whoami

# Fix ownership issues
docker exec <container-name> chown -R appuser:appuser /app
```

#### Issue: Environment variables not loaded
```bash
# Check environment variables
docker exec <container-name> env

# Verify .env file location
docker exec <container-name> ls -la /.env*

# Test with explicit environment variables
docker run -e ENVIRONMENT=dev <image-name>
```

### Docker Compose Issues

#### Issue: Services can't communicate
```bash
# Check network configuration
docker network ls
docker network inspect <network-name>

# Test connectivity between services
docker exec <container1> ping <container2>

# Check service discovery
docker exec <container1> nslookup <service-name>
```

#### Issue: Port conflicts
```bash
# Check port usage
netstat -tulpn | grep <port>
lsof -i :<port>

# Use different ports in docker-compose.yml
ports:
  - "8001:8000"  # Map to different host port
```

#### Issue: Volume mount issues
```bash
# Check volume mounts
docker inspect <container-name> | grep -A 10 Mounts

# Verify host path exists and has correct permissions
ls -la /host/path
chmod 755 /host/path

# Use absolute paths in docker-compose.yml
volumes:
  - /absolute/path:/container/path
```

## Kubernetes Issues

### Pod Issues

#### Issue: Pods stuck in Pending state
```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check node resources
kubectl top nodes
kubectl describe nodes

# Check resource requests vs available
kubectl get pods -n <namespace> -o wide
```

**Common causes:**
- Insufficient cluster resources
- Node selector constraints
- Persistent volume issues
- Image pull failures

#### Issue: Pods in CrashLoopBackOff
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Check liveness/readiness probes
kubectl describe pod <pod-name> -n <namespace>

# Disable probes temporarily for debugging
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","livenessProbe":null,"readinessProbe":null}]}}}}'
```

#### Issue: Image pull failures
```bash
# Check image name and tag
kubectl describe pod <pod-name> -n <namespace>

# Verify image exists
docker pull <image-name>

# Check image pull secrets
kubectl get secrets -n <namespace>
kubectl describe secret <image-pull-secret> -n <namespace>

# Create image pull secret if needed
kubectl create secret docker-registry <secret-name> \
  --docker-server=<registry-url> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n <namespace>
```

### Service Issues

#### Issue: Service not accessible
```bash
# Check service configuration
kubectl get svc -n <namespace>
kubectl describe svc <service-name> -n <namespace>

# Check endpoints
kubectl get endpoints <service-name> -n <namespace>

# Test service connectivity
kubectl run test-pod --image=busybox -it --rm -- wget -qO- http://<service-name>:<port>
```

#### Issue: Load balancer not working
```bash
# Check ingress configuration
kubectl get ingress -n <namespace>
kubectl describe ingress <ingress-name> -n <namespace>

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx <ingress-controller-pod>

# Test ingress rules
curl -H "Host: <hostname>" http://<ingress-ip>/<path>
```

### Deployment Issues

#### Issue: Deployment rollout stuck
```bash
# Check rollout status
kubectl rollout status deployment/<deployment-name> -n <namespace>

# Check deployment events
kubectl describe deployment <deployment-name> -n <namespace>

# Force rollout restart
kubectl rollout restart deployment/<deployment-name> -n <namespace>

# Check replica sets
kubectl get rs -n <namespace>
```

#### Issue: ConfigMap/Secret changes not applied
```bash
# Restart deployment to pick up changes
kubectl rollout restart deployment/<deployment-name> -n <namespace>

# Check if ConfigMap/Secret is mounted correctly
kubectl exec <pod-name> -n <namespace> -- ls -la /path/to/config

# Verify ConfigMap/Secret content
kubectl get configmap <configmap-name> -n <namespace> -o yaml
kubectl get secret <secret-name> -n <namespace> -o yaml
```

### Resource Issues

#### Issue: Out of memory errors
```bash
# Check pod resource usage
kubectl top pods -n <namespace>

# Check resource limits
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 Limits

# Increase memory limits
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

#### Issue: CPU throttling
```bash
# Check CPU usage
kubectl top pods -n <namespace>

# Check CPU limits and requests
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 -B 10 cpu

# Adjust CPU limits
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"cpu":"1000m"},"requests":{"cpu":"500m"}}}]}}}}'
```

## Application Issues

### Backend Issues

#### Issue: FastAPI server not starting
```bash
# Check application logs
kubectl logs <backend-pod> -n <namespace>

# Check if port is available
kubectl exec <backend-pod> -n <namespace> -- netstat -tulpn | grep 8000

# Test application directly
kubectl exec <backend-pod> -n <namespace> -- curl http://localhost:8000/health

# Check environment variables
kubectl exec <backend-pod> -n <namespace> -- env | grep -E "(DATABASE|API_KEY)"
```

#### Issue: Database connection failures
```bash
# Test database connectivity
kubectl exec <backend-pod> -n <namespace> -- python -c "
import os
import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('Database connection successful')
"

# Check database service
kubectl get svc -n <namespace> | grep postgres
kubectl describe svc postgres -n <namespace>

# Verify database credentials
kubectl get secret <db-secret> -n <namespace> -o yaml | base64 -d
```

#### Issue: ChromaDB connection issues
```bash
# Check ChromaDB service
kubectl get pods -n <namespace> | grep chromadb
kubectl logs <chromadb-pod> -n <namespace>

# Test ChromaDB connectivity
kubectl exec <backend-pod> -n <namespace> -- curl http://chromadb:8000/api/v1/heartbeat

# Check ChromaDB data persistence
kubectl exec <chromadb-pod> -n <namespace> -- ls -la /chroma
```

### Frontend Issues

#### Issue: Next.js build failures
```bash
# Check build logs
kubectl logs <frontend-pod> -n <namespace>

# Check Node.js version
kubectl exec <frontend-pod> -n <namespace> -- node --version

# Test build locally
docker run -it <frontend-image> npm run build

# Check environment variables
kubectl exec <frontend-pod> -n <namespace> -- env | grep NEXT_PUBLIC
```

#### Issue: API connection failures
```bash
# Check API endpoint configuration
kubectl exec <frontend-pod> -n <namespace> -- env | grep API_URL

# Test API connectivity from frontend
kubectl exec <frontend-pod> -n <namespace> -- curl http://backend:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://<backend-url>/api/endpoint
```

## Network Issues

### DNS Resolution Issues

#### Issue: Service discovery not working
```bash
# Test DNS resolution
kubectl exec <pod-name> -n <namespace> -- nslookup <service-name>
kubectl exec <pod-name> -n <namespace> -- dig <service-name>.<namespace>.svc.cluster.local

# Check CoreDNS
kubectl get pods -n kube-system | grep coredns
kubectl logs -n kube-system <coredns-pod>

# Check DNS configuration
kubectl exec <pod-name> -n <namespace> -- cat /etc/resolv.conf
```

### Network Policy Issues

#### Issue: Network policies blocking traffic
```bash
# Check network policies
kubectl get networkpolicy -n <namespace>
kubectl describe networkpolicy <policy-name> -n <namespace>

# Test connectivity without network policies
kubectl delete networkpolicy --all -n <namespace>

# Debug network policy rules
kubectl exec <pod-name> -n <namespace> -- nc -zv <target-service> <port>
```

### Ingress Issues

#### Issue: Ingress not routing traffic correctly
```bash
# Check ingress configuration
kubectl get ingress -n <namespace> -o yaml

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Test ingress rules
curl -v -H "Host: <hostname>" http://<ingress-ip>/<path>

# Check SSL certificate issues
kubectl describe certificate <cert-name> -n <namespace>
```

## Performance Issues

### High Memory Usage

#### Issue: Memory leaks in application
```bash
# Monitor memory usage over time
kubectl top pods -n <namespace> --sort-by=memory

# Check for memory leaks in logs
kubectl logs <pod-name> -n <namespace> | grep -i "memory\|oom"

# Profile application memory usage
kubectl exec <pod-name> -n <namespace> -- python -m memory_profiler app.py
```

### High CPU Usage

#### Issue: CPU spikes
```bash
# Monitor CPU usage
kubectl top pods -n <namespace> --sort-by=cpu

# Check application performance
kubectl exec <pod-name> -n <namespace> -- top

# Profile CPU usage
kubectl exec <pod-name> -n <namespace> -- python -m cProfile -o profile.stats app.py
```

### Slow Response Times

#### Issue: API endpoints responding slowly
```bash
# Check application logs for slow queries
kubectl logs <backend-pod> -n <namespace> | grep -E "(slow|timeout|error)"

# Test endpoint response times
kubectl exec <pod-name> -n <namespace> -- curl -w "@curl-format.txt" -o /dev/null -s http://backend:8000/api/endpoint

# Check database performance
kubectl exec <postgres-pod> -n <namespace> -- psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

## Security Issues

### Certificate Issues

#### Issue: SSL certificate problems
```bash
# Check certificate status
kubectl get certificate -n <namespace>
kubectl describe certificate <cert-name> -n <namespace>

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Manually renew certificate
kubectl delete certificate <cert-name> -n <namespace>
```

### Authentication Issues

#### Issue: Authentication failures
```bash
# Check authentication service logs
kubectl logs <auth-pod> -n <namespace>

# Test authentication endpoints
curl -X POST http://<auth-service>/login -d '{"username":"test","password":"test"}'

# Check JWT token validation
kubectl exec <backend-pod> -n <namespace> -- python -c "
import jwt
token = '<jwt-token>'
decoded = jwt.decode(token, verify=False)
print(decoded)
"
```

## Debugging Tools

### Useful kubectl Commands

```bash
# Get all resources in namespace
kubectl get all -n <namespace>

# Describe resource with events
kubectl describe <resource-type> <resource-name> -n <namespace>

# Get resource YAML
kubectl get <resource-type> <resource-name> -n <namespace> -o yaml

# Edit resource live
kubectl edit <resource-type> <resource-name> -n <namespace>

# Port forward for debugging
kubectl port-forward <pod-name> <local-port>:<pod-port> -n <namespace>

# Execute commands in pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# Copy files to/from pod
kubectl cp <local-file> <namespace>/<pod-name>:<pod-file>
kubectl cp <namespace>/<pod-name>:<pod-file> <local-file>
```

### Debug Pod

Create a debug pod for network troubleshooting:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
  namespace: <namespace>
spec:
  containers:
  - name: debug
    image: nicolaka/netshoot
    command: ["/bin/bash"]
    args: ["-c", "while true; do ping localhost; sleep 60;done"]
```

```bash
kubectl apply -f debug-pod.yaml
kubectl exec -it debug-pod -n <namespace> -- /bin/bash
```

### Monitoring Commands

```bash
# Watch pod status
kubectl get pods -n <namespace> -w

# Monitor resource usage
watch kubectl top pods -n <namespace>

# Follow logs from multiple pods
kubectl logs -f -l app=<app-label> -n <namespace>

# Get events sorted by time
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Log Analysis

```bash
# Search for errors in logs
kubectl logs <pod-name> -n <namespace> | grep -i error

# Get logs from specific time range
kubectl logs <pod-name> -n <namespace> --since=1h

# Get logs from all containers in pod
kubectl logs <pod-name> -n <namespace> --all-containers=true

# Export logs to file
kubectl logs <pod-name> -n <namespace> > pod-logs.txt
```

## Getting Help

If you're still experiencing issues:

1. Check the [deployment guide](README.md) for configuration details
2. Review application logs for specific error messages
3. Validate your configuration with `./scripts/validate.sh`
4. Check Kubernetes cluster health and resources
5. Consult the official documentation for specific tools (Docker, Kubernetes, etc.)

For persistent issues, consider:
- Enabling debug logging in applications
- Using profiling tools to identify bottlenecks
- Consulting with your platform team or cloud provider
- Opening an issue in the project repository with detailed logs and configuration