# Frontend Docker Setup

This directory contains the Docker configuration for the GoalTrajectory.AI frontend application built with Next.js.

## Features

- **Multi-stage build**: Optimized for production with separate build and runtime stages
- **Security**: Non-root user configuration and minimal attack surface
- **Health checks**: Built-in health monitoring for container orchestration
- **Optimization**: Static asset optimization and production build configuration
- **Alpine Linux**: Minimal base image for reduced size and security

## Building the Image

```bash
# Build the production image
docker build -t goaltrajectory-frontend .

# Build with custom tag
docker build -t goaltrajectory-frontend:v1.0.0 .
```

## Running the Container

```bash
# Run in production mode
docker run -d -p 3000:3000 --name frontend goaltrajectory-frontend

# Run with environment variables
docker run -d -p 3000:3000 \
  -e NEXT_PUBLIC_SUPABASE_URL=your_url \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key \
  --name frontend goaltrajectory-frontend

# Run with volume mount for development
docker run -d -p 3000:3000 \
  -v $(pwd):/app \
  --name frontend-dev goaltrajectory-frontend
```

## Health Check

The container includes a built-in health check that monitors:
- Application server status
- Memory usage
- Build integrity

Access the health endpoint directly:
```bash
curl http://localhost:3000/api/health
```

## Environment Variables

Required environment variables for production:
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key
- `NEXTAUTH_URL`: NextAuth callback URL
- `NEXTAUTH_SECRET`: NextAuth secret key

## Security Features

- Non-root user (`nextjs:nodejs`)
- Minimal Alpine Linux base image
- Production-only dependencies in runtime stage
- Read-only filesystem compatibility
- Security headers and optimizations

## Optimization Features

- Multi-stage build for minimal image size
- Layer caching optimization
- Static asset optimization
- Bundle splitting and tree shaking
- Compressed assets and caching headers

## Troubleshooting

### Container won't start
Check the logs:
```bash
docker logs frontend
```

### Health check failing
Test the health endpoint manually:
```bash
docker exec frontend node /app/health-check.js
```

### Build failures
Ensure all dependencies are properly installed:
```bash
npm ci
npm run build
```