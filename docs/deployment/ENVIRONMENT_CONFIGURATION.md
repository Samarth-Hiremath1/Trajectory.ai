# Environment Configuration Guide

This guide details the configuration options and best practices for different deployment environments in GoalTrajectory.AI.

## Table of Contents

- [Overview](#overview)
- [Development Environment](#development-environment)
- [Staging Environment](#staging-environment)
- [Production Environment](#production-environment)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Security Configuration](#security-configuration)
- [Resource Configuration](#resource-configuration)

## Overview

GoalTrajectory.AI supports three main deployment environments, each with specific configurations optimized for their use case:

| Environment | Purpose | Characteristics |
|-------------|---------|-----------------|
| **Development** | Local development and testing | Hot reloading, debug logging, minimal resources |
| **Staging** | Pre-production testing | Production-like setup, test data, moderate resources |
| **Production** | Live application | Optimized performance, security hardened, full resources |

## Development Environment

### Purpose
- Local development and debugging
- Feature development and testing
- Integration testing with external services

### Configuration Characteristics

#### Docker Compose (`docker-compose.dev.yml`)
```yaml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./backend:/app
      - /app/venv
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
```

#### Kubernetes Configuration
```yaml
# k8s/base/configmap-dev.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: goaltrajectory-dev
data:
  ENVIRONMENT: "development"
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
  CHROMA_HOST: "chromadb-service"
  CHROMA_PORT: "8000"
  DATABASE_POOL_SIZE: "5"
  CACHE_TTL: "300"
```

#### Resource Limits
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Development Features
- **Hot Reloading**: Code changes reflected immediately
- **Debug Logging**: Verbose logging for troubleshooting
- **Development Tools**: Debuggers, profilers, test utilities
- **Relaxed Security**: Simplified authentication for testing
- **Local Storage**: File-based storage for rapid iteration

### Environment Variables

#### Backend (`.env.development`)
```bash
# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/goaltrajectory_dev
DATABASE_POOL_SIZE=5
DATABASE_POOL_TIMEOUT=30

# AI Service Configuration
GEMINI_API_KEY=your_dev_gemini_key
OPENROUTER_API_KEY=your_dev_openrouter_key
AI_MODEL_TEMPERATURE=0.7
AI_MAX_TOKENS=1000

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=dev_embeddings

# Storage Configuration
STORAGE_PROVIDER=local
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Security Configuration (Relaxed for development)
SECRET_KEY=dev_secret_key_not_for_production
JWT_EXPIRATION=86400  # 24 hours
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

#### Frontend (`.env.development`)
```bash
# Next.js Configuration
NODE_ENV=development
NEXT_PUBLIC_APP_ENV=development

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-dev-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_dev_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_dev_service_role_key

# Authentication Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev_nextauth_secret

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=false
NEXT_PUBLIC_DEBUG_MODE=true
```

## Staging Environment

### Purpose
- Pre-production testing
- User acceptance testing
- Performance testing
- Integration testing with production-like data

### Configuration Characteristics

#### Kubernetes Configuration
```yaml
# k8s/base/configmap-staging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: goaltrajectory-staging
data:
  ENVIRONMENT: "staging"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  CHROMA_HOST: "chromadb-service"
  CHROMA_PORT: "8000"
  DATABASE_POOL_SIZE: "10"
  CACHE_TTL: "600"
  RATE_LIMIT_REQUESTS: "1000"
  RATE_LIMIT_WINDOW: "3600"
```

#### Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Staging Features
- **Production-like Setup**: Similar to production configuration
- **Test Data**: Sanitized production data or realistic test data
- **Performance Monitoring**: Basic monitoring and alerting
- **SSL Certificates**: Valid SSL certificates for testing
- **Backup Systems**: Regular backups for data protection

### Environment Variables

#### Backend (`.env.staging`)
```bash
# Application Configuration
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/goaltrajectory_staging
DATABASE_POOL_SIZE=10
DATABASE_POOL_TIMEOUT=30
DATABASE_SSL_MODE=require

# AI Service Configuration
GEMINI_API_KEY=your_staging_gemini_key
OPENROUTER_API_KEY=your_staging_openrouter_key
AI_MODEL_TEMPERATURE=0.5
AI_MAX_TOKENS=2000

# ChromaDB Configuration
CHROMA_HOST=chromadb-service
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=staging_embeddings

# Storage Configuration
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://your-staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_staging_service_role_key
STORAGE_BUCKET=staging-resumes

# Cache Configuration
REDIS_URL=redis://redis-service:6379/0
CACHE_TTL=600

# Security Configuration
SECRET_KEY=staging_secret_key_change_in_production
JWT_EXPIRATION=3600  # 1 hour
CORS_ORIGINS=["https://staging.goaltrajectory.ai"]

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

#### Frontend (`.env.staging`)
```bash
# Next.js Configuration
NODE_ENV=production
NEXT_PUBLIC_APP_ENV=staging

# API Configuration
NEXT_PUBLIC_API_URL=https://api-staging.goaltrajectory.ai
NEXT_PUBLIC_WS_URL=wss://api-staging.goaltrajectory.ai

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-staging-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_staging_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_staging_service_role_key

# Authentication Configuration
NEXTAUTH_URL=https://staging.goaltrajectory.ai
NEXTAUTH_SECRET=staging_nextauth_secret

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=true
NEXT_PUBLIC_DEBUG_MODE=false

# Monitoring
NEXT_PUBLIC_SENTRY_DSN=https://your-staging-sentry-dsn
```

## Production Environment

### Purpose
- Live application serving real users
- Maximum performance and reliability
- Full security hardening
- Comprehensive monitoring and alerting

### Configuration Characteristics

#### Docker Compose (`docker-compose.prod.yml`)
```yaml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
      target: production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=WARNING
    restart: unless-stopped
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

#### Kubernetes Configuration
```yaml
# k8s/base/configmap-production.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: goaltrajectory-prod
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  CHROMA_HOST: "chromadb-service"
  CHROMA_PORT: "8000"
  DATABASE_POOL_SIZE: "20"
  CACHE_TTL: "3600"
  RATE_LIMIT_REQUESTS: "500"
  RATE_LIMIT_WINDOW: "3600"
```

#### Resource Limits
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Production Features
- **High Availability**: Multiple replicas and failover
- **Auto-scaling**: HPA based on CPU/memory usage
- **Security Hardening**: Full security policies and scanning
- **Monitoring**: Comprehensive metrics, logging, and alerting
- **Backup & Recovery**: Automated backups and disaster recovery
- **Performance Optimization**: Caching, CDN, database optimization

### Environment Variables

#### Backend (`.env.production`)
```bash
# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://prod_user:${DB_PASSWORD}@prod-db-cluster:5432/goaltrajectory_prod
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=/etc/ssl/certs/db-client.crt
DATABASE_SSL_KEY=/etc/ssl/private/db-client.key

# AI Service Configuration
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
AI_MODEL_TEMPERATURE=0.3
AI_MAX_TOKENS=4000
AI_RATE_LIMIT=100

# ChromaDB Configuration
CHROMA_HOST=chromadb-service
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=prod_embeddings
CHROMA_AUTH_TOKEN=${CHROMA_AUTH_TOKEN}

# Storage Configuration
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
STORAGE_BUCKET=prod-resumes
STORAGE_CDN_URL=https://cdn.goaltrajectory.ai

# Cache Configuration
REDIS_URL=redis://:${REDIS_PASSWORD}@redis-cluster:6379/0
CACHE_TTL=3600
CACHE_MAX_MEMORY=1gb

# Security Configuration
SECRET_KEY=${SECRET_KEY}
JWT_EXPIRATION=1800  # 30 minutes
JWT_REFRESH_EXPIRATION=604800  # 7 days
CORS_ORIGINS=["https://goaltrajectory.ai", "https://www.goaltrajectory.ai"]

# Rate Limiting
RATE_LIMIT_REQUESTS=500
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_BURST=50

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
PROMETHEUS_METRICS=true
HEALTH_CHECK_INTERVAL=30

# Performance
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65
```

#### Frontend (`.env.production`)
```bash
# Next.js Configuration
NODE_ENV=production
NEXT_PUBLIC_APP_ENV=production

# API Configuration
NEXT_PUBLIC_API_URL=https://api.goaltrajectory.ai
NEXT_PUBLIC_WS_URL=wss://api.goaltrajectory.ai
NEXT_PUBLIC_CDN_URL=https://cdn.goaltrajectory.ai

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-prod-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}

# Authentication Configuration
NEXTAUTH_URL=https://goaltrajectory.ai
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=true
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_MAINTENANCE_MODE=false

# Monitoring
NEXT_PUBLIC_SENTRY_DSN=${SENTRY_DSN}
NEXT_PUBLIC_GA_TRACKING_ID=${GA_TRACKING_ID}

# Performance
NEXT_PUBLIC_ENABLE_SW=true
NEXT_PUBLIC_CACHE_STRATEGY=stale-while-revalidate
```

## Configuration Files

### Directory Structure
```
├── backend/
│   ├── .env.development
│   ├── .env.staging
│   └── .env.production
├── frontend/
│   ├── .env.development
│   ├── .env.staging
│   └── .env.production
├── k8s/
│   └── base/
│       ├── configmap-dev.yaml
│       ├── configmap-staging.yaml
│       ├── configmap-production.yaml
│       ├── secrets-dev.yaml
│       ├── secrets-staging.yaml
│       └── secrets-production.yaml
├── docker-compose.yml
├── docker-compose.dev.yml
└── docker-compose.prod.yml
```

### Configuration Precedence

1. **Environment Variables**: Highest priority
2. **Kubernetes ConfigMaps/Secrets**: Medium priority
3. **Application Defaults**: Lowest priority

### Secret Management

#### Development
- Secrets in plain text files (not committed to git)
- Local environment variables
- Development-specific keys and tokens

#### Staging/Production
- Kubernetes Secrets (base64 encoded)
- External secret management (AWS Secrets Manager, HashiCorp Vault)
- Environment-specific encryption keys

## Environment Variables

### Required Variables

| Variable | Development | Staging | Production | Description |
|----------|-------------|---------|------------|-------------|
| `ENVIRONMENT` | development | staging | production | Environment identifier |
| `DEBUG` | true | false | false | Enable debug mode |
| `LOG_LEVEL` | DEBUG | INFO | WARNING | Logging level |
| `DATABASE_URL` | ✓ | ✓ | ✓ | Database connection string |
| `SECRET_KEY` | ✓ | ✓ | ✓ | Application secret key |
| `GEMINI_API_KEY` | ✓ | ✓ | ✓ | Google Gemini API key |
| `SUPABASE_URL` | ✓ | ✓ | ✓ | Supabase project URL |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_POOL_SIZE` | 10 | Database connection pool size |
| `CACHE_TTL` | 3600 | Cache time-to-live in seconds |
| `RATE_LIMIT_REQUESTS` | 1000 | Rate limit requests per window |
| `AI_MODEL_TEMPERATURE` | 0.5 | AI model creativity setting |
| `WORKER_PROCESSES` | 1 | Number of worker processes |

## Security Configuration

### Development Security
- Relaxed CORS policies
- Simple authentication
- Plain text secrets (local only)
- Disabled security headers

### Staging Security
- Production-like CORS policies
- Full authentication flow
- Encrypted secrets
- Basic security headers

### Production Security
- Strict CORS policies
- Multi-factor authentication
- Hardware security modules
- Full security headers
- Regular security scanning

### Security Headers (Production)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
      add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

## Resource Configuration

### Development Resources
- **CPU**: 100m request, 500m limit
- **Memory**: 256Mi request, 512Mi limit
- **Storage**: 1Gi for development data
- **Replicas**: 1 (no redundancy needed)

### Staging Resources
- **CPU**: 250m request, 1000m limit
- **Memory**: 512Mi request, 1Gi limit
- **Storage**: 10Gi for test data
- **Replicas**: 2 (basic redundancy)

### Production Resources
- **CPU**: 500m request, 2000m limit
- **Memory**: 1Gi request, 2Gi limit
- **Storage**: 100Gi+ for production data
- **Replicas**: 3+ (high availability)

### Auto-scaling Configuration

#### Development
```yaml
# No HPA in development
```

#### Staging
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Production
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
```

## Best Practices

### Configuration Management
1. **Environment Parity**: Keep configurations as similar as possible
2. **Secret Rotation**: Regularly rotate secrets and API keys
3. **Version Control**: Track configuration changes
4. **Validation**: Validate configurations before deployment
5. **Documentation**: Document all configuration options

### Security Best Practices
1. **Principle of Least Privilege**: Grant minimal required permissions
2. **Secret Management**: Never commit secrets to version control
3. **Encryption**: Encrypt sensitive data at rest and in transit
4. **Regular Updates**: Keep dependencies and base images updated
5. **Security Scanning**: Regular vulnerability assessments

### Performance Best Practices
1. **Resource Monitoring**: Monitor resource usage and adjust limits
2. **Caching Strategy**: Implement appropriate caching at all levels
3. **Database Optimization**: Optimize queries and connection pooling
4. **CDN Usage**: Use CDN for static assets in production
5. **Load Testing**: Regular performance testing under load