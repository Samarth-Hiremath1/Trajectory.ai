# GoalTrajectory.AI Backend Docker Setup

This directory contains Docker configurations for the GoalTrajectory.AI backend service with production-ready containerization.

## Docker Files

### Dockerfile
Multi-stage production Dockerfile with the following features:
- **Multi-stage build**: Separates build dependencies from runtime
- **Security**: Non-root user, minimal attack surface
- **Optimization**: Layer caching, minimal image size
- **Health checks**: Built-in health monitoring
- **Dependencies**: All required system packages (libmagic, etc.)

### Dockerfile.prod
Production-optimized version with:
- Production-only dependencies (requirements-prod.txt)
- Multiple workers for better performance
- Enhanced security configurations
- Optimized resource usage

### .dockerignore
Optimizes build context by excluding:
- Development files and directories
- Git history and documentation
- Test files and coverage reports
- Temporary and cache files

## Requirements Files

### requirements.txt
Full development and production dependencies

### requirements-prod.txt
Production-only dependencies with:
- No development/testing packages
- Optimized for container deployment
- Security-focused package selection

## Building Images

### Development Build
```bash
docker build -t goaltrajectory-backend:dev -f Dockerfile .
```

### Production Build
```bash
docker build -t goaltrajectory-backend:prod -f Dockerfile.prod .
```

## Running Containers

### Development Mode
```bash
docker run -d \
  --name goaltrajectory-backend \
  -p 8000:8000 \
  -e ENVIRONMENT=development \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  goaltrajectory-backend:dev
```

### Production Mode
```bash
docker run -d \
  --name goaltrajectory-backend \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  --restart unless-stopped \
  goaltrajectory-backend:prod
```

## Health Checks

The container includes multiple health check endpoints:

### Basic Health Check
```bash
curl http://localhost:8000/health
```
Returns comprehensive service status including database, cache, and ChromaDB connectivity.

### Kubernetes Readiness Probe
```bash
curl http://localhost:8000/health/ready
```
Checks if the application is ready to serve traffic.

### Kubernetes Liveness Probe
```bash
curl http://localhost:8000/health/live
```
Checks if the application is alive and responsive.

## Security Features

### Container Security
- **Non-root user**: Application runs as user `appuser` (UID 1001)
- **Minimal base image**: Python 3.11-slim for reduced attack surface
- **Read-only filesystem**: Where applicable
- **Security contexts**: Proper user and group configurations

### Image Security
- **Multi-stage builds**: Separate build and runtime environments
- **Minimal dependencies**: Production images exclude development tools
- **Layer optimization**: Efficient caching and minimal layers
- **Dependency pinning**: Specific versions to prevent supply chain attacks

## Environment Variables

### Required
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key

### Optional
- `ENVIRONMENT`: Set to 'production' for production mode
- `WORKERS`: Number of uvicorn workers (default: 1 for dev, 4 for prod)
- `LOG_LEVEL`: Logging level (default: info)

## Troubleshooting

### Common Issues

1. **Container fails to start with Supabase errors**
   - Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set
   - Check that the Supabase credentials are valid

2. **Health check failures**
   - Verify the container is fully started (may take 30+ seconds)
   - Check container logs: `docker logs <container_name>`

3. **Permission errors**
   - Ensure proper file permissions in mounted volumes
   - Check that the appuser has access to required directories

### Debugging Commands

```bash
# Check container status
docker ps

# View container logs
docker logs goaltrajectory-backend

# Execute shell in container
docker exec -it goaltrajectory-backend /bin/bash

# Check health status
docker inspect goaltrajectory-backend --format='{{.State.Health.Status}}'
```

## Performance Optimization

### Resource Limits
For production deployment, consider setting resource limits:

```bash
docker run -d \
  --name goaltrajectory-backend \
  --memory=1g \
  --cpus=1.0 \
  -p 8000:8000 \
  goaltrajectory-backend:prod
```

### Volume Mounts
For persistent data and logs:

```bash
docker run -d \
  --name goaltrajectory-backend \
  -p 8000:8000 \
  -v /host/logs:/app/logs \
  -v /host/uploads:/app/uploads \
  goaltrajectory-backend:prod
```

## Integration with Docker Compose

This Dockerfile is designed to work with the enhanced Docker Compose configurations in the project root. See the main docker-compose.yml files for complete stack deployment.