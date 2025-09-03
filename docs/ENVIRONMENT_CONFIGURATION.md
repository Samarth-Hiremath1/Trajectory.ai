# Environment Configuration Guide

This guide explains how to configure GoalTrajectory.AI for different environments using the provided configuration files.

## Overview

The application supports multiple environment configurations:
- **Development**: Local development with debugging and hot reload
- **Production**: Optimized for performance, security, and scalability

## Configuration Files Structure

```
├── .env.development                    # Root development config
├── .env.production                     # Root production config
├── backend/
│   ├── .env.development               # Backend development config
│   └── .env.production                # Backend production config
├── frontend/
│   ├── .env.development               # Frontend development config
│   └── .env.production                # Frontend production config
├── chromadb/
│   ├── .env.development               # ChromaDB development config
│   └── .env.production                # ChromaDB production config
└── k8s/base/
    ├── configmap-development.yaml     # Kubernetes development config
    ├── configmap-production.yaml      # Kubernetes production config
    ├── secrets-development.yaml       # Kubernetes development secrets
    └── secrets-production.yaml        # Kubernetes production secrets
```

## Development Environment Setup

### 1. Local Development (Docker Compose)

```bash
# Copy development environment files
cp .env.development .env
cp backend/.env.development backend/.env
cp frontend/.env.development frontend/.env.local
cp chromadb/.env.development chromadb/.env

# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 2. Kubernetes Development

```bash
# Create development namespace
kubectl create namespace goaltrajectory-dev

# Apply development configuration
kubectl apply -f k8s/base/configmap-development.yaml
kubectl apply -f k8s/base/secrets-development.yaml

# Deploy services
kubectl apply -f k8s/ -n goaltrajectory-dev
```

## Production Environment Setup

### 1. Docker Compose Production

```bash
# Copy and customize production environment files
cp .env.production .env
cp backend/.env.production backend/.env
cp frontend/.env.production frontend/.env.local
cp chromadb/.env.production chromadb/.env

# IMPORTANT: Edit the files and replace placeholder values
# with actual production credentials

# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Kubernetes Production

```bash
# Create production namespace
kubectl create namespace goaltrajectory-prod

# Customize and apply production configuration
# IMPORTANT: Edit configmap-production.yaml and secrets-production.yaml
# Replace placeholder values with actual production credentials

kubectl apply -f k8s/base/configmap-production.yaml
kubectl apply -f k8s/base/secrets-production.yaml

# Deploy services
kubectl apply -f k8s/ -n goaltrajectory-prod
```

## Configuration Categories

### Database Configuration

**Development:**
- Local PostgreSQL with simple credentials
- Connection pooling disabled for easier debugging
- Test database for automated testing

**Production:**
- Managed database service (recommended)
- Connection pooling enabled
- Backup and monitoring configured
- SSL/TLS encryption enabled

### Security Configuration

**Development:**
- Simple JWT secrets
- Rate limiting disabled
- CORS relaxed for local development
- Debug endpoints enabled

**Production:**
- Strong JWT secrets (minimum 32 characters)
- Rate limiting enabled
- Strict CORS policy
- Debug endpoints disabled
- Security headers enabled

### Performance Configuration

**Development:**
- Lower resource limits
- Hot reload enabled
- Source maps enabled
- Caching disabled

**Production:**
- Optimized resource allocation
- Multiple workers/replicas
- Caching enabled
- Compression enabled
- CDN integration

### Monitoring Configuration

**Development:**
- Detailed logging
- Profiling enabled
- Metrics collection optional
- Error reporting disabled

**Production:**
- Structured JSON logging
- Metrics collection enabled
- Error reporting to Sentry
- Performance monitoring
- Health checks configured

## Required Credentials

### Production Credentials Checklist

Before deploying to production, ensure you have:

- [ ] Production database credentials
- [ ] Production Supabase project credentials
- [ ] AI service API keys (HuggingFace, Gemini, OpenRouter)
- [ ] OAuth credentials (Google, etc.)
- [ ] JWT secret keys (minimum 32 characters)
- [ ] NextAuth secret (minimum 32 characters)
- [ ] Redis credentials (if using external Redis)
- [ ] Sentry DSN for error reporting
- [ ] AWS credentials for backups (optional)
- [ ] SSL/TLS certificates
- [ ] Domain names and DNS configuration

### Generating Secure Secrets

```bash
# Generate JWT secret (32+ characters)
openssl rand -hex 32

# Generate NextAuth secret
openssl rand -base64 32

# Generate bcrypt-compatible password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Environment Variables Reference

### Critical Variables

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `ENVIRONMENT` | development | production | Environment identifier |
| `DEBUG` | true | false | Enable debug mode |
| `LOG_LEVEL` | DEBUG | INFO | Logging verbosity |
| `DATABASE_URL` | Local DB | Production DB | Database connection string |
| `JWT_SECRET_KEY` | Simple | Strong (32+ chars) | JWT signing key |
| `RATE_LIMIT_ENABLED` | false | true | Enable rate limiting |

### Service-Specific Variables

**Backend:**
- `FASTAPI_ENV`: FastAPI environment mode
- `RELOAD`: Enable auto-reload (dev only)
- `MAX_WORKERS`: Number of worker processes

**Frontend:**
- `NODE_ENV`: Node.js environment
- `NEXT_PUBLIC_*`: Public environment variables
- `NEXTAUTH_*`: NextAuth configuration

**ChromaDB:**
- `CHROMA_LOG_LEVEL`: ChromaDB logging level
- `CHROMA_MAX_MEMORY`: Memory limit
- `CHROMA_ALLOW_RESET`: Allow database reset (dev only)

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```bash
   # Check if all required variables are set
   docker-compose config
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker-compose exec backend python -c "from services.database_service import DatabaseService; print('DB OK')"
   ```

3. **Kubernetes Secret Issues**
   ```bash
   # Verify secrets are properly encoded
   kubectl get secret app-secrets-production -o yaml
   echo "encoded_value" | base64 -d
   ```

### Environment Validation

Create a validation script to check environment configuration:

```bash
#!/bin/bash
# validate-env.sh

echo "Validating environment configuration..."

# Check required files exist
files=(".env" "backend/.env" "frontend/.env.local")
for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing: $file"
        exit 1
    fi
done

# Check critical variables
if [[ -z "$DATABASE_URL" ]]; then
    echo "❌ DATABASE_URL not set"
    exit 1
fi

echo "✅ Environment configuration valid"
```

## Security Best Practices

1. **Never commit production credentials to version control**
2. **Use strong, unique secrets for production**
3. **Regularly rotate API keys and secrets**
4. **Enable rate limiting in production**
5. **Use HTTPS/TLS for all production traffic**
6. **Implement proper CORS policies**
7. **Enable security headers**
8. **Monitor for security vulnerabilities**

## Performance Optimization

### Development
- Use minimal resource allocation
- Enable hot reload for faster development
- Disable caching for immediate feedback

### Production
- Optimize resource allocation based on load
- Enable caching at multiple levels
- Use CDN for static assets
- Implement connection pooling
- Configure horizontal pod autoscaling

## Monitoring and Observability

### Development
- Enable detailed logging
- Use development-friendly log formats
- Enable profiling tools

### Production
- Use structured JSON logging
- Implement centralized logging
- Enable metrics collection
- Set up alerting
- Configure health checks
- Implement distributed tracing