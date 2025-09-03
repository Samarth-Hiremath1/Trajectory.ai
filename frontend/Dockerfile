# Frontend Dockerfile with Next.js optimization
# Multi-stage build for production-ready container

# Stage 1: Dependencies installation
FROM node:18-alpine AS deps
WORKDIR /app

# Install dependencies needed for node-gyp and native modules
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies with npm ci for faster, reliable, reproducible builds
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies needed for building
RUN apk add --no-cache libc6-compat

# Copy package files and install all dependencies (including devDependencies)
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Set build environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Stage 3: Production runtime
FROM node:18-alpine AS runner
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application from builder stage
COPY --from=builder /app/public ./public

# Set correct permissions for precompiled cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy standalone build output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Create health check endpoint
COPY --chown=nextjs:nodejs <<EOF /app/health-check.js
const http = require('http');

const options = {
  hostname: '0.0.0.0',
  port: 3000,
  path: '/api/health',
  method: 'GET',
  timeout: 5000
};

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    if (res.statusCode === 200) {
      console.log('Health check passed:', data);
      process.exit(0);
    } else {
      console.error('Health check failed with status:', res.statusCode);
      process.exit(1);
    }
  });
});

req.on('error', (err) => {
  console.error('Health check error:', err.message);
  process.exit(1);
});

req.on('timeout', () => {
  console.error('Health check timeout');
  req.destroy();
  process.exit(1);
});

req.setTimeout(5000);
req.end();
EOF

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set hostname to bind to all interfaces
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD node /app/health-check.js

# Start the application
CMD ["node", "server.js"]